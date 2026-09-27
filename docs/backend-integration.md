# Backend integration

The RAG module is in `src/v_me_50`. It exposes a FastAPI router and leaves the gateway authentication implementation to the backend team. No identity value supplied directly in a client header is trusted by this module.

## API contract

Mount `recommendation_router(engine, verified_user)` under a FastAPI app. The `verified_user` dependency must validate the gateway's authenticated principal and return a nonempty user ID; authentication is a prerequisite to this route. Do not mount the router with a dependency that merely reads an unverified request header.

```python
from fastapi import FastAPI, HTTPException
from v_me_50.api import recommendation_router
from v_me_50.factory import create_engine

app = FastAPI()

def verified_user():
    # The gateway/backend team replaces this with verification of the
    # gateway-issued identity or session. This placeholder must fail closed.
    raise HTTPException(status_code=503, detail="Gateway auth is not configured")

app.include_router(recommendation_router(create_engine(), verified_user))
```

`POST /v1/recommendations` accepts:

```json
{"query": "Like Interstellar, but more focused on family relationships"}
```

It returns `recommendations[]` with `movie_id`, `title`, `year`, `genres`, `explanation`, `evidence` (the source plot), and `source_url`, plus `reference_movie_id` when relevant. Ambiguous or unknown reference titles return HTTP 422. The response can be empty when no movie satisfies the hard constraints. Backend and gateway teams can add request IDs, rate limiting, and telemetry around this route without changing the RAG logic.

## Setup

Use Python 3.11 or newer and install the project with `pip install -e '.[data,test]'`. Set the variables shown in `.env.example` on the server; keep the LLM key server-side. The Supabase publishable key is used only for catalog reads. Select an LLM that supports LangChain structured output; `factory.create_engine()` currently uses `ChatOpenAI`, and the chosen model is supplied through `OPENAI_MODEL`.

The query encoder loads `BAAI/bge-m3` locally on first use. The 1024-dimensional vectors already in Supabase are derived from this model. Any replacement encoder requires reindexing the movie vectors. The FastAPI route is synchronous because local encoding and database calls are synchronous; the backend should configure worker capacity accordingly.

## Data boundary

The catalog table and search functions are read-only for `anon` and `authenticated`. The movie data is public source material; user history and private preferences must be stored separately with owner-specific access control if added later. The authentication gateway remains responsible for protected API access.

The catalog contains all 92,374 films from the pinned [dataset revision](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset/tree/3300dbea0b3c5891c48eb7c468116c1062ccb8a9). Vectors use pgvector `halfvec(1024)` to remain within the [Free Plan's 500 MB database limit](https://supabase.com/docs/guides/platform/database-size). The source CSV is over Supabase Free Storage's [50 MB per-file upload limit](https://supabase.com/docs/guides/storage/uploads/file-limits), so the full source files remain at Hugging Face and in the local download cache. The Supabase catalog contains complete cleaned plots, metadata, and vectors, and each row records the source revision. The [source dataset](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset) is licensed CC BY-NC 4.0 and requires attribution to the dataset and its underlying sources. Full-table exact vector search exceeded Supabase's statement timeout; this version uses a compact binary HNSW index to shortlist candidates and exact cosine distance to rerank them. Database use is about 447 MB including the index; two live RPC searches completed in 2–3 seconds each, but broader relevance and latency evaluation remains necessary.

The RAG core has passed local tests with fake model/repository adapters, and live Supabase title and vector searches have succeeded. Full LLM generation and the gateway authentication flow still require downstream credentials and integration.

# Backend integration

The RAG workflow is in `src/v_me_50/rag`, service adapters are in `adapters`, and HTTP integration is in `api`. See [module boundaries](module-boundaries.md). The source exposes a FastAPI application factory and a router factory; the gateway authentication implementation belongs to the backend/gateway team. No identity value supplied directly in a client header is trusted by this module.

## Team handoff points

| Component | Provided interface | Remaining integration |
| --- | --- | --- |
| Frontend | React client consumes `POST /v1/recommendations` with a raw `query`; typed JSON response | Configure the actual gateway API prefix, login URL, and optional session path; validate authenticated requests |
| Gateway | `verified_user` dependency passed to `recommendation_router(engine, verified_user)` | Verify the gateway-issued identity/session and return a nonempty trusted user ID |
| FastAPI backend | `create_app(verified_user=...)`, `create_engine()`, and the router factory; `engine.recommend(query)` for internal use | Supply verified authentication, configure model credentials and hosting, and deploy |

The structured intent is an internal RAG contract, not a second public frontend endpoint. It uses nested `soft_preferences.prefer` and `soft_preferences.avoid`, as shown in `examples/family-intent.json`. `retrieve_candidates(intent, embedder=..., repository=...)` runs the same retrieval stage without requiring an LLM and is available for inspection and integration tests. The auth dependency is an extension point; actual user login and gateway token verification are not implemented here.

## API contract

Use the application factory to mount the recommendation route and manage the shared engine. The `verified_user` dependency must validate the gateway's authenticated principal and return a nonempty user ID; authentication is a prerequisite to this route. Do not supply a dependency that merely reads an unverified request header.

```python
from fastapi import HTTPException
from v_me_50.app import create_app

def verified_user():
    # The gateway/backend team replaces this with verification of the
    # gateway-issued identity or session. This placeholder must fail closed.
    raise HTTPException(status_code=503, detail="Gateway auth is not configured")

app = create_app(verified_user=verified_user)
```

The existing `recommendation_router(engine, verified_user)` interface remains available for a backend that already owns its FastAPI application. `create_app()` initializes its own engine once, after the first authenticated request, and closes its clients on shutdown. If you supply a prebuilt engine with `create_app(engine=engine, ...)`, its creator owns cleanup.

For a local application exposing health and OpenAPI, run `uvicorn v_me_50.app:create_app --factory`. Its default auth dependency returns 503; replace it in the team's application to enable authenticated recommendations. `/health` reports process liveness, not model or authentication readiness.

`POST /v1/recommendations` accepts:

```json
{"query": "Like Interstellar, but more focused on family relationships"}
```

It returns `recommendations[]` with `movie_id`, `title`, `year`, `genres`, `explanation`, `evidence` (the source plot), `evidence_quote` (an excerpt verified to occur in that plot), and `source_url`, plus `reference_movie_id` when relevant. Results may be empty when no movie satisfies the hard constraints or no model selection passes evidence validation. Backend and gateway teams can add request IDs, rate limiting, and telemetry without changing the RAG logic.

| HTTP status | Meaning |
| --- | --- |
| 401 | No verified principal |
| 422 | Invalid request or unknown/ambiguous reference movie; ambiguity includes `detail.candidates` |
| 502 | Unusable structured output from the model |
| 503 | Authentication/configuration is missing, or the model/catalog is temporarily unavailable |

If a title is ambiguous, the frontend can ask the user to include its release year in the request. The internal intent schema now has `reference_year`, and reference resolution checks it against the returned title matches.

## Setup

Use Python 3.11 or newer and install the project with `pip install -e '.[server,data,test]'`. Export the variables shown in `.env.example` in the server environment; keep the LLM key server-side. The package does not automatically load a `.env` file. The Supabase publishable key is used only for catalog reads. Select a model supporting LangChain structured output; the model adapter uses `ChatOpenAI`, and the selected model is supplied through `OPENAI_MODEL`. `OPENAI_BASE_URL` optionally selects a compatible provider endpoint. Timeouts, retries, and candidate count are configurable in the template and validated by `settings.py`.

The query encoder loads `BAAI/bge-m3` locally on first use. The 1024-dimensional vectors already in Supabase are derived from this model. Any replacement encoder requires reindexing the movie vectors. The FastAPI route is synchronous because local encoding and database calls are synchronous; the backend should configure worker capacity accordingly.

## Data boundary

The catalog table and search functions are read-only for `anon` and `authenticated`. The movie data is public source material; user history and private preferences must be stored separately with owner-specific access control if added later. The authentication gateway remains responsible for protected API access.

The catalog contains all 92,374 films from the pinned [dataset revision](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset/tree/3300dbea0b3c5891c48eb7c468116c1062ccb8a9). Vectors use pgvector `halfvec(1024)` to remain within the [Free Plan's 500 MB database limit](https://supabase.com/docs/guides/platform/database-size). The source CSV is over Supabase Free Storage's [50 MB per-file upload limit](https://supabase.com/docs/guides/storage/uploads/file-limits), so the full source files remain at Hugging Face and in the local download cache. The Supabase catalog contains complete cleaned plots, metadata, and vectors, and each row records the source revision. The [source dataset](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset) is licensed CC BY-NC 4.0 and requires attribution to the dataset and its underlying sources. Full-table exact vector search exceeded Supabase's statement timeout; this version uses a compact binary HNSW index to shortlist candidates and exact cosine distance to rerank them. Database use is about 447 MB including the index; two live RPC searches completed in 2–3 seconds each, but broader relevance and latency evaluation remains necessary.

The RAG core has 31 passing offline tests, including an HTTP-to-pipeline test with a fake structured-output model and repository. Live Supabase title and vector searches have succeeded. Full LLM generation and the gateway authentication flow still require actual credentials and integration. Evidence validation checks that the quoted plot text exists; it does not automatically establish that every explanation claim follows from the quote.

For a real retrieval-only example and its limitations, see [the family-theme query check](retrieval-check.md). `sql/004_fetch_ranked_records.sql` keeps full plot retrieval after candidate ranking to reduce work during vector search.

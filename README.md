# V Me 50

An AI-powered movie matching and recommendation system for CSE 5914, using a Retrieval-Augmented Generation (RAG) pipeline.

## Team

- Zelin Li
- Zijun Lu
- Sihao Ren
- Zhuotong Meng

## Project overview

Traditional movie recommendation systems often rely on genres, ratings, or user history. Our project explores recommendations that understand specific natural-language preferences, such as:

> I want a movie similar to Interstellar but with less science fiction and more focus on family relationships.

Users will describe what they want to watch. The system will retrieve relevant movies using plots, genres, themes, actors, directors, and other available metadata, then use an LLM to generate ranked recommendations with explanations grounded in the retrieved evidence.

## Planned user experience

1. Enter a movie request in natural language.
2. Receive ranked movie recommendations.
3. Read an explanation of why each movie matches the request.
4. Inspect the movie information retrieved to support each recommendation.

## Proposed pipeline

```text
Offline: Dataset → Cleaning + aligned embeddings → Supabase halfvec catalog + binary HNSW index

Online:  User request → Structured intent → Reference movie lookup (if needed)
                     → Query embedding + filters → Indexed candidate retrieval
                     → Exact cosine reranking on candidate vectors
                     → Constraint checks + preference reranking
                     → Recommendations with supporting evidence
```

Recommendations should refer to retrieved movie records and avoid inventing plot details or metadata. When the dataset cannot support a requested constraint, the system should make that limitation clear.

## Technology choices

FastAPI is selected for the backend, LangChain for RAG orchestration, React and TypeScript for the frontend, and a gateway for user authentication.

| Component | Candidate / decision needed |
| --- | --- |
| Dataset | [Movie Plot Embeddings Dataset](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset), revision `3300dbea0b3c5891c48eb7c468116c1062ccb8a9` |
| Retrieval | Binary HNSW candidate search, exact cosine reranking, and metadata filters |
| Movie lookup | Supabase queries for reference titles and structured metadata |
| Dataset storage | Supabase Postgres for all 92,374 cleaned records and vectors; source files remain on Hugging Face |
| Vector search | Supabase pgvector `halfvec(1024)` with a compact binary HNSW index and BGE-M3 query embeddings |
| Language model | To be selected for query understanding and recommendation generation |
| Frontend | React + TypeScript + Vite, with recommendations and source-evidence display |
| Gateway | User authentication between the frontend and backend; implementation to be selected |
| Backend | Python with FastAPI for the recommendation API and RAG orchestration |
| RAG orchestration | LangChain within FastAPI for intent parsing, query embedding, filtered retrieval, reranking, and LLM calls |

## Development roadmap

- [x] Confirm the dataset revision, license, and key metadata fields.
- [x] Define a normalized movie record and import all 92,374 records with aligned vectors.
- [x] Implement pgvector retrieval and verify live title and vector searches.
- [x] Implement modular LangChain intent, reference-query, retrieval, and selection stages with evidence-quote checks.
- [x] Implement a runnable FastAPI application factory and recommendation API contract.
- [ ] Configure a real LLM and validate the complete recommendation pipeline.
- [x] Build the responsive web interface and configurable gateway API client.
- [ ] Implement gateway authentication and connect its login/session endpoints.
- [ ] Evaluate relevance, preference satisfaction, explanation faithfulness, and latency.
- [ ] Prepare a reproducible demonstration and final project report.

## Repository guide

- `src/v_me_50/rag/`: recommendation workflow and LangChain stages.
- `src/v_me_50/adapters/`: BGE-M3, Supabase, and model-provider implementations.
- `src/v_me_50/api/`: FastAPI routes, application lifecycle, and gateway integration.
- `scripts/`: offline import and retrieval inspection commands using source modules.
- `sql/`: catalog and retrieval migrations.
- `tests/`: source-module, adapter, and API tests.
- `frontend/`: React application with separate API, authentication, and recommendation modules.
- `docs/module-boundaries.md`: module responsibilities and dependencies.
- `docs/project-status.md`: implemented components and remaining team work.
- `docs/project-plan.md`: architecture, data plan, and milestones.
- `.env.example`: server-side configuration variable names.
- `.gitignore`: excludes secrets, local environments, generated data, and build artifacts.

## Current status

The modular LangChain core, FastAPI application factory, Supabase movie catalog, and React frontend are implemented. All 92,374 movies and aligned BGE-M3 vectors are in Supabase; source files remain on Hugging Face. The frontend supports natural-language search, ranked results, plot evidence, cancellation, errors, and title clarification. Its separate sample preview uses explicitly labelled manual explanations. Actual LLM generation, gateway authentication, deployment, and full integration remain pending. See [frontend setup](frontend/README.md), [backend integration](docs/backend-integration.md), and [project status](docs/project-status.md).

## Local setup

Use Python 3.11 or newer and a virtual environment:

```sh
pip install -e '.[server,data,test]'
pytest -q
uvicorn v_me_50.app:create_app --factory --host 127.0.0.1 --port 8000
```

The application exposes `/health`, `/docs`, and `/openapi.json`. The default recommendation route returns HTTP 503 until the gateway's verification dependency is supplied. Server environment variables are listed in `.env.example`; the actual LLM pipeline requires the selected model and credentials. See [backend integration](docs/backend-integration.md) for the application factory integration example.

Start the frontend in another terminal using Node.js 24 LTS:

```sh
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:5173`. The development proxy forwards `/api` to `http://127.0.0.1:8000`; configure the real gateway and optional login/session endpoints with `frontend/.env.example`. The sample preview is available without credentials.

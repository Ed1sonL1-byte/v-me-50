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
Offline: Dataset → Cleaning + aligned embeddings → Supabase pgvector catalog

Online:  User request → Structured intent → Reference movie lookup (if needed)
                     → Query embedding + filters → Vector retrieval
                     → Constraint checks + preference reranking
                     → Recommendations with supporting evidence
```

Recommendations should refer to retrieved movie records and avoid inventing plot details or metadata. When the dataset cannot support a requested constraint, the system should make that limitation clear.

## Technology choices

FastAPI is selected for the backend, LangChain for RAG orchestration, and a gateway for user authentication. Other components remain under consideration.

| Component | Candidate / decision needed |
| --- | --- |
| Dataset | [Movie Plot Embeddings Dataset](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset), revision `3300dbea0b3c5891c48eb7c468116c1062ccb8a9` |
| Retrieval | Semantic vector search with metadata filters and preference-based reranking |
| Movie lookup | Supabase queries for reference titles and structured metadata |
| Dataset storage | Supabase Postgres for the 5,000 cleaned records; full source files remain on Hugging Face |
| Vector search | Supabase pgvector, with BGE-M3 query embeddings |
| Language model | To be selected for query understanding and recommendation generation |
| Frontend | Web interface; framework to be selected |
| Gateway | User authentication between the frontend and backend; implementation to be selected |
| Backend | Python with FastAPI for the recommendation API and RAG orchestration |
| RAG orchestration | LangChain within FastAPI for intent parsing, query embedding, filtered retrieval, reranking, and LLM calls |

## Development roadmap

- [x] Confirm the dataset revision, license, and key metadata fields for the initial subset.
- [x] Define a normalized movie record and import 5,000 records with aligned vectors.
- [x] Implement pgvector retrieval and verify live title and vector searches.
- [ ] Add LLM query understanding and evidence-grounded explanations.
- [ ] Build the web interface and recommendation API.
- [ ] Evaluate relevance, preference satisfaction, explanation faithfulness, and latency.
- [ ] Prepare a reproducible demonstration and final project report.

## Repository guide

- `docs/project-plan.md`: architecture, data plan, and milestones.
- `.env.example`: server-side configuration variable names.
- `.gitignore`: excludes secrets, local environments, generated data, and build artifacts.

## Current status

The Python LangChain recommendation core, a FastAPI route factory, and a Supabase movie catalog are implemented. The project contains 5,000 cleaned movies with aligned BGE-M3 vectors in Supabase; the full source dataset remains on Hugging Face. The authentication gateway, frontend, and selected LLM credentials are pending integration. See [backend integration](docs/backend-integration.md) for the route and configuration contract.

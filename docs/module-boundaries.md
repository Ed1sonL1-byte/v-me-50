# Source modules and ownership

The online recommendation workflow is implemented in `src/v_me_50`. Scripts are command-line tools for offline data operations or inspection; the retrieval inspection script calls the same source module as the API.

```text
src/v_me_50/
├── rag/
│   ├── pipeline.py       # Compose the recommendation stages
│   ├── intent.py         # LLM request → validated Intent
│   ├── query.py          # Build a query from retrieved reference evidence
│   ├── retrieval.py      # Resolve titles; retrieve, deduplicate, recheck constraints
│   ├── selection.py      # LLM preference selection; validate IDs and evidence quotes
│   ├── prompts.py        # LangChain prompt definitions
│   └── structured.py     # Structured-output validation and model failure boundary
├── adapters/
│   ├── embeddings.py     # BGE-M3 QueryEmbedder implementation
│   ├── supabase.py       # Read-only MovieRepository implementation
│   └── llm.py            # OpenAI-compatible model connection and client lifetime
├── api/
│   ├── routes.py         # Request/response validation and HTTP error mapping
│   └── application.py    # Gateway dependency, lazy shared engine, health, shutdown
├── app.py                # ASGI application factory entry point
├── factory.py            # Wire settings, adapters, and the RAG pipeline
├── settings.py           # Validated environment settings; masked secrets
├── models.py             # Shared Pydantic contracts
├── ports.py              # Repository, encoder, structured-model, service protocols
├── errors.py             # Failures independent of HTTP
└── genres.py             # Shared genre canonicalization and search aliases
```

`engine.py`, `embedding.py`, and `supabase_repository.py` remain as import compatibility modules. They re-export the implementation above; they contain no duplicate workflow. `from v_me_50.api import recommendation_router` also remains supported.

## Boundaries

| Layer | Responsibility | Dependencies |
| --- | --- | --- |
| RAG | Interpret preferences, resolve reference movies, orchestrate retrieval, and validate selected recommendations | Shared contracts and ports; LangChain for model stages |
| Adapters | Encode text, call the movie catalog, and connect the selected LLM provider | External SDKs and shared contracts |
| API | Validate HTTP input, invoke the recommendation service, and translate failures | FastAPI, contracts, and the service protocol |
| Composition | Read server configuration, create adapters, and own their lifetime | Settings, adapters, and RAG |
| Scripts | Parse command-line options, run offline imports or source-module checks, and write inspection artifacts | Import tools or the source composition root |

RAG modules do not read environment variables or issue HTTP/SQL requests directly. API routes do not implement prompts or retrieval. Supabase and encoder implementations can be replaced by another implementation of the same ports. An injected gateway dependency verifies the principal before the recommendation service is called.

## Workflow and validation

The complete code path is `IntentParser → reference resolution → ReferenceQueryBuilder → MovieRetriever → RecommendationSelector`. For a request without a reference movie, query construction uses the parsed semantic query directly. For a reference title with a supplied year, resolution filters title matches by that year.

Retrieval checks year, runtime, and genre constraints again after the database response. Genre aliases such as `sci-fi`, `sci fi`, and `science fiction film` share a canonical meaning; the database adapter also expands aliases for SQL filtering. Unknown required metadata does not satisfy a hard constraint. The reference movie is excluded locally as well as in the database when requested.

The selector requests an exact plot quote for each choice. It rejects IDs outside the displayed candidate set, duplicate choices, and quotes that do not occur in the source plot after whitespace normalization. This checks citation existence, not whether every explanation claim logically follows from its quote. Actual preference satisfaction and explanation accuracy still require real LLM testing. Selection context is capped at 80,000 characters, with at most 5,000 plot characters per candidate; full retrieved plots remain available in returned evidence.

`create_engine()` produces an owned recommendation engine with `close()` for cleanup. `create_app()` creates one engine lazily after the first authenticated request, reuses it, and closes it on shutdown. A caller who injects an already constructed engine owns its cleanup. `/health` is a liveness endpoint; it does not imply that gateway authentication or an LLM provider is configured.

## Verified status

The source modules have 31 passing offline tests, including an HTTP-to-LangChain workflow using a fake model and repository. A real Uvicorn process served health and OpenAPI requests, while unconfigured gateway authentication blocked recommendation requests. The refactored retrieval module also returned the same 20 live Supabase candidates on three successive checks.

These checks do not substitute for a real LLM run. The deployed provider, credentials, gateway, and frontend are still pending. See [project status](project-status.md) for the remaining work.

# Project status and remaining work

The source implementation is organized by RAG, adapters, API, shared contracts, composition, and frontend features. The movie catalog, live retrieval, and React interface are available. The complete application has not yet been validated with a real LLM and authenticated gateway.

| Component | Current state | Remaining work |
| --- | --- | --- |
| Dataset | All 92,374 normalized movie records and aligned vectors imported into Supabase | Maintain provenance and handle future catalog changes through the documented import process |
| Retrieval | Real BGE-M3 encoding, title lookup, binary HNSW retrieval, and exact candidate reranking tested | Check relevance and latency over more requests and realistic concurrent use |
| LangChain stages | Intent parsing, reference-aware query construction, soft-preference selection, and exact evidence-quote validation implemented and tested offline | Supply an actual provider/model/key; run the full pipeline and inspect preference satisfaction and explanation claims |
| FastAPI | Application factory, recommendation route, typed responses, health, safe upstream errors, shared initialization, and shutdown implemented | Mount the verified gateway dependency and configure the server for the chosen hosting environment |
| Gateway/authentication | `verified_user` extension point and denied-by-default behavior provided | Implement login/session or token verification, reject invalid requests, and forward trusted identity to the backend |
| Frontend | React/TypeScript query input, loading/cancellation, errors/retry, ranked results, evidence dialog, empty results, title/year clarification, explicit sample preview, and configurable gateway login/session adapters implemented | Connect the real gateway and validate authenticated requests with real LLM results; gateway owns login and session creation |
| Deployment | Local server startup verified; environment configuration template provided | Choose hosting, configure secrets and gateway/backend routes, configure allowed frontend origins where needed, and deploy |
| End-to-end delivery | Offline pipeline/API tests, frontend contract tests/build, browser interaction checks, and real retrieval checks pass | Test the actual frontend → gateway → backend → LLM → Supabase path; prepare the demo and final report |

## Suggested team handoff

- **RAG owner:** Configure and validate the real LLM stages, review generated explanations against source evidence, and address remaining retrieval-quality issues.
- **Backend/gateway owner:** Implement verified authentication, wire it into the FastAPI application, configure the deployed services, and test upstream failure behavior.
- **Frontend owner:** Configure the gateway API prefix, login URL, and optional session path from [frontend setup](../frontend/README.md), then validate the real authenticated flow. The interface and HTTP client are implemented.
- **Team:** Run integrated requests covering the agreed user experience, inspect recommendation quality, and prepare a reproducible demonstration.

The local application can start without credentials to expose health and OpenAPI. Recommendation requests remain blocked until verified authentication is supplied; actual model calls also require configured LLM credentials. No mock LLM or unverified user-ID header is used as a default production fallback.

## Frontend checks

The frontend production build and 14 contract/interaction tests pass; all 31 existing backend tests also pass. Browser checks cover desktop and mobile layouts (1440, 390, and 320 pixels wide), explicit sample results, full plot evidence, Escape dismissal, and the actual default FastAPI 503 response through the development proxy. Mocked HTTP responses exercise ambiguous-title/year clarification and empty results. These checks validate the interface and contracts, not real authentication or LLM recommendations. Preview screenshots are local artifacts under ignored `output/playwright/`.

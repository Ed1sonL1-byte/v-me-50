# V Me 50 frontend

React, TypeScript, and Vite interface. It accepts natural-language requests, displays ranked recommendations and exact plot quotes, and opens complete source plots in an accessible dialog. It handles loading, cancellation, retry, empty results, authentication failures, and ambiguous reference titles.

## Run locally

Use Node.js 24 LTS:

```sh
cd frontend
npm ci
cp .env.example .env
npm run dev
```

Open `http://127.0.0.1:5173`. `npm run build` checks TypeScript and creates `dist/`. `npm test` checks API contracts and recommendation interactions. `npm run preview` serves the static build. The development proxy is not part of production builds or the preview server.

## Gateway integration

- `VITE_GATEWAY_BASE_URL` defaults to `/api`. Requests use `POST /api/v1/recommendations` with `{ "query": "..." }` and `credentials: 'include'` for gateway-managed cookies. The client does not send an unverified user-ID header, model key, Supabase key, or internal structured intent.
- `GATEWAY_PROXY_TARGET` configures only the development proxy; `/api` is removed when forwarding. The default local FastAPI target intentionally returns 503 until its gateway verification dependency is implemented.
- `VITE_GATEWAY_LOGIN_URL` points to the gateway's sign-in page. That page owns login, session creation, and the return redirect. With no configured page, the sign-in button explains that login is unavailable.
- `VITE_GATEWAY_SESSION_PATH` is optional and relative to the gateway base URL. Set it only after implementing a session endpoint. The proposed response is `{ "user": { "id": "...", "name": "..." } }`, or `{ "user": null }` / 401 for a signed-out user. No session request is made with a blank setting. This is a proposed gateway contract, not an endpoint implemented by the RAG backend.

Production must serve the built files and route `/api` through the real gateway. A same-origin gateway with an HttpOnly session cookie is the intended setup. A separate API origin requires explicit allowed origins and credentialed CORS at the gateway. Authentication and identity verification remain server responsibilities. All `VITE_*` values are public build-time configuration; secrets belong on the backend.

Ambiguous-title choices append a title and year to the original natural-language request and reuse the same endpoint. If the result exceeds 1,000 characters, the input remains editable for shortening. Choices without a known year ask for more detail. Requests time out after two minutes and can be cancelled; late responses cannot replace newer searches or the sample.

## Sample preview and attribution

“See a sample” explicitly enters preview mode, makes no recommendation API call, and never silently replaces a failed live request. The three movies are real records from the [September 27 retrieval inspection](../docs/retrieval-check.md). The order and explanations are manual; no real LLM generated this sample. Plots, years, IDs, genres, and source links are preserved. Card artwork is decorative typography, not movie posters. No unavailable ratings or streaming providers are invented.

Dataset: [Movie Plot Embeddings Dataset by NiklasAbraham](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset), revision `3300dbea0b3c5891c48eb7c468116c1062ccb8a9`. See [data import](../docs/data-import.md) for dataset and source licensing; each sample links its original source. This remains an academic, noncommercial demonstration.

## Module ownership

```text
src/
├── app/                          # Page composition
├── api/
│   ├── contracts.ts              # Runtime schemas and TypeScript contracts
│   └── gateway.ts                # Transport, cookies, timeouts, safe error messages
├── features/
│   ├── auth/AccountButton.tsx     # Gateway login redirect and optional session display
│   └── recommendations/
│       ├── useRecommendations.ts # Request lifecycle and stale-response protection
│       ├── QueryForm.tsx         # Input validation and example prompts
│       ├── Results.tsx           # Results, errors, loading, ambiguity, empty states
│       ├── RecommendationCard.tsx
│       ├── EvidenceDialog.tsx
│       └── sample.ts             # Explicit demonstration data
├── styles.css                    # Responsive layout and reduced-motion support
└── test/setup.ts                 # Test environment
```

The backend RAG modules own intent parsing, embeddings, retrieval, and selection. The frontend consumes the public HTTP contract and renders evidence. Real gateway login and real LLM recommendations still require integrated validation.

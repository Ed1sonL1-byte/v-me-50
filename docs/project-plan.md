# Project plan

## Objective

Build a web application that translates natural-language movie preferences into ranked recommendations supported by retrieved movie evidence.

## Initial scope

- Free-text requests, including comparisons to named movies and multiple preferences.
- Retrieval over movie plots and metadata available in the selected dataset.
- Ranked recommendations with movie identifiers, titles, match explanations, and supporting evidence.
- A web interface for entering requests and inspecting results.

User authentication is included in the initial scope. Long-term viewing history and streaming-service availability are outside the initial scope unless the team explicitly adds them.

## Planned application architecture

```mermaid
flowchart TB
    frontend["Frontend<br/>Login, preferences, recommendations"]
    gateway["Gateway<br/>User authentication"]
    subgraph backend["FastAPI Backend - Python"]
        api["Recommendation API"]
        chain["LangChain RAG Pipeline<br/>Understand query, retrieve, merge and rank"]
        api <-->|Request / recommendations with evidence| chain
    end
    frontend <-->|HTTPS request / response| gateway
    gateway <-->|Authenticated request / response| api
    chain <-->|Text / query vector| embedding["Embedding Model"]
    chain <-->|Semantic search / candidates| vector[("Vector Database")]
    chain <-->|Keyword search / candidates| elastic[("Elasticsearch")]
    chain <-->|Prompt and evidence / generated output| llm["LLM"]
    chain <-->|Movie IDs / canonical records| postgres[("Supabase Postgres<br/>Movie plots and metadata")]

    subgraph ingestion["Dataset Import and Indexing"]
        dataset["Hugging Face<br/>MoviePlotEmbeddingsDataset"]
        storage[("Supabase Storage<br/>Source dataset files")]
        clean["Validate and Normalize"]
        indexer["Build Search Indexes<br/>Shared movie IDs"]
        dataset -->|Import files| storage
        storage -->|Source records| clean
    end
    clean -->|Cleaned movie records| postgres
    postgres -->|Canonical records| indexer
    storage -->|Precomputed vectors or re-embed| indexer
    indexer -.->|Vectors and metadata| vector
    indexer -.->|Text and metadata| elastic

    classDef service fill:#eff6ff,stroke:#2563eb,color:#0f172a
    classDef data fill:#ecfdf5,stroke:#059669,color:#0f172a
    class frontend,gateway,api,chain,embedding,llm service
    class vector,elastic,postgres,storage data
```

- **Frontend:** Provides the login experience, accepts movie preferences, and displays recommendations with supporting evidence. API requests go through the gateway.
- **Gateway:** Sits between the frontend and backend, validates user credentials or sessions/tokens for protected requests, rejects unauthenticated requests, and forwards authenticated requests with trusted user identity to the backend. The authentication provider and gateway implementation will be selected during implementation.
- **Backend:** Uses Python and FastAPI to implement the movie recommendation API, coordinate retrieval and LLM generation, and return ranked movies with explanations and evidence. The backend accepts user identity only through a verified gateway connection, not from arbitrary client-supplied headers, and enforces any user-specific access rules.
- **LangChain:** Runs within the FastAPI backend to orchestrate query understanding, embedding and retrieval calls, prompt construction from retrieved movie records, and LLM recommendation generation. Explanations will retain references to supporting movie records.
- **Elasticsearch:** Provides keyword and text search over movie titles, plots, genres, cast, and directors. The planned hybrid retrieval flow combines Elasticsearch results with semantic matches from the vector database, deduplicates candidates by movie ID, and ranks the merged candidates before constructing the LLM prompt. Both indexes will use the same normalized movie IDs and source records; the fusion and ranking strategy will be chosen during implementation.
- **Supabase:** Hosts the movie dataset as the source of truth. We plan to retain downloaded dataset files in Supabase Storage and load cleaned movie records into Supabase Postgres. An indexing job derives the Elasticsearch and vector indexes from these records using shared movie IDs. FastAPI reads canonical movie details and evidence from Supabase when assembling recommendations. Supabase is selected for data storage; the gateway continues to own authentication enforcement.

Standalone Markdown diagram: [System architecture](../figures/system-architecture.md).

This architecture is planned; the gateway, authentication flow, and FastAPI application have not yet been implemented.

## Planned dataset

[Movie Plot Embeddings Dataset on Hugging Face](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset)

### Preprocessing plan — In Progress

1. Remove duplicate movie records and exclude entries missing a title or usable plot. Keep missing optional metadata as null rather than inventing values.
2. Clean plot text by removing formatting artifacts and normalizing whitespace. Standardize movie IDs, release dates, genres, cast, and director fields.
3. Create retrieval documents from the cleaned plots and metadata, preserving movie IDs and source links. Split long plots into chunks linked to their original movie.
4. Reuse existing embeddings only when they match the indexed text and movie IDs; generate new embeddings for modified text or new chunks using a consistent encoder.
5. Store source files in Supabase Storage and cleaned records in Supabase Postgres, then build Elasticsearch and vector indexes using shared movie IDs.

## Milestones and completion criteria

| Milestone | Completion criteria |
| --- | --- |
| Data selection | Record the exact dataset source, revision, license, schema, missing fields, and duplicate handling |
| Retrieval baseline | Reproducible ingestion and search return movie records for a fixed set of example queries |
| RAG recommendations | Generated recommendations reference retrieved records and expose supporting evidence |
| Authentication and API | Frontend requests pass through the authentication gateway to the FastAPI backend; protected requests require valid authentication |
| Web demonstration | A user can submit a request and inspect ranked results, loading states, and useful error messages |
| Evaluation | Report measured relevance, constraint satisfaction, faithfulness, and latency with the evaluation procedure |

## Data and configuration handling

Keep API keys in local environment variables or an ignored `.env` file. Commit only placeholder configuration. Keep downloaded datasets and generated indexes out of Git; document how to obtain and rebuild them after selecting the data source.

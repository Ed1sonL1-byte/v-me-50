# V Me 50 - System Architecture

Proposed architecture; not yet implemented. The gateway handles authentication, FastAPI hosts the LangChain RAG pipeline, and Supabase stores the dataset. LangChain parses user intent, resolves reference movies, embeds the semantic query, retrieves candidates with metadata filters, and reranks them using the original preferences. Query embedding is part of the backend retrieval flow. The first version uses vector retrieval without Elasticsearch.

```mermaid
flowchart TB
    frontend["Frontend<br/>Login, preferences, recommendations"]
    gateway["Gateway<br/>User authentication"]
    subgraph backend["FastAPI Backend - Python"]
        api["Recommendation API"]
        chain["LangChain RAG Pipeline<br/>Parse intent and resolve reference movies<br/>Query embedding, filtered retrieval and reranking"]
        api <-->|Request / recommendations with evidence| chain
    end
    frontend <-->|HTTPS request / response| gateway
    gateway <-->|Authenticated request / response| api
    chain <-->|Query vector and filters / candidates| vector[("Vector Database")]
    chain <-->|Prompt and evidence / generated output| llm["LLM"]
    chain <-->|Title lookup and movie IDs / canonical records| postgres[("Supabase Postgres<br/>Movie plots and metadata")]

    subgraph ingestion["Dataset Import and Indexing"]
        dataset["Hugging Face<br/>MoviePlotEmbeddingsDataset"]
        storage[("Supabase Storage<br/>Source dataset files")]
        clean["Validate and Normalize"]
        indexer["Build Vector Index<br/>Shared movie IDs"]
        dataset -->|Import files| storage
        storage -->|Source records| clean
    end
    clean -->|Cleaned movie records| postgres
    postgres -->|Canonical records| indexer
    storage -->|Precomputed vectors or re-embed| indexer
    indexer -.->|Vectors and metadata| vector

    classDef service fill:#eff6ff,stroke:#2563eb,color:#0f172a
    classDef data fill:#ecfdf5,stroke:#059669,color:#0f172a
    class frontend,gateway,api,chain,llm service
    class vector,postgres,storage data
```

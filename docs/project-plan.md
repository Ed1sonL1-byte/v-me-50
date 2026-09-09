# Project plan

## Objective

Build a web application that translates natural-language movie preferences into ranked recommendations supported by retrieved movie evidence.

## Initial scope

- Free-text requests, including comparisons to named movies and multiple preferences.
- Retrieval over movie plots and metadata available in the selected dataset.
- Ranked recommendations with movie identifiers, titles, match explanations, and supporting evidence.
- A web interface for entering requests and inspecting results.

User accounts, long-term viewing history, and streaming-service availability are outside the initial scope unless the team explicitly adds them.

## Planned dataset

We plan to use [Movie Plot Embeddings Dataset by NiklasAbraham on Hugging Face](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset) as the initial data source for our movie recommendation RAG pipeline.

According to the publisher's dataset card, it contains approximately 92,000 movies from 1930–2024, with plot text and metadata such as titles, genres, directors, actors, and ratings. It also provides precomputed 1024-dimensional BGE-M3 embeddings and movie identifiers for linking embeddings to metadata. These are publisher-reported details; actual row counts, field completeness, and embedding coverage still need to be verified after download.

### Initial implementation plan

1. Download the metadata CSV and inspect the schema, missing values, duplicates, and plot quality. Record the dataset revision and attribution requirements. The dataset card labels it CC BY-NC 4.0 and lists source-specific licensing requirements.
2. Start with 5,000–10,000 movies with usable plots and the metadata required for the initial demonstration, then expand after validating the pipeline.
3. Evaluate reusing the supplied dense embeddings, joining them to metadata by `movie_id` through the accompanying movie-ID array. Verify dimensions and alignment, and encode user queries using the same BGE-M3 configuration. If we choose another encoder, regenerate movie embeddings with that encoder.
4. Store vectors and movie metadata in the selected vector database, retrieve candidates from natural-language requests, and apply explicit metadata filters where supported.
5. Use an LLM to produce ranked recommendations grounded in retrieved records, showing plot evidence and available source links for each recommendation.

The Hugging Face viewer showed a schema mismatch during our initial review, so the planned ingestion path uses the underlying CSV and NumPy files rather than relying on the viewer's automatic schema. This is a proposed data plan; no dataset has been downloaded or validated yet.

## Milestones and completion criteria

| Milestone | Completion criteria |
| --- | --- |
| Data selection | Record the exact dataset source, revision, license, schema, missing fields, and duplicate handling |
| Retrieval baseline | Reproducible ingestion and search return movie records for a fixed set of example queries |
| RAG recommendations | Generated recommendations reference retrieved records and expose supporting evidence |
| Web demonstration | A user can submit a request and inspect ranked results, loading states, and useful error messages |
| Evaluation | Report measured relevance, constraint satisfaction, faithfulness, and latency with the evaluation procedure |

## Suggested evaluation

Prepare a fixed set of requests covering genres, themes, named-movie comparisons, positive and negative preferences, conflicting constraints, and requests with insufficient evidence. Reserve a subset for final evaluation rather than repeatedly tuning against it.

Compare a simple keyword or genre baseline against semantic retrieval and the complete RAG pipeline. Use a documented human-rating rubric for recommendation relevance and preference satisfaction. Check whether explanation claims are supported by retrieved fields, and measure end-to-end latency. Record dataset revisions, model settings, retrieval settings, and evaluation queries so results can be reproduced.

## Open decisions

- Validate the planned dataset's actual coverage, especially actor/director metadata, and pin a revision.
- Embedding model, vector database, and retrieval/ranking strategy.
- LLM provider, cost constraints, and configuration.
- Frontend and backend frameworks.
- Team responsibilities and course deadlines.

## Data and configuration handling

Keep API keys in local environment variables or an ignored `.env` file. Commit only placeholder configuration. Keep downloaded datasets and generated indexes out of Git; document how to obtain and rebuild them after selecting the data source.

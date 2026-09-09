# Project plan

## Objective

Build a web application that translates natural-language movie preferences into ranked recommendations supported by retrieved movie evidence.

## Initial scope

- Free-text requests, including comparisons to named movies and multiple preferences.
- Retrieval over movie plots and metadata available in the selected dataset.
- Ranked recommendations with movie identifiers, titles, match explanations, and supporting evidence.
- A web interface for entering requests and inspecting results.

User accounts, long-term viewing history, and streaming-service availability are outside the initial scope unless the team explicitly adds them.

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

- Exact dataset and whether actor/director metadata is sufficiently complete.
- Embedding model, vector database, and retrieval/ranking strategy.
- LLM provider, cost constraints, and configuration.
- Frontend and backend frameworks.
- Team responsibilities and course deadlines.

## Data and configuration handling

Keep API keys in local environment variables or an ignored `.env` file. Commit only placeholder configuration. Keep downloaded datasets and generated indexes out of Git; document how to obtain and rebuild them after selecting the data source.

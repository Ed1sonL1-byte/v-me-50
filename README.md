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
Movie dataset → Cleaning and normalization → Embeddings → Vector database
                                                               ↑
User request → Query understanding → Semantic retrieval ─────────┘
                                           ↓
                              Ranking and grounded generation
                                           ↓
                           Recommendations + supporting evidence
```

Recommendations should refer to retrieved movie records and avoid inventing plot details or metadata. When the dataset cannot support a requested constraint, the system should make that limitation clear.

## Technology candidates

These are options under consideration, not finalized dependencies.

| Component | Candidate / decision needed |
| --- | --- |
| Dataset | A Hugging Face movie dataset, such as the Movie Plot Embeddings Dataset; verify the exact dataset, license, fields, and coverage before use |
| Retrieval | Semantic search over movie plots and available metadata |
| Vector database | Qdrant, Pinecone, or pgvector |
| Language model | To be selected for query understanding and recommendation generation |
| Application | Web interface with a backend recommendation API; frameworks to be selected |

## Development roadmap

- [ ] Confirm the dataset, usage terms, and metadata coverage.
- [ ] Define a normalized movie record and build an ingestion pipeline.
- [ ] Implement a retrieval baseline and inspect results for representative requests.
- [ ] Add LLM query understanding and evidence-grounded explanations.
- [ ] Build the web interface and recommendation API.
- [ ] Evaluate relevance, preference satisfaction, explanation faithfulness, and latency.
- [ ] Prepare a reproducible demonstration and final project report.

## Repository guide

- `docs/project-plan.md`: proposed scope, milestones, and evaluation approach.
- `.env.example`: placeholder for future local configuration.
- `.gitignore`: excludes secrets, local environments, generated data, and build artifacts.

## Current status

Project initialization only. This repository does not yet contain a runnable application, downloaded dataset, configured model, or evaluation results. Setup instructions will be added with the first implementation.

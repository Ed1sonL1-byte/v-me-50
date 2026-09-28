# Family-theme retrieval check

On September 27, 2026, we tested the exact structured intent in [family-intent.json](../examples/family-intent.json) against the live Supabase catalog of 92,374 movies. The semantic query was:

> Family bonds, parent-child relationships, separation, sacrifice and reunion

The reference title was `Interstellar`, the positive preference was `family relationships`, and the soft avoidance was `heavy science-fiction elements`. There were no hard filters.

## What ran

This was a retrieval check, not a complete LLM recommendation run. We validated the intent, resolved `Interstellar` (2014) to `Q13417189`, encoded the supplied semantic query with normalized 1024-dimensional BGE-M3 embeddings, searched the binary HNSW index, reranked candidates using the original half-precision vectors, and returned 20 movies. The reference movie was excluded. The dataset revision was `3300dbea0b3c5891c48eb7c468116c1062ccb8a9`.

The initial request returned HTTP 500, and its server error code was not captured; a second request succeeded. We then changed the SQL function to fetch full plots and metadata after ranking. The ordered Top 20 stayed identical before and after that change. Three successive runs returned identical movie IDs and took 1.269, 0.263, and 0.253 seconds, including query encoding, title lookup, and retrieval. Loading the cached encoder took another 6.54 seconds once. These few runs do not establish general latency or reliability.

## Retrieved results

The assessments below are a manual reading of the retrieved dataset fields. They are not an LLM output or an independent verification of the actual films. Cosine similarity is a retrieval score, not a probability that a recommendation satisfies the request.

| Rank | Movie | Year | Similarity | Assessment from retrieved plot |
| --- | --- | --- | --- | --- |
| 1 | Vanvaas | 2024 | 0.6262 | Family bonds and sacrifice match, but the short synopsis provides few concrete events |
| 2 | Beautifully Broken | 2018 | 0.6160 | Three fathers protecting their families; forgiveness and reconciliation fit |
| 3 | Heaven Without People | 2017 | 0.6135 | Family reunion and conflict between generations fit; parent-child sacrifice is less explicit |
| 4 | A Question of Faith | 2017 | 0.5974 | Family tragedy fits partly; religious faith dominates the available synopsis |
| 5 | Naanu Nanna Kanasu | 2010 | 0.5911 | Strong parent-child match: a father's relationship with his daughter as she grows up |
| 6 | Papy | 2022 | 0.5898 | Strong father-child theme across four stories; separation/reunion is not explicit |
| 7 | The Puffy Chair | 2005 | 0.5845 | A journey to bring a father a birthday present; family theme is present but mixed with romance |
| 8 | O.Baby | 2023 | 0.5837 | Generational conflict fits partly; the synopsis centers on traditions and social ties |
| 9 | Neverending Past | 2018 | 0.5808 | Father-son relationships fit; the available synopsis is very brief |
| 10 | Mothers and Daughters | 2016 | 0.5786 | Strong match: motherhood and a woman reconsidering her estranged mother's relationship |
| 11 | Parallel Lives | 1994 | 0.5758 | Weak: reunion refers to college classmates, with no clear parent-child evidence |
| 12 | The Rigorous Fate | 1985 | 0.5725 | A child reunites with his grandfather and learns about his father; family discovery fits |
| 13 | Samsara Sangeetham | 1989 | 0.5673 | Strong separation/reunion match: parents split and a son searches for his mother |
| 14 | My Neighbors the Yamadas | 1999 | 0.5652 | Strong family-life and parent-child match; less focused on separation and sacrifice |
| 15 | 10 Things We Should Do Before We Break Up | 2020 | 0.5639 | Weak: the available plot mainly concerns a romantic couple |
| 16 | All Happy Families | 2023 | 0.5621 | Family reunion and tension fit; the source synopsis has limited detail |
| 17 | Distance | 2015 | 0.5610 | Partial: one story involves a young father, while others center on different relationships |
| 18 | Poppins | 2012 | 0.5576 | Weak for parent-child preferences: the stories center on husbands and wives |
| 19 | The Caranchos of Florida | 1938 | 0.5556 | Father-son conflict fits, though the conflict concerns a romantic relationship |
| 20 | Perhaps Love | 2021 | 0.5554 | Weak: the available synopsis emphasizes intertwined romantic relationships |

## Interpretation

The retrieval direction makes sense: many candidates have direct evidence of parent-child relationships, family separation, reconciliation, or reunion. A reasonable evidence-based shortlist for further selection would include `Naanu Nanna Kanasu`, `Mothers and Daughters`, `Samsara Sangeetham`, `Beautifully Broken`, and `The Rigorous Fate`. This is a manual shortlist, not a generated recommendation.

The vector ranking also includes semantic near misses. A college reunion and romantic relationship stories overlap with words in the query without meeting its main parent-child preference. Short, generic theme summaries can also rank above richer plots. Therefore, returning the five highest similarity scores directly would be insufficient.

No retrieved plot foregrounds heavy science fiction, but some genre fields are empty. The soft avoidance was preserved in the intent and would be passed to the LLM selector; it was not enforced or independently scored in this retrieval-only run. The absence of a genre value does not prove that a movie has no science-fiction elements.

This run validates the supplied family-theme query. The inspection path preserves that query and uses the reference for lookup and exclusion. The full recommendation pipeline now has a separate reference-aware query builder using retrieved plot evidence, but that LLM stage was not run in this inspection. Real LLM intent parsing, query construction, preference selection, explanation generation, and factual grounding still need end-to-end validation with a configured provider.

After splitting the source modules, the same inspection was rerun three times and returned the identical ordered Top 20 in 3.654, 0.365, and 0.208 seconds. Model initialization took 8.20 seconds. These remain retrieval-only measurements; the real provider's LLM stages are not included.

## Reproduce

Install the project and configure `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` locally as described in [backend integration](backend-integration.md), then run:

```sh
python scripts/inspect_retrieval.py --intent examples/family-intent.json --runs 3
```

The ignored `data/retrieval-inspection.json` contains full retrieved records and timings. Dataset source: [Movie Plot Embeddings Dataset](https://huggingface.co/datasets/NiklasAbraham/MoviePlotEmbeddingsDataset). Its attribution and licensing requirements are recorded in [data import](data-import.md).

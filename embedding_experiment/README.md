# Movie embedding comparison: BGE-M3 and Qwen

All experiment code, generated data, and downloaded Qwen files live in this folder.
The application, SQL, and original import script are not changed. We read the
original dataset under `../Data` and reuse the existing Python environment.

## Current decisions

- Reuse the dataset's BGE-M3 vectors for the fixed 100 movies.
- Skip BGE-M3 re-encoding/reproduction checks for now, by user choice.
- Generate Qwen movie vectors from the cleaned `plot` field.
- Use `Qwen/Qwen3-Embedding-0.6B` with 1024 output dimensions.
- Compare locally later; no application database is changed.

The exact historical BGE-M3 settings remain unverified. A final report must state
that limitation. Equal dimensions do not make different models' vectors compatible.

## Folder layout

```text
embedding_experiment/
    cleaning.py                # Local helpers matching the original import rules
    prepare_sample.py          # Fixed sample and existing BGE-M3 vectors
    download_qwen.py           # Download one pinned model snapshot
    qwen_encoder.py            # Load model, encode movies, encode queries
    generate_qwen.py           # Encode the fixed movie sample
    compare_query.py           # Shared year filtering and exact cosine retrieval
    queries/
        scifi_after_2000.json   # Fixed first query, min_year = 2001
    data/
        sample_100/
            sample_movies.json
            sample_movies.csv
            movie_ids.npy
            bge_m3_precomputed.npy
            manifest.json
            qwen/
                movie_embeddings.npy
                movie_ids.npy
                plot_token_lengths.npy
                manifest.json
    models/
        qwen_model.json
        huggingface/
```

The original sample was moved from `../Data/embedding_experiment/sample_100`
without re-sampling. Its manifest remains a record of its original preparation;
references there to shared import helpers describe that earlier preparation.
Those same rules now live here in `cleaning.py`. Generated data and model weights
are ignored by this folder's `.gitignore`.

## 1. Prepare a sample

Run from the repository root using the project's Python environment:

```powershell
.venv\Scripts\python.exe -m embedding_experiment.prepare_sample
```

The sample already exists. The script refuses to overwrite a nonempty output,
so there is no need to run it again. For a separate future sample:

```powershell
.venv\Scripts\python.exe -m embedding_experiment.prepare_sample --size 1000 --seed 42 --output embedding_experiment/data/sample_1000
```

Preparation checks ID uniqueness and vector shape, trims titles, collapses plot
whitespace, excludes unusable records, sorts by ID, and samples without replacement
with seed 42. Original plots are preserved. The local cleanup rules match the
original import script, but do not verify the factual accuracy of movie data.

JSON/CSV record i, movie ID i and BGE-M3 vector i refer to the same movie. CSV list
fields are JSON strings; `sample_movies.json` preserves native lists and nulls
and is the preferred input for the next steps.

Existing vectors were converted from float16 to float32 without re-encoding or
renormalizing. This does not recover lost precision. Normalize appropriately for
cosine similarity; these vectors are only approximately unit length.

## 2. Download Qwen

```powershell
.venv\Scripts\python.exe -m embedding_experiment.download_qwen
```

Model weights (approximately 1.2 GB) and tokenizer files are cached under
`embedding_experiment/models` on D:. `models/qwen_model.json` records the resolved
revision and download time. Later downloads reuse that revision.

## 3. Generate Qwen movie embeddings

```powershell
.venv\Scripts\python.exe -m embedding_experiment.generate_qwen
```

Generation loads the snapshot offline and encodes cleaned plots with no document
instruction. Defaults: CPU float32, 8 threads, batch size 2, max input length 8192,
1024 output dimensions, L2 normalization. Qwen supports longer inputs, but we
record the actual configured limit and observed truncation for this run.

The Qwen manifest records revision, sample hashes, dependency versions, input
settings, pooling, token lengths, truncation, load/encoding time and output hashes.
Final files are written after every movie is encoded and validated. Existing
Qwen output is not overwritten.

The environment needs numpy, pandas, huggingface-hub, torch, transformers >= 4.51.0
and sentence-transformers >= 2.7.0. This experiment does not modify application
dependency files.

## 4. Run the first query

```powershell
.venv\Scripts\python.exe -m embedding_experiment.compare_query
```

The fixed query in `queries/scifi_after_2000.json` asks for science-fiction
adventure/exploration movies released after 2000 (minimum year 2001). The script
filters metadata once, then searches the identical candidates using exact cosine
similarity for both models, returning at most 20 movies each. This initial
experiment supports only `min_year` and `max_year`; other filters raise an error.

The BGE-M3 encoder reads its existing D: cache without changing or downloading it.
Qwen uses the experiment's downloaded snapshot and the same revision used to
encode movies. Old BGE-M3 movie vectors are normalized for cosine search, without
overwriting their saved values.

Outputs go to `data/results/scifi_after_2000/`:

- `comparison.md`: side-by-side ranked movie titles and years.
- `comparison.json`: complete results including plots, scores, candidates,
  model revisions, data hashes and one-shot timings.
- `bge_m3_query.npy`, `qwen_query.npy`: each model's query vector.
- `blind_review.csv`: shuffled, deduplicated results without model names,
  original ranks or scores; blank columns for two independent reviewers.

Existing results are not overwritten. To test a different query, copy the JSON
to a new file and run `--query embedding_experiment/queries/your_query.json`.
To deliberately repeat a run, supply a new `--output` directory inside this
experiment. For an empty candidate set, the script stops before model loading.

## Evaluation

`qwen_encoder.encode_queries(model, queries)` adds this fixed query instruction:

```text
Instruct: Given a movie preference query, retrieve movie plots that match its themes.
Query: <semantic query>
```

Movie generation does not create query vectors; `compare_query.py` calls this
function for the fixed query. Human relevance judgments remain separate.

Freeze semantic query text and search the same candidate IDs for both models.
BGE-M3 query vectors search BGE-M3 movie vectors; Qwen query vectors search Qwen
movie vectors. Previous full-catalog Top 20 results cannot be compared with this
100-movie sample.

Grade pooled results with model identities and scores hidden, using written
criteria and independent human judgments. For the first query, require science
fiction AND adventure/exploration to be important to the plot; fantasy alone is
not sufficient. Label relevant, not relevant, or insufficient evidence, then
resolve disagreements before computing Precision@5. Unknown ratings are not
automatically positive. No automatic relevance scores have been produced.

This pilot sample does not guarantee relevant movies for every query. Top 20 is
a ranking, not a guarantee of 20 relevant movies. One first query after loading
is not a speed benchmark, and raw similarity values are not comparable quality
scores across models. Do not choose future evaluation queries only because one
model performed well on them; freeze a diverse query set for formal evaluation.

[Qwen model card and input instructions](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)

# Movie data import and provenance

The full import is complete: all 92,374 cleaned records and matching 1024-dimensional BGE-M3 vectors are in `public.movies` on Supabase project `cgnkdgkzmnsxojnxjbzj`. The pinned Hugging Face dataset revision is `3300dbea0b3c5891c48eb7c468116c1062ccb8a9`. The source has 92,374 unique movie IDs with nonempty titles and plots. The published vectors are `float16`, and the imported pgvector column stores them as `halfvec(1024)` to fit the Supabase Free Plan. We compared locally encoded plots for three titles with their published vectors and observed cosine similarity greater than 0.99999.

`scripts/prepare_movie_import.py` downloads the pinned CSV, ID array, and dense vector array, verifies their alignment, and prepares ignored JSON batches under `data/import_batches/`. Each row keeps its source ID and revision. The import uses entire movie plots. Changing to plot chunks requires new embeddings for each chunk.

The database schema is in `sql/001_movies.sql`; `sql/002_halfvec.sql` migrated the initial 5,000 float32 vectors to half precision. `sql/003_binary_index.sql` adds a binary HNSW index and changes the search function to rerank indexed candidates by cosine distance on the original vectors. `sql/004_fetch_ranked_records.sql` delays fetching full plots and metadata until after ranking. The catalog uses about 447 MB including its index, below the Free Plan's 500 MB limit. It enables RLS, grants read access to the public movie catalog, and defines read-only title and vector search functions. The route's gateway authentication is a separate backend responsibility.

## Reimport procedure

The temporary import permission has been revoked. Reimport requires a new temporary token and an operator who can apply schema changes to the Supabase project:

1. Set `SUPABASE_PUBLISHABLE_KEY` locally, then run `python scripts/create_import_auth.py`. The command prints only the token hash; it keeps the token in ignored `data/import_auth.json` with restricted local permissions.
2. Apply a temporary `INSERT` grant and RLS policy whose `WITH CHECK` compares the SHA-256 hash of the `x-import-token` HTTP request header with that printed hash. The policy must be limited to `anon` and `INSERT` on `public.movies`. Never put the raw token into SQL or Git.
3. Run `python scripts/prepare_movie_import.py --limit 0 --batch-size 20` and `python scripts/upload_movie_batches.py`. The uploader checkpoints completed batches in `data/import_checkpoint.json` and uses `resolution=ignore-duplicates` so retries do not create duplicate movie IDs. A new selection or dataset revision requires a reviewed update strategy, since existing IDs are intentionally not overwritten. Delete the old checkpoint only when starting a genuinely new import selection.
4. Immediately drop the temporary policy and `REVOKE INSERT ON public.movies FROM anon`. Verify that `has_table_privilege('anon','public.movies','INSERT')` is false and there are no `INSERT` policies on the table, then remove `data/import_auth.json`.

The temporary policy in step 2 uses the printed hash in place of `<TOKEN_SHA256>`:

```sql
grant insert (movie_id, title, release_year, plot, genres, actors,
              directors, runtime_minutes, source_url, dataset_revision, embedding)
on public.movies to anon;

create policy "Temporary token-gated movie import"
on public.movies for insert to anon
with check (
  encode(extensions.digest(
    coalesce(nullif(current_setting('request.headers', true), '')::jsonb
             ->> 'x-import-token', ''), 'sha256'), 'hex') = '<TOKEN_SHA256>'
);
```

Revocation in step 4 is:

```sql
drop policy if exists "Temporary token-gated movie import" on public.movies;
revoke insert on public.movies from anon;
```

The temporary import policy was used only to make client-side batch upload possible without placing a service-role key in the repository. The production state has public catalog reads and no anonymous catalog writes. Do not leave the temporary policy enabled after an interrupted import.

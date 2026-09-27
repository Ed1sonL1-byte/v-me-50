-- Compact binary HNSW index for the complete Free Plan catalog.
-- Exact distance is computed on the shortlisted original halfvec values.
create index if not exists movies_embedding_binary_hnsw_idx
on public.movies using hnsw
    ((extensions.binary_quantize(embedding)::bit(1024)) extensions.bit_hamming_ops)
with (m = 8, ef_construction = 64);

create or replace function public.match_movies(
    query_embedding extensions.vector(1024),
    match_count integer default 20,
    min_release_year integer default null,
    max_release_year integer default null,
    max_runtime integer default null,
    excluded_genres text[] default '{}',
    excluded_movie_id text default null
)
returns table (
    movie_id text, title text, year integer, plot text, genres text[],
    actors text[], directors text[], runtime_minutes integer,
    source_url text, similarity double precision
)
language sql stable security invoker
set search_path = ''
set hnsw.iterative_scan = 'relaxed_order'
as $$
    with candidates as materialized (
        select m.*
        from public.movies m
        where (min_release_year is null or m.release_year >= min_release_year)
          and (max_release_year is null or m.release_year <= max_release_year)
          and (max_runtime is null or m.runtime_minutes <= max_runtime)
          and (excluded_movie_id is null or m.movie_id <> excluded_movie_id)
          and not exists (
              select 1 from unnest(coalesce(excluded_genres, '{}')) excluded
              join unnest(m.genres) genre on position(lower(excluded) in lower(genre)) > 0
          )
        order by extensions.binary_quantize(m.embedding)::bit(1024)
                 operator(extensions.<~>)
                 extensions.binary_quantize(query_embedding::extensions.halfvec(1024))
        limit greatest(500, least(greatest(match_count, 1), 100) * 25)
    )
    select m.movie_id, m.title, m.release_year, m.plot, m.genres,
           m.actors, m.directors, m.runtime_minutes, m.source_url,
           1 - (m.embedding operator(extensions.<=>) query_embedding::extensions.halfvec(1024)) as similarity
    from candidates m
    order by m.embedding operator(extensions.<=>) query_embedding::extensions.halfvec(1024)
    limit least(greatest(match_count, 1), 100);
$$;

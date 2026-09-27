-- Public movie catalog only. User data belongs in separate, owner-restricted tables.
create extension if not exists vector with schema extensions;

create table if not exists public.movies (
    movie_id text primary key,
    title text not null,
    release_year integer,
    plot text not null,
    genres text[] not null default '{}',
    actors text[] not null default '{}',
    directors text[] not null default '{}',
    runtime_minutes integer,
    source_url text,
    dataset_revision text not null,
    embedding extensions.vector(1024) not null,
    check (length(title) > 0 and length(plot) > 0)
);

create index if not exists movies_title_lower_idx on public.movies (lower(title));
create index if not exists movies_year_idx on public.movies (release_year);

alter table public.movies enable row level security;
create policy "Anyone may read public movie catalog"
on public.movies for select to anon, authenticated using (true);
grant select on public.movies to anon, authenticated;

create or replace function public.find_movies_by_title(query_title text)
returns table (
    movie_id text, title text, year integer, plot text, genres text[],
    actors text[], directors text[], runtime_minutes integer,
    source_url text, similarity double precision
)
language sql stable security invoker set search_path = '' as $$
    select m.movie_id, m.title, m.release_year, m.plot, m.genres,
           m.actors, m.directors, m.runtime_minutes, m.source_url,
           null::double precision
    from public.movies m
    where lower(m.title) = lower(query_title)
    order by m.release_year nulls last
    limit 10;
$$;

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
language sql stable security invoker set search_path = '' as $$
    select m.movie_id, m.title, m.release_year, m.plot, m.genres,
           m.actors, m.directors, m.runtime_minutes, m.source_url,
           1 - (m.embedding operator(extensions.<=>) query_embedding) as similarity
    from public.movies m
    where (min_release_year is null or m.release_year >= min_release_year)
      and (max_release_year is null or m.release_year <= max_release_year)
      and (max_runtime is null or m.runtime_minutes <= max_runtime)
      and (excluded_movie_id is null or m.movie_id <> excluded_movie_id)
      and not exists (
          select 1 from unnest(coalesce(excluded_genres, '{}')) excluded
          join unnest(m.genres) genre on position(lower(excluded) in lower(genre)) > 0
      )
    order by m.embedding operator(extensions.<=>) query_embedding
    limit least(greatest(match_count, 1), 100);
$$;

revoke all on function public.find_movies_by_title(text) from public;
revoke all on function public.match_movies(extensions.vector, integer, integer, integer, integer, text[], text) from public;
grant execute on function public.find_movies_by_title(text) to anon, authenticated;
grant execute on function public.match_movies(extensions.vector, integer, integer, integer, integer, text[], text) to anon, authenticated;

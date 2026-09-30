-- Accelerate exact cast/crew array membership for named-person requests.
-- The single multicolumn GIN index supports either actor or director lookup.
create index if not exists movies_people_gin_idx
on public.movies using gin (actors, directors);

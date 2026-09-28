"""Genre normalization shared by the domain checks and database adapter."""

import re


def canonical_genre(value: str) -> str:
    value = " ".join(re.sub(r"[-_]", " ", value.casefold()).split())
    value = re.sub(r"\s+films?$", "", value)
    return {"sci fi": "science fiction", "scifi": "science fiction"}.get(value, value)


def database_genre_terms(genres: list[str]) -> list[str]:
    terms: list[str] = []
    for genre in genres:
        canonical = canonical_genre(genre)
        aliases = [canonical]
        if canonical == "science fiction":
            aliases += ["science-fiction", "sci-fi", "sci fi", "scifi"]
        terms.extend(term for term in aliases if term and term not in terms)
    return terms

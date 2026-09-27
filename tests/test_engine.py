from langchain_core.runnables import RunnableLambda
import pytest

from v_me_50.engine import AmbiguousReference, RecommendationEngine, passes_filters
from v_me_50.models import HardFilters, Intent, Movie, Selection


class FakeLLM:
    def __init__(self, intent: Intent, selection: Selection):
        self.intent = intent
        self.selection = selection

    def with_structured_output(self, schema):
        value = self.intent if schema is Intent else self.selection
        return RunnableLambda(lambda _prompt: value)


class FakeEmbedder:
    def __init__(self):
        self.last_query = None

    def embed_query(self, text):
        self.last_query = text
        return [0.0] * 1023 + [1.0]


class FakeRepository:
    def __init__(self, candidates, references=()):
        self.candidates = candidates
        self.references = references
        self.last_filters = None

    def find_by_title(self, title):
        return [movie for movie in self.references if movie.title.casefold() == title.casefold()]

    def search(self, embedding, filters, *, exclude_movie_id, limit):
        self.last_filters = filters
        return [m for m in self.candidates if m.movie_id != exclude_movie_id][:limit]


def movie(movie_id, title, genres=None, year=2010, runtime=100):
    return Movie(
        movie_id=movie_id,
        title=title,
        year=year,
        plot="A parent reconnects with a child after a long separation.",
        genres=genres or ["Drama"],
        runtime_minutes=runtime,
        source_url=f"https://www.wikidata.org/wiki/{movie_id}",
    )


def test_reference_excluded_hard_filters_rechecked_and_unlisted_selection_dropped():
    reference = movie("Q1", "Interstellar", ["Science fiction"])
    family = movie("Q2", "Family Journey")
    scifi = movie("Q3", "Space Family", ["Science fiction"])
    embedder = FakeEmbedder()
    repo = FakeRepository([reference, family, scifi, family], [reference])
    llm = FakeLLM(
        Intent(
            reference_title="Interstellar",
            semantic_query="Family bonds after separation",
            hard_filters=HardFilters(excluded_genres=["science fiction"]),
            prefer=["family relationships"],
            avoid=["space travel"],
        ),
        Selection(
            recommendations=[
                {"movie_id": "Q2", "explanation": "The plot centers on a parent and child."},
                {"movie_id": "Q3", "explanation": "Invalid hard-filter choice."},
                {"movie_id": "Q999", "explanation": "Not retrieved."},
            ]
        ),
    )
    result = RecommendationEngine(llm=llm, embedder=embedder, repository=repo).recommend(
        "Like Interstellar, but more family and no science fiction"
    )
    assert [r.movie_id for r in result.recommendations] == ["Q2"]
    assert result.recommendations[0].evidence == family.plot
    assert result.reference_movie_id == "Q1"
    assert embedder.last_query == "Family bonds after separation"
    assert repo.last_filters.excluded_genres == ["science fiction"]


def test_unknown_metadata_fails_hard_filter():
    assert not passes_filters(movie("Q4", "Unknown", runtime=None), HardFilters(max_runtime_minutes=120))


def test_ambiguous_reference_requires_clarification():
    refs = [movie("Q1", "Home", year=2010), movie("Q2", "Home", year=2020)]
    engine = RecommendationEngine(
        llm=FakeLLM(Intent(reference_title="Home", semantic_query="family"), Selection(recommendations=[])),
        embedder=FakeEmbedder(),
        repository=FakeRepository([], refs),
    )
    with pytest.raises(AmbiguousReference):
        engine.recommend("Something like Home")


def test_no_candidates_does_not_call_selection():
    engine = RecommendationEngine(
        llm=FakeLLM(Intent(semantic_query="family bonds"), Selection(recommendations=[])),
        embedder=FakeEmbedder(),
        repository=FakeRepository([]),
    )
    result = engine.recommend("A family movie")
    assert result.recommendations == []
    assert "No movies" in result.message

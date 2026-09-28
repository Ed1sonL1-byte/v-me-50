from langchain_core.runnables import RunnableLambda
import pytest

from v_me_50.engine import AmbiguousReference, RecommendationEngine, passes_filters, retrieve_candidates
from v_me_50.models import HardFilters, Intent, Movie, ReferenceQuery, Selection


class FakeLLM:
    def __init__(self, intent: Intent, selection: Selection, reference_query=None):
        self.intent = intent
        self.selection = selection
        self.reference_query = reference_query or ReferenceQuery(semantic_query=intent.semantic_query)
        self.calls = []

    def with_structured_output(self, schema):
        value = {Intent: self.intent, ReferenceQuery: self.reference_query, Selection: self.selection}[schema]
        def invoke(prompt):
            self.calls.append((schema, prompt.to_string()))
            return value
        return RunnableLambda(invoke)


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
        genres=["Drama"] if genres is None else genres,
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
            soft_preferences={"prefer": ["family relationships"], "avoid": ["space travel"]},
        ),
        Selection(
            recommendations=[
                {"movie_id": "Q2", "explanation": "The plot centers on a parent and child.",
                 "evidence_quote": "A parent reconnects with a child after a long separation."},
                {"movie_id": "Q3", "explanation": "Invalid hard-filter choice.", "evidence_quote": "A parent"},
                {"movie_id": "Q999", "explanation": "Not retrieved.", "evidence_quote": "A parent"},
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


def test_parsed_intent_retrieval_can_run_without_llm():
    reference = movie("Q1", "Interstellar")
    candidate = movie("Q2", "Family Journey")
    result = retrieve_candidates(
        Intent(
            reference_title="Interstellar", semantic_query="Family bonds and reunion",
            soft_preferences={"prefer": ["family"], "avoid": ["heavy sci-fi"]},
        ),
        embedder=FakeEmbedder(), repository=FakeRepository([reference, candidate], [reference]),
    )
    assert result.reference.movie_id == "Q1"
    assert [m.movie_id for m in result.candidates] == ["Q2"]


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
    llm = FakeLLM(Intent(semantic_query="family bonds"), Selection(recommendations=[]))
    engine = RecommendationEngine(
        llm=llm,
        embedder=FakeEmbedder(),
        repository=FakeRepository([]),
    )
    result = engine.recommend("A family movie")
    assert result.recommendations == []
    assert "No movies" in result.message
    assert [schema for schema, _ in llm.calls] == [Intent]


def test_reference_year_resolves_a_remake():
    refs = [movie("Q1", "Home", year=2010), movie("Q2", "Home", year=2020)]
    result = retrieve_candidates(
        Intent(reference_title="Home", reference_year=2020, semantic_query="family"),
        embedder=FakeEmbedder(), repository=FakeRepository([movie("Q3", "Family")], refs),
    )
    assert result.reference.movie_id == "Q2"


@pytest.mark.parametrize("genre", ["sci-fi", "Science Fiction Film", "sci fi", "Science-fiction"])
def test_genre_aliases_cannot_bypass_hard_exclusion(genre):
    assert not passes_filters(movie("Q4", "Space", [genre]), HardFilters(excluded_genres=["sci-fi"]))


def test_missing_genres_do_not_prove_science_fiction_absence():
    assert not passes_filters(movie("Q4", "Unknown", []), HardFilters(excluded_genres=["sci-fi"]))
    assert passes_filters(movie("Q4", "Unknown", []), HardFilters())


def test_reference_query_builder_sees_actual_reference_evidence():
    reference = movie("Q1", "Interstellar")
    candidate = movie("Q2", "Family")
    llm = FakeLLM(
        Intent(reference_title="Interstellar", semantic_query="similar movie"),
        Selection(recommendations=[]),
        ReferenceQuery(semantic_query="Parent and child reconnect after separation"),
    )
    embedder = FakeEmbedder()
    engine = RecommendationEngine(llm=llm, embedder=embedder, repository=FakeRepository([candidate], [reference]))
    engine.recommend("A movie similar to Interstellar")
    prompt = next(prompt for schema, prompt in llm.calls if schema is ReferenceQuery)
    assert reference.plot in prompt
    assert embedder.last_query == "Parent and child reconnect after separation"


def test_fabricated_evidence_is_not_returned_to_user():
    candidate = movie("Q2", "Family")
    llm = FakeLLM(
        Intent(semantic_query="family bonds"),
        Selection(recommendations=[{
            "movie_id": "Q2", "explanation": "A parent returns from space.",
            "evidence_quote": "The parent returns from a space station.",
        }]),
    )
    result = RecommendationEngine(llm=llm, embedder=FakeEmbedder(), repository=FakeRepository([candidate])).recommend("Family drama")
    assert result.recommendations == []
    assert "evidence-supported" in result.message


def test_invalid_model_schema_is_a_model_failure():
    from v_me_50.errors import InvalidModelOutput
    class BadLLM:
        def with_structured_output(self, schema):
            return RunnableLambda(lambda _prompt: {"not_an_intent": True})
    engine = RecommendationEngine(llm=BadLLM(), embedder=FakeEmbedder(), repository=FakeRepository([]))
    with pytest.raises(InvalidModelOutput):
        engine.recommend("Family drama")


def test_http_to_langchain_pipeline_returns_validated_evidence():
    from fastapi.testclient import TestClient
    from v_me_50.app import create_app
    candidate = movie("Q2", "Family")
    llm = FakeLLM(
        Intent(semantic_query="family bonds", soft_preferences={"prefer": ["family"], "avoid": ["heavy sci-fi"]}),
        Selection(recommendations=[{
            "movie_id": "Q2", "explanation": "A parent and child reconnect after separation.",
            "evidence_quote": "A parent reconnects with a child after a long separation.",
        }]),
    )
    engine = RecommendationEngine(llm=llm, embedder=FakeEmbedder(), repository=FakeRepository([candidate]))
    with TestClient(create_app(engine=engine, verified_user=lambda: "verified-user")) as client:
        response = client.post("/v1/recommendations", json={"query": "Family drama"})
    assert response.status_code == 200
    recommendation = response.json()["recommendations"][0]
    assert recommendation["movie_id"] == "Q2"
    assert recommendation["evidence_quote"] in candidate.plot
    assert [schema for schema, _ in llm.calls] == [Intent, Selection]
    assert "heavy sci-fi" in llm.calls[-1][1]


def test_pipeline_closes_owned_resources_once_and_rejects_use_after_shutdown():
    from v_me_50.errors import ConfigurationError
    calls = []
    engine = RecommendationEngine(
        llm=FakeLLM(Intent(semantic_query="family"), Selection(recommendations=[])),
        embedder=FakeEmbedder(), repository=FakeRepository([]), closers=(lambda: calls.append("closed"),),
    )
    engine.close()
    engine.close()
    assert calls == ["closed"]
    with pytest.raises(ConfigurationError):
        engine.recommend("Family drama")

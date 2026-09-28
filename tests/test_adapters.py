import json

import httpx
import pytest

from v_me_50.adapters.supabase import SupabaseMovieRepository
from v_me_50.errors import RepositoryUnavailable
from v_me_50.models import HardFilters


def test_repository_sends_genre_aliases_and_reference_exclusion():
    captured = []
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json=[{"movie_id": "Q2", "title": "Family", "plot": "Parent and child reunite."}])
    with httpx.Client(base_url="https://catalog.test/rest/v1/", transport=httpx.MockTransport(handler)) as client:
        repository = SupabaseMovieRepository(url="https://catalog.test", publishable_key="test-key", client=client)
        rows = repository.search([1.0] + [0.0] * 1023, HardFilters(excluded_genres=["sci-fi"]),
                                 exclude_movie_id="Q1", limit=20)
    assert rows[0].movie_id == "Q2"
    assert captured[0]["excluded_movie_id"] == "Q1"
    assert {"science fiction", "sci-fi", "scifi"}.issubset(captured[0]["excluded_genres"])


@pytest.mark.parametrize("status,payload", [(500, {"message": "upstream error"}), (200, [{"invalid": "record"}])])
def test_repository_translates_bad_upstream_responses(status, payload):
    with httpx.Client(base_url="https://catalog.test/rest/v1/",
                     transport=httpx.MockTransport(lambda _request: httpx.Response(status, json=payload))) as client:
        repository = SupabaseMovieRepository(url="https://catalog.test", publishable_key="test-key", client=client)
        with pytest.raises(RepositoryUnavailable):
            repository.find_by_title("Interstellar")


def test_model_adapter_owns_and_closes_its_connection_without_a_network_call():
    from v_me_50.adapters.llm import OpenAIChatModel
    from v_me_50.models import Intent
    from v_me_50.settings import LLMSettings
    adapter = OpenAIChatModel(LLMSettings.from_env({"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"}))
    try:
        assert adapter.with_structured_output(Intent) is not None
        assert not adapter.http_client.is_closed
    finally:
        adapter.close()
    assert adapter.http_client.is_closed

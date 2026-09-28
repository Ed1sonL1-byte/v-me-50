import pytest

from v_me_50.errors import ConfigurationError
from v_me_50.settings import LLMSettings, RetrievalSettings


def test_retrieval_settings_do_not_require_llm_credentials():
    settings = RetrievalSettings.from_env({"SUPABASE_URL": "https://catalog.test", "SUPABASE_PUBLISHABLE_KEY": "read-secret"})
    assert settings.candidate_limit == 20
    assert "read-secret" not in repr(settings)


def test_llm_settings_support_compatible_endpoint_without_exposing_key():
    settings = LLMSettings.from_env({"OPENAI_MODEL": "chosen-model", "OPENAI_API_KEY": "llm-secret",
                                     "OPENAI_BASE_URL": "https://provider.test/v1"})
    assert str(settings.base_url) == "https://provider.test/v1"
    assert "llm-secret" not in settings.model_dump_json()


def test_configuration_errors_name_missing_fields_without_values():
    with pytest.raises(ConfigurationError, match="OPENAI_MODEL"):
        LLMSettings.from_env({"OPENAI_API_KEY": "llm-secret"})
    with pytest.raises(ConfigurationError) as error:
        RetrievalSettings.from_env({"SUPABASE_URL": "not-a-url", "SUPABASE_PUBLISHABLE_KEY": "read-secret"})
    assert "read-secret" not in str(error.value)

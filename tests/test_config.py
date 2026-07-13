"""Tests for configuration loading."""

import pytest

from mini_agent.config import load_settings
from mini_agent.exceptions import ConfigurationError


@pytest.fixture
def isolated_env(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Run tests without project-root .env interference."""
    monkeypatch.chdir(tmp_path)
    for key in (
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL",
        "DEEPSEEK_MODEL",
        "REQUEST_TIMEOUT",
        "MAX_AGENT_STEPS",
    ):
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


def test_load_settings_reads_valid_config(isolated_env) -> None:
    isolated_env.setenv("DEEPSEEK_API_KEY", "test-key")
    isolated_env.setenv("DEEPSEEK_BASE_URL", "https://example.com")
    isolated_env.setenv("DEEPSEEK_MODEL", "test-model")
    isolated_env.setenv("REQUEST_TIMEOUT", "45.5")
    isolated_env.setenv("MAX_AGENT_STEPS", "20")
    settings = load_settings()
    assert settings.deepseek_api_key == "test-key"
    assert settings.deepseek_base_url == "https://example.com"
    assert settings.deepseek_model == "test-model"
    assert settings.request_timeout == 45.5
    assert isinstance(settings.request_timeout, float)
    assert settings.max_agent_steps == 20
    assert isinstance(settings.max_agent_steps, int)


def test_load_settings_uses_defaults(isolated_env) -> None:
    isolated_env.setenv("DEEPSEEK_API_KEY", "test-key")
    settings = load_settings()
    assert settings.deepseek_base_url == "https://api.deepseek.com"
    assert settings.deepseek_model == "deepseek-chat"
    assert settings.request_timeout == 30.0
    assert settings.max_agent_steps == 10


def test_load_settings_missing_api_key_raises(isolated_env) -> None:
    with pytest.raises(ConfigurationError):
        load_settings()


def test_load_settings_invalid_timeout_raises(isolated_env) -> None:
    isolated_env.setenv("DEEPSEEK_API_KEY", "test-key")
    isolated_env.setenv("REQUEST_TIMEOUT", "not-a-float")
    with pytest.raises(ConfigurationError):
        load_settings()


def test_load_settings_invalid_max_steps_raises(isolated_env) -> None:
    isolated_env.setenv("DEEPSEEK_API_KEY", "test-key")
    isolated_env.setenv("MAX_AGENT_STEPS", "abc")
    with pytest.raises(ConfigurationError):
        load_settings()

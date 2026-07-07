"""Tests for the --debug flag, centralized logging config, and error propagation.

Logging is configured once in the main callback (default WARNING). --debug
turns on DEBUG logging (including the SDK auth loggers) and full tracebacks
on unexpected errors. Identity upserts must not swallow update failures.
"""

import logging
from types import SimpleNamespace

import pytest
from scm.exceptions import APIError, NotFoundError

from src.scm_cli.main import app


@pytest.fixture(autouse=True)
def _mock_mode(monkeypatch):
    monkeypatch.setenv("SCM_MOCK", "1")


class TestDebugFlag:
    def test_debug_sets_root_logger_to_debug(self, runner):
        result = runner.invoke(app, ["--debug", "show", "object", "address", "--folder", "Texas"])

        assert result.exit_code == 0
        assert logging.getLogger().level == logging.DEBUG

    def test_debug_unpins_sdk_auth_loggers(self, runner):
        result = runner.invoke(app, ["--debug", "show", "object", "address", "--folder", "Texas"])

        assert result.exit_code == 0
        assert logging.getLogger("scm.auth").level != logging.CRITICAL
        assert logging.getLogger("oauthlib").level != logging.CRITICAL

    def test_default_pins_sdk_auth_loggers(self, runner):
        result = runner.invoke(app, ["show", "object", "address", "--folder", "Texas"])

        assert result.exit_code == 0
        assert logging.getLogger("scm.auth").level == logging.CRITICAL

    def test_debug_shows_traceback_on_error(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def boom(**kwargs):
            raise RuntimeError("kaboom")

        monkeypatch.setattr(scm_client, "list_addresses", boom)
        result = runner.invoke(app, ["--debug", "show", "object", "address", "--folder", "Texas"])

        assert result.exit_code == 1
        assert "kaboom" in result.output
        assert "Traceback" in result.output or "RuntimeError" in result.output

    def test_no_debug_hides_traceback(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def boom(**kwargs):
            raise RuntimeError("kaboom")

        monkeypatch.setattr(scm_client, "list_addresses", boom)
        result = runner.invoke(app, ["show", "object", "address", "--folder", "Texas"])

        assert result.exit_code == 1
        assert "kaboom" in result.output
        assert "Traceback" not in result.output


class TestLogLevelValidation:
    def test_invalid_scm_log_level_warns_but_works(self, runner, monkeypatch):
        monkeypatch.setenv("SCM_LOG_LEVEL", "VERBOSE")
        result = runner.invoke(app, ["show", "object", "address", "--folder", "Texas"])

        assert result.exit_code == 0
        assert "VERBOSE" in result.output  # warning names the bad value

    def test_valid_scm_log_level_applies(self, runner, monkeypatch):
        monkeypatch.setenv("SCM_LOG_LEVEL", "ERROR")
        result = runner.invoke(app, ["show", "object", "address", "--folder", "Texas"])

        assert result.exit_code == 0
        assert logging.getLogger().level == logging.ERROR


class TestUpsertErrorPropagation:
    """Update failures in identity upserts must propagate, not fall through to create."""

    def _client_with_fake_sdk(self, monkeypatch, fake_profile):
        monkeypatch.delenv("SCM_MOCK", raising=False)
        import scm_cli.utils.sdk_client as sdk_module

        client = object.__new__(sdk_module.SCMClient)  # skip __init__
        client.logger = logging.getLogger("test")
        client.client = SimpleNamespace(authentication_profile=fake_profile)
        return client

    def test_update_failure_propagates(self, monkeypatch):
        calls = {"create": 0}

        class FakeProfile:
            def fetch(self, **kwargs):
                return SimpleNamespace(id="p1")

            def update(self, existing):
                raise APIError("update failed")

            def create(self, data):
                calls["create"] += 1
                raise AssertionError("create must not run after a failed update")

        client = self._client_with_fake_sdk(monkeypatch, FakeProfile())

        with pytest.raises(APIError, match="update failed"):
            client.create_authentication_profile(name="p1", folder="Texas")
        assert calls["create"] == 0

    def test_not_found_falls_through_to_create(self, monkeypatch):
        class FakeProfile:
            def fetch(self, **kwargs):
                raise NotFoundError("nope")

            def create(self, data):
                return SimpleNamespace(model_dump_json=lambda **kw: '{"id": "p1", "name": "p1"}')

        client = self._client_with_fake_sdk(monkeypatch, FakeProfile())

        result = client.create_authentication_profile(name="p1", folder="Texas")
        assert result["__action__"] == "created"

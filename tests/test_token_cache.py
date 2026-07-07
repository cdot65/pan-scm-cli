"""Tests for the OAuth token file cache (scm_cli.utils.token_cache).

Tokens fetched during OAuth login are cached per context so consecutive CLI
invocations skip the token + JWKS roundtrips. Cache entries carry the
client_id (needed for commit admin under cached-token bearer mode).
"""

import os
import time

import pytest

from scm_cli.utils import token_cache


@pytest.fixture(autouse=True)
def cache_dir(tmp_path, monkeypatch):
    """Point the cache at a temp directory for every test."""
    monkeypatch.setattr(token_cache, "CACHE_DIR", str(tmp_path / "cache"))
    return tmp_path / "cache"


def _token(expires_in: float = 3600.0) -> dict:
    return {"access_token": "tok-abc", "token_type": "Bearer", "expires_at": time.time() + expires_in}


class TestSaveAndLoad:
    def test_round_trip(self):
        token_cache.save_token("prod", _token(), client_id="cid@x.com", tsg_id="123")
        entry = token_cache.load_token("prod")

        assert entry is not None
        assert entry["token"]["access_token"] == "tok-abc"
        assert entry["client_id"] == "cid@x.com"
        assert entry["tsg_id"] == "123"

    def test_no_context_uses_default_name(self):
        token_cache.save_token(None, _token(), client_id="cid", tsg_id="1")
        assert token_cache.load_token(None) is not None

    def test_file_permissions_0600(self, cache_dir):
        token_cache.save_token("prod", _token(), client_id="cid", tsg_id="1")
        files = list(cache_dir.iterdir())
        assert len(files) == 1
        assert oct(files[0].stat().st_mode & 0o777) == "0o600"

    def test_contexts_are_isolated(self):
        token_cache.save_token("a", _token(), client_id="cid-a", tsg_id="1")
        token_cache.save_token("b", _token(), client_id="cid-b", tsg_id="2")

        assert token_cache.load_token("a")["client_id"] == "cid-a"
        assert token_cache.load_token("b")["client_id"] == "cid-b"


class TestExpiryAndCorruption:
    def test_expired_token_returns_none(self):
        token_cache.save_token("prod", _token(expires_in=10), client_id="cid", tsg_id="1")
        # within the 5-minute safety buffer -> treated as expired
        assert token_cache.load_token("prod") is None

    def test_missing_cache_returns_none(self):
        assert token_cache.load_token("nope") is None

    def test_corrupt_cache_tolerated_and_cleared(self, cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
        path = cache_dir / "token-prod.json"
        path.write_text("{not json")

        assert token_cache.load_token("prod") is None
        assert not path.exists()

    def test_token_without_expiry_returns_none(self):
        token_cache.save_token("prod", {"access_token": "x"}, client_id="cid", tsg_id="1")
        assert token_cache.load_token("prod") is None


class TestClear:
    def test_clear_removes_entry(self):
        token_cache.save_token("prod", _token(), client_id="cid", tsg_id="1")
        token_cache.clear_token("prod")
        assert token_cache.load_token("prod") is None

    def test_clear_missing_is_noop(self):
        token_cache.clear_token("never-existed")


class TestDisableSwitch:
    def test_env_var_disables_cache(self, monkeypatch):
        token_cache.save_token("prod", _token(), client_id="cid", tsg_id="1")
        monkeypatch.setenv("SCM_NO_TOKEN_CACHE", "1")

        assert token_cache.load_token("prod") is None

    def test_env_var_disables_save(self, monkeypatch, cache_dir):
        monkeypatch.setenv("SCM_NO_TOKEN_CACHE", "1")
        token_cache.save_token("prod", _token(), client_id="cid", tsg_id="1")

        assert not (cache_dir / "token-prod.json").exists()


class TestClientIntegration:
    """SCMClient uses the cache: hit -> bearer-mode init (no OAuth), miss -> OAuth + save."""

    def _fresh_client(self, monkeypatch, fake_scm):
        import scm_cli.utils.sdk_client as sdk_module
        from scm_cli.utils.context import get_context_aware_settings

        monkeypatch.delenv("SCM_MOCK", raising=False)
        monkeypatch.setenv("SCM_SCM_CLIENT_ID", "cid@x.com")
        monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "sec")
        monkeypatch.setenv("SCM_SCM_TSG_ID", "123")
        monkeypatch.setattr(sdk_module, "Scm", fake_scm)
        monkeypatch.setattr(sdk_module, "get_current_context", lambda: None)
        monkeypatch.setattr(sdk_module, "settings", get_context_aware_settings())
        import scm_cli.utils.config as cfg_mod

        monkeypatch.setattr(cfg_mod, "settings", get_context_aware_settings())
        return sdk_module.SCMClient()

    def test_cache_hit_uses_bearer_mode(self, monkeypatch):
        token_cache.save_token(None, _token(), client_id="cid@x.com", tsg_id="123")
        captured = {}

        class FakeScm:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        client = self._fresh_client(monkeypatch, FakeScm)

        assert captured.get("access_token") == "tok-abc"
        assert "client_secret" not in captured
        assert client._cached_token_mode is True

    def test_cache_hit_for_other_client_id_ignored(self, monkeypatch):
        token_cache.save_token(None, _token(), client_id="someone-else", tsg_id="123")
        captured = {}

        class FakeScm:
            oauth_client = None

            def __init__(self, **kwargs):
                captured.update(kwargs)

        client = self._fresh_client(monkeypatch, FakeScm)

        assert "access_token" not in captured
        assert captured.get("client_id") == "cid@x.com"
        assert client._cached_token_mode is False

    def test_cache_miss_saves_token_after_oauth(self, monkeypatch):
        from types import SimpleNamespace

        fresh_token = {"access_token": "new-tok", "expires_at": time.time() + 900}

        class FakeScm:
            def __init__(self, **kwargs):
                self.oauth_client = SimpleNamespace(session=SimpleNamespace(token=fresh_token))

        self._fresh_client(monkeypatch, FakeScm)

        entry = token_cache.load_token(None)
        assert entry is not None
        assert entry["token"]["access_token"] == "new-tok"
        assert entry["client_id"] == "cid@x.com"

"""Tests for API/auth endpoint override support (api_base_url, token_url)."""

import os

import yaml

from src.scm_cli.utils.context import create_context, get_context_config
from src.scm_cli.utils.config import get_auth_config
from src.scm_cli.main import app as main_app
from src.scm_cli.commands import context as context_module

main_app.add_typer(context_module.app, name="context")

API_URL = "https://api.example.paloaltonetworks.com"
TOKEN_URL = "https://auth.example.paloaltonetworks.com/oauth2/access_token"


class FakeScm:
    """Stand-in for scm.client.Scm that records init kwargs.

    Has a real signature so the inspect.signature guard in sdk_client.py
    sees api_base_url/token_url as supported parameters.
    """

    last_kwargs: dict = {}

    def __init__(
        self,
        client_id=None,
        client_secret=None,
        tsg_id=None,
        access_token=None,
        api_base_url=None,
        token_url=None,
        log_level="INFO",
        region=None,
    ):
        FakeScm.last_kwargs = {
            "client_id": client_id,
            "client_secret": client_secret,
            "tsg_id": tsg_id,
            "access_token": access_token,
            "api_base_url": api_base_url,
            "token_url": token_url,
            "log_level": log_level,
            "region": region,
        }


class TestContextEndpointStorage:
    """Test api_base_url/token_url fields in context storage."""

    def test_create_context_with_endpoints(self, tmp_path, monkeypatch):
        """Endpoint URLs are stored in context YAML when provided."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        create_context(
            context_name="test-endpoints",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
            api_base_url=API_URL,
            token_url=TOKEN_URL,
        )

        context_file = tmp_path / "contexts" / "test-endpoints.yaml"
        assert context_file.exists()
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["api_base_url"] == API_URL
        assert data["token_url"] == TOKEN_URL

    def test_create_context_without_endpoints_omits_fields(self, tmp_path, monkeypatch):
        """Endpoint fields are absent from context YAML when not provided."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        create_context(
            context_name="test-no-endpoints",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
        )

        context_file = tmp_path / "contexts" / "test-no-endpoints.yaml"
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert "api_base_url" not in data
        assert "token_url" not in data

    def test_old_context_without_endpoints(self, tmp_path, monkeypatch):
        """Old context files without endpoint fields load fine and return None."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        os.makedirs(tmp_path / "contexts", exist_ok=True)
        old_context = tmp_path / "contexts" / "legacy.yaml"
        old_context.write_text("client_id: cid\nclient_secret: csec\ntsg_id: tsg\n")

        config = get_context_config("legacy")
        assert config.get("api_base_url") is None
        assert config.get("token_url") is None


class TestContextCreateEndpointCLI:
    """Test --api-base-url/--token-url flags on context create command."""

    def test_create_with_endpoint_flags(self, runner, tmp_path, monkeypatch):
        """Flags store endpoint URLs in context."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        result = runner.invoke(
            main_app,
            [
                "context",
                "create",
                "fedramp",
                "--client-id",
                "cid",
                "--client-secret",
                "csec",
                "--tsg-id",
                "tsg",
                "--api-base-url",
                API_URL,
                "--token-url",
                TOKEN_URL,
                "--no-set-current",
            ],
        )

        assert result.exit_code == 0
        context_file = tmp_path / "contexts" / "fedramp.yaml"
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["api_base_url"] == API_URL
        assert data["token_url"] == TOKEN_URL

    def test_create_without_endpoint_flags(self, runner, tmp_path, monkeypatch):
        """Omitting the flags leaves endpoint fields out of the context YAML."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        result = runner.invoke(
            main_app,
            [
                "context",
                "create",
                "plain",
                "--client-id",
                "cid",
                "--client-secret",
                "csec",
                "--tsg-id",
                "tsg",
                "--no-set-current",
            ],
        )

        assert result.exit_code == 0
        context_file = tmp_path / "contexts" / "plain.yaml"
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert "api_base_url" not in data
        assert "token_url" not in data

    def test_show_displays_endpoints_when_set(self, runner, tmp_path, monkeypatch):
        """context show displays endpoint URLs when configured."""
        ctx_dir = str(tmp_path / "contexts")
        cur_ctx_file = str(tmp_path / "current-context")
        for mod_path in ("src.scm_cli.utils.context", "scm_cli.utils.context"):
            monkeypatch.setattr(f"{mod_path}.CONTEXT_DIR", ctx_dir)
            monkeypatch.setattr(f"{mod_path}.CURRENT_CONTEXT_FILE", cur_ctx_file)

        create_context(
            context_name="fed",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
            api_base_url=API_URL,
            token_url=TOKEN_URL,
        )

        result = runner.invoke(main_app, ["context", "show", "fed"])
        assert result.exit_code == 0
        assert API_URL in result.output
        assert TOKEN_URL in result.output

    def test_show_displays_defaults_when_unset(self, runner, tmp_path, monkeypatch):
        """context show indicates SDK defaults when endpoints not configured."""
        ctx_dir = str(tmp_path / "contexts")
        cur_ctx_file = str(tmp_path / "current-context")
        for mod_path in ("src.scm_cli.utils.context", "scm_cli.utils.context"):
            monkeypatch.setattr(f"{mod_path}.CONTEXT_DIR", ctx_dir)
            monkeypatch.setattr(f"{mod_path}.CURRENT_CONTEXT_FILE", cur_ctx_file)

        create_context(
            context_name="plain",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
        )

        result = runner.invoke(main_app, ["context", "show", "plain"])
        assert result.exit_code == 0
        assert "default" in result.output.lower()


class TestEndpointsInAuthConfig:
    """Test endpoint overrides flow through auth config."""

    def test_auth_config_omits_endpoints_when_unset(self, monkeypatch):
        """get_auth_config has no endpoint keys when nothing is configured."""
        monkeypatch.setenv("SCM_SCM_CLIENT_ID", "cid")
        monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "csec")
        monkeypatch.setenv("SCM_SCM_TSG_ID", "tsg")
        monkeypatch.delenv("SCM_API_BASE_URL", raising=False)
        monkeypatch.delenv("SCM_TOKEN_URL", raising=False)

        import src.scm_cli.utils.config as src_config_mod
        from scm_cli.utils.context import get_context_aware_settings

        monkeypatch.setattr(src_config_mod, "settings", get_context_aware_settings())

        auth = get_auth_config()
        assert "api_base_url" not in auth
        assert "token_url" not in auth

    def test_auth_config_endpoints_from_env(self, monkeypatch):
        """SCM_API_BASE_URL / SCM_TOKEN_URL env vars flow into auth config."""
        monkeypatch.setenv("SCM_SCM_CLIENT_ID", "cid")
        monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "csec")
        monkeypatch.setenv("SCM_SCM_TSG_ID", "tsg")
        monkeypatch.setenv("SCM_API_BASE_URL", API_URL)
        monkeypatch.setenv("SCM_TOKEN_URL", TOKEN_URL)

        import src.scm_cli.utils.config as src_config_mod
        from scm_cli.utils.context import get_context_aware_settings

        monkeypatch.setattr(src_config_mod, "settings", get_context_aware_settings())

        auth = get_auth_config()
        assert auth["api_base_url"] == API_URL
        assert auth["token_url"] == TOKEN_URL

    def test_auth_config_endpoints_from_context(self, tmp_path, monkeypatch):
        """get_auth_config picks up endpoint URLs from the active context."""
        import scm_cli.utils.context as ctx_mod
        import src.scm_cli.utils.context as src_ctx_mod
        import src.scm_cli.utils.config as src_config_mod

        ctx_dir = str(tmp_path / "contexts")
        cur_ctx_file = str(tmp_path / "current-context")
        for mod in (ctx_mod, src_ctx_mod):
            monkeypatch.setattr(mod, "CONTEXT_DIR", ctx_dir)
            monkeypatch.setattr(mod, "CURRENT_CONTEXT_FILE", cur_ctx_file)
            monkeypatch.setattr(mod, "get_current_context", lambda: "fed")

        create_context(
            context_name="fed",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
            api_base_url=API_URL,
            token_url=TOKEN_URL,
        )

        monkeypatch.delenv("SCM_API_BASE_URL", raising=False)
        monkeypatch.delenv("SCM_TOKEN_URL", raising=False)

        new_settings = ctx_mod.get_context_aware_settings()
        monkeypatch.setattr(src_config_mod, "settings", new_settings)

        auth = get_auth_config()
        assert auth["api_base_url"] == API_URL
        assert auth["token_url"] == TOKEN_URL

    def test_env_overrides_context(self, tmp_path, monkeypatch):
        """Env vars win over context-configured endpoint URLs."""
        import scm_cli.utils.context as ctx_mod
        import src.scm_cli.utils.context as src_ctx_mod
        import src.scm_cli.utils.config as src_config_mod

        ctx_dir = str(tmp_path / "contexts")
        cur_ctx_file = str(tmp_path / "current-context")
        for mod in (ctx_mod, src_ctx_mod):
            monkeypatch.setattr(mod, "CONTEXT_DIR", ctx_dir)
            monkeypatch.setattr(mod, "CURRENT_CONTEXT_FILE", cur_ctx_file)
            monkeypatch.setattr(mod, "get_current_context", lambda: "fed")

        create_context(
            context_name="fed",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
            api_base_url="https://context-api.example.com",
            token_url="https://context-auth.example.com/token",
        )

        monkeypatch.setenv("SCM_API_BASE_URL", API_URL)
        monkeypatch.setenv("SCM_TOKEN_URL", TOKEN_URL)

        new_settings = ctx_mod.get_context_aware_settings()
        monkeypatch.setattr(src_config_mod, "settings", new_settings)

        auth = get_auth_config()
        assert auth["api_base_url"] == API_URL
        assert auth["token_url"] == TOKEN_URL


class TestEndpointsReachScmInit:
    """Test endpoint overrides are passed into Scm() init by SCMClient."""

    def _fresh_client(self, monkeypatch):
        """Build an SCMClient with FakeScm patched in and fresh settings."""
        import scm_cli.utils.sdk_client as sdk_module
        from scm_cli.utils.context import get_context_aware_settings

        # These tests exercise real client init, so opt out of suite-wide mock mode
        monkeypatch.delenv("SCM_MOCK", raising=False)
        monkeypatch.setattr(sdk_module, "Scm", FakeScm)
        monkeypatch.setattr(sdk_module, "settings", get_context_aware_settings())
        import scm_cli.utils.config as cfg_mod

        monkeypatch.setattr(cfg_mod, "settings", get_context_aware_settings())
        FakeScm.last_kwargs = {}
        return sdk_module.SCMClient()

    def test_oauth2_mode_passes_endpoints(self, monkeypatch):
        """OAuth2 mode: endpoint env overrides reach Scm init."""
        monkeypatch.setenv("SCM_API_BASE_URL", API_URL)
        monkeypatch.setenv("SCM_TOKEN_URL", TOKEN_URL)

        self._fresh_client(monkeypatch)

        assert FakeScm.last_kwargs["api_base_url"] == API_URL
        assert FakeScm.last_kwargs["token_url"] == TOKEN_URL
        assert FakeScm.last_kwargs["client_id"] == "test-client-id"

    def test_oauth2_mode_omits_endpoints_when_unset(self, monkeypatch):
        """OAuth2 mode: kwargs absent when no override set (SDK defaults apply)."""
        monkeypatch.delenv("SCM_API_BASE_URL", raising=False)
        monkeypatch.delenv("SCM_TOKEN_URL", raising=False)

        self._fresh_client(monkeypatch)

        assert FakeScm.last_kwargs["api_base_url"] is None
        assert FakeScm.last_kwargs["token_url"] is None

    def test_bearer_mode_passes_endpoints(self, monkeypatch):
        """Bearer token mode: endpoint env overrides reach Scm init."""
        monkeypatch.setenv("SCM_ACCESS_TOKEN", "bearer-tok")
        monkeypatch.setenv("SCM_API_BASE_URL", API_URL)
        monkeypatch.setenv("SCM_TOKEN_URL", TOKEN_URL)

        self._fresh_client(monkeypatch)

        assert FakeScm.last_kwargs["access_token"] == "bearer-tok"
        assert FakeScm.last_kwargs["api_base_url"] == API_URL
        assert FakeScm.last_kwargs["token_url"] == TOKEN_URL

    def test_bearer_mode_omits_endpoints_when_unset(self, monkeypatch):
        """Bearer token mode: kwargs absent when no override set."""
        monkeypatch.setenv("SCM_ACCESS_TOKEN", "bearer-tok")
        monkeypatch.delenv("SCM_API_BASE_URL", raising=False)
        monkeypatch.delenv("SCM_TOKEN_URL", raising=False)

        self._fresh_client(monkeypatch)

        assert FakeScm.last_kwargs["access_token"] == "bearer-tok"
        assert FakeScm.last_kwargs["api_base_url"] is None
        assert FakeScm.last_kwargs["token_url"] is None

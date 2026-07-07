"""Tests for region support in context management."""

import os

import yaml

from src.scm_cli.commands import context as context_module
from src.scm_cli.main import app as main_app
from src.scm_cli.utils.config import get_auth_config
from src.scm_cli.utils.context import create_context, get_context_config

main_app.add_typer(context_module.app, name="context")


class TestContextRegion:
    """Test region field in context storage."""

    def test_create_context_with_region(self, tmp_path, monkeypatch):
        """Region is stored in context YAML when provided."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        create_context(
            context_name="test-region",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
            region="europe",
        )

        context_file = tmp_path / "contexts" / "test-region.yaml"
        assert context_file.exists()
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["region"] == "europe"

    def test_create_context_default_region(self, tmp_path, monkeypatch):
        """Region defaults to 'americas' when not provided."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        create_context(
            context_name="test-default",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
        )

        context_file = tmp_path / "contexts" / "test-default.yaml"
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["region"] == "americas"

    def test_old_context_without_region_defaults(self, tmp_path, monkeypatch):
        """Old context files without region field return 'americas'."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        os.makedirs(tmp_path / "contexts", exist_ok=True)
        old_context = tmp_path / "contexts" / "legacy.yaml"
        old_context.write_text("client_id: cid\nclient_secret: csec\ntsg_id: tsg\n")

        config = get_context_config("legacy")
        assert config.get("region", "americas") == "americas"


class TestContextCreateRegionCLI:
    """Test --region flag on context create command."""

    def test_create_with_region_flag(self, runner, tmp_path, monkeypatch):
        """--region flag stores region in context."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        result = runner.invoke(main_app, [
            "context", "create", "eu-prod",
            "--client-id", "cid",
            "--client-secret", "csec",
            "--tsg-id", "tsg",
            "--region", "europe",
            "--no-set-current",
        ])

        assert result.exit_code == 0
        context_file = tmp_path / "contexts" / "eu-prod.yaml"
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["region"] == "europe"

    def test_create_without_region_defaults_americas(self, runner, tmp_path, monkeypatch):
        """Omitting --region stores 'americas' as default."""
        monkeypatch.setattr("src.scm_cli.utils.context.CONTEXT_DIR", str(tmp_path / "contexts"))
        monkeypatch.setattr("src.scm_cli.utils.context.CURRENT_CONTEXT_FILE", str(tmp_path / "current-context"))

        result = runner.invoke(main_app, [
            "context", "create", "us-prod",
            "--client-id", "cid",
            "--client-secret", "csec",
            "--tsg-id", "tsg",
            "--no-set-current",
        ])

        assert result.exit_code == 0
        context_file = tmp_path / "contexts" / "us-prod.yaml"
        with open(context_file) as f:
            data = yaml.safe_load(f)
        assert data["region"] == "americas"


class TestRegionInAuthConfig:
    """Test region flows through auth config."""

    def test_auth_config_includes_region_from_settings(self, monkeypatch):
        """get_auth_config returns region from settings."""
        monkeypatch.setenv("SCM_SCM_CLIENT_ID", "cid")
        monkeypatch.setenv("SCM_SCM_CLIENT_SECRET", "csec")
        monkeypatch.setenv("SCM_SCM_TSG_ID", "tsg")

        import src.scm_cli.utils.config as src_config_mod
        from scm_cli.utils.context import get_context_aware_settings

        monkeypatch.setattr(src_config_mod, "settings", get_context_aware_settings())

        auth = get_auth_config()
        assert "region" in auth
        assert auth["region"] == "americas"  # default when not set

    def test_auth_config_region_from_context(self, tmp_path, monkeypatch):
        """get_auth_config picks up region from context settings."""
        import scm_cli.utils.context as ctx_mod
        import src.scm_cli.utils.config as src_config_mod
        import src.scm_cli.utils.context as src_ctx_mod

        # Patch both module instances (src. prefix and without)
        ctx_dir = str(tmp_path / "contexts")
        cur_ctx_file = str(tmp_path / "current-context")
        for mod in (ctx_mod, src_ctx_mod):
            monkeypatch.setattr(mod, "CONTEXT_DIR", ctx_dir)
            monkeypatch.setattr(mod, "CURRENT_CONTEXT_FILE", cur_ctx_file)
            monkeypatch.setattr(mod, "get_current_context", lambda: "eu")

        create_context(
            context_name="eu",
            client_id="cid",
            client_secret="csec",
            tsg_id="tsg",
            region="europe",
        )

        # Must patch the src. module since get_auth_config was imported from there
        new_settings = ctx_mod.get_context_aware_settings()
        monkeypatch.setattr(src_config_mod, "settings", new_settings)

        auth = get_auth_config()
        assert auth["region"] == "europe"


class TestRegionOverride:
    """Test global --region flag override."""

    def test_get_region_override_default_none(self):
        """get_region_override returns None when no override set."""
        # Reset the module-level variable
        import scm_cli.main as main_mod
        from scm_cli.main import get_region_override

        main_mod._region_override = None
        assert get_region_override() is None

    def test_region_override_set(self):
        """get_region_override returns value after being set."""
        import sys

        from scm_cli.main import get_region_override

        main_mod = sys.modules["scm_cli.main"]
        main_mod._region_override = "europe"
        assert get_region_override() == "europe"
        # Clean up
        main_mod._region_override = None

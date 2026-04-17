"""Tests for region support in context management."""

import os

import yaml
import pytest

from src.scm_cli.utils.context import create_context, get_context_config
from src.scm_cli.main import app as main_app
from src.scm_cli.commands import context as context_module

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

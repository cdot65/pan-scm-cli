"""Tests for the setup commands module."""

import pytest
import typer
from pydantic import ValidationError

from scm_cli.commands.setup import (
    backup_app,
    delete_app,
    delete_folder,
    delete_label,
    delete_snippet,
    delete_variable,
    load_app,
    set_app,
    set_folder,
    set_label,
    set_snippet,
    set_variable,
    show_app,
    show_device,
    show_folder,
    show_label,
    show_snippet,
    show_variable,
)
from scm_cli.utils.validators import Folder, Label, Snippet, Variable


class TestSetupCommandsExist:
    """Test that all setup command apps exist."""

    def test_set_app_exists(self):
        assert set_app

    def test_show_app_exists(self):
        assert show_app

    def test_delete_app_exists(self):
        assert delete_app

    def test_load_app_exists(self):
        assert load_app

    def test_backup_app_exists(self):
        assert backup_app


class TestFolderCommands:
    """Test folder commands."""

    def test_set_folder_command(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "folder-123",
                "name": kwargs.get("name"),
                "parent": kwargs.get("parent"),
                "description": kwargs.get("description", ""),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_folder", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_folder)

        result = runner.invoke(
            test_app,
            ["--name", "Texas", "--parent", "All", "--description", "Texas offices"],
        )

        assert result.exit_code == 0
        assert "Created folder" in result.stdout
        assert "Texas" in result.stdout

    def test_show_folder_list(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "f1", "name": "All", "parent": ""},
                {"id": "f2", "name": "Texas", "parent": "All"},
            ]

        monkeypatch.setattr(scm_client, "list_folders", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_folder)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "All" in result.stdout
        assert "Texas" in result.stdout

    def test_show_folder_by_name(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {"id": "f1", "name": "Texas", "parent": "All", "description": "Texas offices"}

        monkeypatch.setattr(scm_client, "get_folder", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_folder)

        result = runner.invoke(test_app, ["--name", "Texas"])

        assert result.exit_code == 0
        assert "Texas" in result.stdout

    def test_delete_folder_command(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "delete_folder", lambda *a, **kw: True)

        test_app = typer.Typer()
        test_app.command()(delete_folder)

        result = runner.invoke(test_app, ["--name", "Texas", "--force"])

        assert result.exit_code == 0
        assert "Deleted folder" in result.stdout


class TestLabelCommands:
    """Test label commands."""

    def test_set_label_command(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "label-123",
                "name": kwargs.get("name"),
                "description": kwargs.get("description", ""),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_label", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_label)

        result = runner.invoke(
            test_app,
            ["--name", "production", "--description", "Prod environment"],
        )

        assert result.exit_code == 0
        assert "Created label" in result.stdout

    def test_show_label_list(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "l1", "name": "production", "description": "Prod"},
                {"id": "l2", "name": "staging"},
            ]

        monkeypatch.setattr(scm_client, "list_labels", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_label)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "production" in result.stdout

    def test_delete_label_command(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "delete_label", lambda *a, **kw: True)

        test_app = typer.Typer()
        test_app.command()(delete_label)

        result = runner.invoke(test_app, ["--name", "staging", "--force"])

        assert result.exit_code == 0
        assert "Deleted label" in result.stdout


class TestSnippetCommands:
    """Test snippet commands."""

    def test_set_snippet_command(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "snippet-123",
                "name": kwargs.get("name"),
                "description": kwargs.get("description", ""),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_snippet", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_snippet)

        result = runner.invoke(
            test_app,
            ["--name", "DNS-Best-Practice", "--description", "DNS config"],
        )

        assert result.exit_code == 0
        assert "Created snippet" in result.stdout

    def test_show_snippet_list(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "s1", "name": "DNS-Best-Practice", "type": "predefined"},
                {"id": "s2", "name": "Web-Security", "type": "custom"},
            ]

        monkeypatch.setattr(scm_client, "list_snippets", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_snippet)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "DNS-Best-Practice" in result.stdout

    def test_delete_snippet_command(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "delete_snippet", lambda *a, **kw: True)

        test_app = typer.Typer()
        test_app.command()(delete_snippet)

        result = runner.invoke(test_app, ["--name", "Web-Security", "--force"])

        assert result.exit_code == 0
        assert "Deleted snippet" in result.stdout


class TestVariableCommands:
    """Test variable commands."""

    def test_set_variable_command(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "var-123",
                "name": kwargs.get("name"),
                "type": kwargs.get("type"),
                "value": kwargs.get("value"),
                "folder": kwargs.get("folder"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_variable", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_variable)

        result = runner.invoke(
            test_app,
            ["--name", "$egress-max", "--type", "egress-max", "--value", "1000", "--folder", "Texas"],
        )

        assert result.exit_code == 0
        assert "Created variable" in result.stdout

    def test_show_variable_list(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "v1", "name": "$egress-max", "type": "egress-max", "value": "1000"},
            ]

        monkeypatch.setattr(scm_client, "list_variables", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_variable)

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "$egress-max" in result.stdout

    def test_delete_variable_command(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "delete_variable", lambda *a, **kw: True)

        test_app = typer.Typer()
        test_app.command()(delete_variable)

        result = runner.invoke(test_app, ["--name", "$egress-max", "--folder", "Texas", "--force"])

        assert result.exit_code == 0
        assert "Deleted variable" in result.stdout

    def test_variable_requires_container(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_variable", lambda *a, **kw: {})

        test_app = typer.Typer()
        test_app.command()(set_variable)

        result = runner.invoke(
            test_app,
            ["--name", "$test", "--type", "fqdn", "--value", "example.com"],
        )

        # Should fail because no container is specified
        assert result.exit_code != 0


class TestDeviceCommands:
    """Test device commands (read-only)."""

    def test_show_device_list(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "d1", "name": "PA-VM-01", "model": "PA-VM", "is_connected": True},
                {"id": "d2", "name": "PA-VM-02", "model": "PA-VM", "is_connected": False},
            ]

        monkeypatch.setattr(scm_client, "list_devices", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_device)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "PA-VM-01" in result.stdout
        assert "PA-VM-02" in result.stdout

    def test_show_device_by_name(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "d1",
                "name": "PA-VM-01",
                "serial_number": "0123456789",
                "model": "PA-VM",
                "software_version": "11.1.0",
                "is_connected": True,
            }

        monkeypatch.setattr(scm_client, "get_device", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_device)

        result = runner.invoke(test_app, ["--name", "PA-VM-01"])

        assert result.exit_code == 0
        assert "PA-VM-01" in result.stdout
        assert "PA-VM" in result.stdout


class TestSetupValidators:
    """Test setup validator models."""

    def test_folder_validator(self):
        folder = Folder(name="Texas", parent="All", description="Texas offices")
        sdk = folder.to_sdk_model()
        assert sdk["name"] == "Texas"
        assert sdk["parent"] == "All"
        assert sdk["description"] == "Texas offices"

    def test_folder_minimal(self):
        folder = Folder(name="Branch", parent="All")
        sdk = folder.to_sdk_model()
        assert sdk["name"] == "Branch"
        assert sdk["parent"] == "All"
        assert "description" not in sdk

    def test_label_validator(self):
        label = Label(name="production", description="Production environment")
        sdk = label.to_sdk_model()
        assert sdk["name"] == "production"
        assert sdk["description"] == "Production environment"

    def test_label_minimal(self):
        label = Label(name="staging")
        sdk = label.to_sdk_model()
        assert sdk["name"] == "staging"
        assert "description" not in sdk

    def test_snippet_validator(self):
        snippet = Snippet(name="DNS-Best-Practice", description="DNS config", labels=["prod"])
        sdk = snippet.to_sdk_model()
        assert sdk["name"] == "DNS-Best-Practice"
        assert sdk["description"] == "DNS config"
        assert sdk["labels"] == ["prod"]

    def test_snippet_with_enable_prefix(self):
        snippet = Snippet(name="test", enable_prefix=True)
        sdk = snippet.to_sdk_model()
        assert sdk["enable_prefix"] is True

    def test_variable_validator(self):
        var = Variable(name="$egress-max", type="egress-max", value="1000", folder="Texas")
        sdk = var.to_sdk_model()
        assert sdk["name"] == "$egress-max"
        assert sdk["type"] == "egress-max"
        assert sdk["value"] == "1000"
        assert sdk["folder"] == "Texas"

    def test_variable_invalid_type(self):
        with pytest.raises(ValidationError):
            Variable(name="$test", type="invalid-type", value="123", folder="Texas")

    def test_variable_requires_container(self):
        with pytest.raises(ValidationError):
            Variable(name="$test", type="fqdn", value="example.com")

    def test_variable_multiple_containers(self):
        with pytest.raises(ValidationError):
            Variable(name="$test", type="fqdn", value="example.com", folder="Texas", snippet="DNS")

    def test_variable_snippet_container(self):
        var = Variable(name="$dns", type="fqdn", value="dns.example.com", snippet="DNS-Config")
        sdk = var.to_sdk_model()
        assert sdk["snippet"] == "DNS-Config"
        assert "folder" not in sdk

    def test_variable_device_container(self):
        var = Variable(name="$ip", type="ip-netmask", value="10.0.0.1/32", device="fw-01")
        sdk = var.to_sdk_model()
        assert sdk["device"] == "fw-01"
        assert "folder" not in sdk

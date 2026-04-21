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
    set_device,
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
from scm_cli.utils.validators import Device, Folder, Label, Snippet, Variable


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

    def test_device_minimal(self):
        from scm_cli.utils.validators import Device
        device = Device(name="PA-VM-01")
        sdk = device.to_sdk_model()
        assert sdk == {"name": "PA-VM-01"}

    def test_device_all_fields(self):
        from scm_cli.utils.validators import Device
        device = Device(
            name="PA-VM-01",
            display_name="Edge-FW",
            folder="Austin",
            description="Edge firewall",
            labels=["production", "west"],
            snippets=["DNS-Best-Practice"],
        )
        sdk = device.to_sdk_model()
        assert sdk["name"] == "PA-VM-01"
        assert sdk["display_name"] == "Edge-FW"
        assert sdk["folder"] == "Austin"
        assert sdk["description"] == "Edge firewall"
        assert sdk["labels"] == ["production", "west"]
        assert sdk["snippets"] == ["DNS-Best-Practice"]

    def test_device_ignores_read_only_extras(self):
        from scm_cli.utils.validators import Device
        device = Device(
            name="PA-VM-01",
            labels=["prod"],
            serial_number="0123456789",
            model="PA-VM",
            hostname="pa-vm-01",
            is_connected=True,
            id="device-uuid",
        )
        sdk = device.to_sdk_model()
        assert sdk == {"name": "PA-VM-01", "labels": ["prod"]}

    def test_device_empty_labels_list_passes_through(self):
        from scm_cli.utils.validators import Device
        device = Device(name="PA-VM-01", labels=[])
        sdk = device.to_sdk_model()
        assert sdk == {"name": "PA-VM-01", "labels": []}

    def test_device_requires_name(self):
        from scm_cli.utils.validators import Device
        with pytest.raises(ValidationError):
            Device()

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


class TestDeviceCommands:
    """Test device commands."""

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

    def test_set_device_updates_labels(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_update(**kwargs):
            captured.update(kwargs)
            return {
                "id": "device-PA-VM-01",
                "name": kwargs.get("name"),
                "labels": kwargs.get("labels", []),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_device)

        result = runner.invoke(
            test_app,
            ["--name", "PA-VM-01", "--labels", "production", "--labels", "west"],
        )

        assert result.exit_code == 0, result.stdout
        assert "Updated device" in result.stdout
        assert captured["name"] == "PA-VM-01"
        assert captured["labels"] == ["production", "west"]

    def test_set_device_all_fields(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_update(**kwargs):
            captured.update(kwargs)
            return {"name": kwargs["name"], "__action__": "updated"}

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_device)

        result = runner.invoke(
            test_app,
            [
                "--name", "PA-VM-01",
                "--display-name", "Edge-FW",
                "--folder", "Austin",
                "--description", "Edge firewall",
                "--labels", "production",
                "--snippets", "DNS-Best-Practice",
            ],
        )

        assert result.exit_code == 0, result.stdout
        assert captured["display_name"] == "Edge-FW"
        assert captured["folder"] == "Austin"
        assert captured["description"] == "Edge firewall"
        assert captured["labels"] == ["production"]
        assert captured["snippets"] == ["DNS-Best-Practice"]

    def test_set_device_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_update(**kwargs):
            return {"name": kwargs["name"], "__action__": "no_change"}

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_device)

        result = runner.invoke(test_app, ["--name", "PA-VM-01", "--labels", "production"])

        assert result.exit_code == 0, result.stdout
        assert "No changes detected" in result.stdout

    def test_set_device_not_found_exits_nonzero(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_update(**kwargs):
            raise ValueError("Device 'missing' not found. Devices cannot be created via the CLI.")

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_device)

        result = runner.invoke(test_app, ["--name", "missing", "--labels", "x"])

        assert result.exit_code != 0
        assert "not found" in result.output

    def test_show_device_detail_includes_writable_fields(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(name):
            return {
                "id": "device-PA-VM-01",
                "name": name,
                "display_name": "Edge-FW",
                "hostname": "pa-vm-01",
                "serial_number": "0123456789",
                "model": "PA-VM",
                "folder": "Austin",
                "description": "Edge firewall",
                "labels": ["production", "west"],
                "snippets": ["DNS-Best-Practice"],
                "is_connected": True,
            }

        monkeypatch.setattr(scm_client, "get_device", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_device)

        result = runner.invoke(test_app, ["--name", "PA-VM-01"])

        assert result.exit_code == 0, result.stdout
        assert "Display Name: Edge-FW" in result.stdout
        assert "Description: Edge firewall" in result.stdout
        assert "Labels: production, west" in result.stdout
        assert "Snippets: DNS-Best-Practice" in result.stdout

    def test_show_device_list_shows_labels(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(folder=None):
            return [
                {
                    "id": "d1",
                    "name": "PA-VM-01",
                    "labels": ["production"],
                    "is_connected": True,
                },
            ]

        monkeypatch.setattr(scm_client, "list_devices", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_device)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0, result.stdout
        assert "PA-VM-01" in result.stdout
        assert "Labels: production" in result.stdout

    def test_load_device_processes_all_entries(self, runner, monkeypatch, tmp_path):
        from scm_cli.commands.setup import load_app
        from scm_cli.utils.sdk_client import scm_client

        captured_calls = []

        def mock_update(**kwargs):
            captured_calls.append(kwargs)
            return {"name": kwargs["name"], "__action__": "updated"}

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        import shutil
        from pathlib import Path
        fixture = Path(__file__).parent / "data" / "devices.yaml"
        target = tmp_path / "devices.yaml"
        shutil.copy(fixture, target)

        result = runner.invoke(load_app, ["device", "--file", str(target)])

        assert result.exit_code == 0, result.output
        assert len(captured_calls) == 2
        assert captured_calls[0]["name"] == "PA-VM-01"
        assert captured_calls[0]["labels"] == ["production", "west"]
        assert captured_calls[1]["name"] == "PA-VM-02"
        # Read-only fields must not reach the SDK call
        assert "serial_number" not in captured_calls[1]
        assert "is_connected" not in captured_calls[1]
        assert "Processed 2 devices" in result.output

    def test_load_device_dry_run_skips_sdk(self, runner, monkeypatch, tmp_path):
        from scm_cli.commands.setup import load_app
        from scm_cli.utils.sdk_client import scm_client

        called = {"n": 0}

        def mock_update(**kwargs):
            called["n"] += 1
            return {"name": kwargs["name"], "__action__": "updated"}

        monkeypatch.setattr(scm_client, "update_device", mock_update)

        import shutil
        from pathlib import Path
        fixture = Path(__file__).parent / "data" / "devices.yaml"
        target = tmp_path / "devices.yaml"
        shutil.copy(fixture, target)

        result = runner.invoke(load_app, ["device", "--file", str(target), "--dry-run"])

        assert result.exit_code == 0, result.output
        assert called["n"] == 0
        assert "Dry run" in result.output

    def test_backup_device_writes_yaml(self, runner, monkeypatch, tmp_path):
        from scm_cli.commands.setup import backup_app
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(folder=None):
            return [
                {
                    "id": "device-PA-VM-01",
                    "name": "PA-VM-01",
                    "display_name": "Edge-FW",
                    "serial_number": "0123456789",
                    "labels": ["production"],
                },
                {
                    "id": "device-PA-VM-02",
                    "name": "PA-VM-02",
                    "labels": ["staging"],
                },
            ]

        monkeypatch.setattr(scm_client, "list_devices", mock_list)

        out_file = tmp_path / "device-backup.yaml"
        result = runner.invoke(backup_app, ["device", "--file", str(out_file)])

        assert result.exit_code == 0, result.output
        assert out_file.exists()

        import yaml
        data = yaml.safe_load(out_file.read_text())
        assert "devices" in data
        assert len(data["devices"]) == 2
        assert data["devices"][0]["name"] == "PA-VM-01"
        # id must be stripped
        assert "id" not in data["devices"][0]
        assert "id" not in data["devices"][1]
        # labels must round-trip
        assert data["devices"][0]["labels"] == ["production"]

    def test_backup_device_empty_returns_message(self, runner, monkeypatch):
        from scm_cli.commands.setup import backup_app
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_devices", lambda folder=None: [])

        result = runner.invoke(backup_app, ["device"])

        assert result.exit_code == 0
        assert "No devices found" in result.output

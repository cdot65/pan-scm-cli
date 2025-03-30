"""Tests for the objects commands module."""

import typer
from scm_cli.commands.objects import (
    delete_address_group,
    delete_command,
    load_address_group,
    load_command,
    set_address_group,
    set_command,
)


class TestObjectsCommands:
    """Test the objects commands."""

    def test_set_command_exists(self):
        """Test that the set command exists."""
        assert set_command is not None
        assert isinstance(set_command, typer.Typer)

    def test_delete_command_exists(self):
        """Test that the delete command exists."""
        assert delete_command is not None
        assert isinstance(delete_command, typer.Typer)

    def test_load_command_exists(self):
        """Test that the load command exists."""
        assert load_command is not None
        assert isinstance(load_command, typer.Typer)


class TestAddressGroupCommands:
    """Test the address group commands."""

    def test_set_address_group_command(self, runner, monkeypatch):
        """Test the set address group command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "ag-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "type": kwargs.get("type"),
                "members": kwargs.get("members", []),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }

        monkeypatch.setattr(scm_client, "create_address_group", mock_create)

        # Invoke the command
        result = runner.invoke(
            set_address_group,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-group",
                "--type",
                "static",
                "--members",
                "192.168.1.0/24",
                "--members",
                "10.0.0.0/8",
                "--description",
                "Test address group",
                "--tag",
                "test",
                "--tag",
                "example",
            ],
        )

        assert result.exit_code == 0
        assert "Created address group" in result.stdout
        assert "ID: ag-12345" in result.stdout
        assert "Name: test-group" in result.stdout
        assert "Folder: test-folder" in result.stdout
        assert "Type: static" in result.stdout
        assert "Members: " in result.stdout
        assert "192.168.1.0/24" in result.stdout
        assert "10.0.0.0/8" in result.stdout
        assert "Description: Test address group" in result.stdout
        assert "Tags: " in result.stdout
        assert "test" in result.stdout
        assert "example" in result.stdout

    def test_set_address_group_error(self, runner, monkeypatch):
        """Test the set address group command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr(scm_client, "create_address_group", mock_create_error)

        # Invoke the command
        result = runner.invoke(set_address_group, ["--folder", "test-folder", "--name", "test-group", "--type", "static"])

        assert result.exit_code == 1
        assert "Error creating address group" in result.stdout
        assert "API Error" in result.stdout

    def test_delete_address_group_command(self, runner, monkeypatch):
        """Test the delete address group command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_address_group", mock_delete)

        # Invoke the command
        result = runner.invoke(delete_address_group, ["--folder", "test-folder", "--name", "test-group"])

        assert result.exit_code == 0
        assert "Deleted address group" in result.stdout
        assert "test-group" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_address_group_error(self, runner, monkeypatch):
        """Test the delete address group command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr(scm_client, "delete_address_group", mock_delete_error)

        # Invoke the command
        result = runner.invoke(delete_address_group, ["--folder", "test-folder", "--name", "test-group"])

        assert result.exit_code == 1
        assert "Error deleting address group" in result.stdout
        assert "API Error" in result.stdout

    def test_load_address_group_command(self, runner, monkeypatch, mock_address_groups_yaml_file):
        """Test the load address group command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        created_groups = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"ag-{len(created_groups) + 1}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "type": kwargs.get("type"),
                "members": kwargs.get("members", []),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }
            created_groups.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_address_group", mock_create)

        # Invoke the command
        result = runner.invoke(load_address_group, ["--file", str(mock_address_groups_yaml_file)])

        assert result.exit_code == 0
        assert "Loaded 1 address group(s)" in result.stdout
        assert len(created_groups) == 1
        assert created_groups[0]["name"] == "test-group"
        assert created_groups[0]["folder"] == "test-folder"
        assert created_groups[0]["type"] == "static"
        assert "192.168.1.0/24" in created_groups[0]["members"]
        assert "10.0.0.0/8" in created_groups[0]["members"]

    def test_load_address_group_dry_run(self, runner, monkeypatch, mock_address_groups_yaml_file):
        """Test the load address group command with dry-run option."""
        # Mock the SCM client method to track if it gets called
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_address_group", mock_create)

        # Invoke the command with dry-run
        result = runner.invoke(load_address_group, ["--file", str(mock_address_groups_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout
        assert "Would create address group" in result.stdout
        assert "test-group" in result.stdout
        assert not mock_called  # Ensure the mock wasn't called due to dry-run

    def test_load_address_group_error(self, runner, monkeypatch, mock_address_groups_yaml_file):
        """Test the load address group command with an error."""
        # Mock the config loader to simulate an error
        from scm_cli.utils import config

        def mock_load_error(*args, **kwargs):
            raise ValueError("Invalid file format")

        monkeypatch.setattr(config, "load_from_yaml", mock_load_error)

        # Invoke the command
        result = runner.invoke(load_address_group, ["--file", str(mock_address_groups_yaml_file)])

        assert result.exit_code == 1
        assert "Error loading address groups" in result.stdout
        assert "Invalid file format" in result.stdout

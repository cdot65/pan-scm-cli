"""Tests for the objects commands module."""

import typer
from scm_cli.commands.objects import (
    delete_address_group,
    delete_app,
    load_address_group,
    load_app,
    set_address_group,
    set_app,
)


class TestObjectsCommands:
    """Test the objects commands."""

    def test_set_command_exists(self):
        """Test that the set command exists."""
        assert set_app

    def test_delete_command_exists(self):
        """Test that the delete command exists."""
        assert delete_app

    def test_load_command_exists(self):
        """Test that the load command exists."""
        assert load_app


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

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_address_group)

        # Invoke the command
        result = runner.invoke(
            test_app,
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
                "--tags",
                "test",
                "--tags",
                "example",
            ],
        )

        assert result.exit_code == 0
        assert "Created address group" in result.stdout
        assert "test-group" in result.stdout
        assert "test-folder" in result.stdout

    def test_set_address_group_error(self, runner, monkeypatch):
        """Test the set address group command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_address_group", mock_create_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_address_group)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-group",
                "--type",
                "static",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating address group" in result.stdout
        assert "Test error" in result.stdout

    def test_delete_address_group_command(self, runner, monkeypatch):
        """Test the delete address group command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_address_group", mock_delete)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_address_group)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-group",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted address group" in result.stdout
        assert "test-group" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_address_group_error(self, runner, monkeypatch):
        """Test the delete address group command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_address_group", mock_delete_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_address_group)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-group",
            ],
        )

        assert result.exit_code == 1
        assert "Error deleting address group" in result.stdout
        assert "Test error" in result.stdout

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

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_address_group)

        # Invoke the command
        result = runner.invoke(test_app, ["--file", str(mock_address_groups_yaml_file)])

        assert result.exit_code == 0
        assert "Applied address group" in result.stdout
        assert "test-group" in result.stdout
        assert "test-folder" in result.stdout
        assert len(created_groups) == 1

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

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_address_group)

        # Invoke the command with dry-run
        result = runner.invoke(test_app, ["--file", str(mock_address_groups_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called  # Ensure the create method was not called

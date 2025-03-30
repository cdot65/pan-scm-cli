"""Tests for the network commands module."""

import typer
from scm_cli.commands.network import delete_app, delete_zone, load_app, load_zone, set_app, set_zone


class TestNetworkCommands:
    """Test the network commands."""

    def test_set_command_exists(self):
        """Test that the set command exists."""
        assert set_app

    def test_delete_command_exists(self):
        """Test that the delete command exists."""
        assert delete_app

    def test_load_command_exists(self):
        """Test that the load command exists."""
        assert load_app


class TestZoneCommands:
    """Test the zone commands."""

    def test_set_zone_command(self, runner, monkeypatch):
        """Test the set zone command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "zone-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "mode": kwargs.get("mode"),
                "interfaces": kwargs.get("interfaces", []),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }

        monkeypatch.setattr(scm_client, "create_zone", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_zone)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-zone",
                "--mode",
                "L3",
                "--interfaces",
                "ethernet1/1",
                "--interfaces",
                "ethernet1/2",
                "--description",
                "Test zone",
                "--tags",
                "test",
                "--tags",
                "example",
            ],
        )

        assert result.exit_code == 0
        assert "Created zone" in result.stdout
        assert "test-zone" in result.stdout
        assert "test-folder" in result.stdout

    def test_set_zone_error(self, runner, monkeypatch):
        """Test the set zone command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_zone", mock_create_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_zone)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-zone",
                "--mode",
                "L3",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating security zone" in result.stdout
        assert "Test error" in result.stdout

    def test_delete_zone_command(self, runner, monkeypatch):
        """Test the delete zone command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_zone", mock_delete)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_zone)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-zone",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted zone" in result.stdout
        assert "test-zone" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_zone_error(self, runner, monkeypatch):
        """Test the delete zone command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_zone", mock_delete_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_zone)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-zone",
            ],
        )

        assert result.exit_code == 1
        assert "Error deleting security zone" in result.stdout
        assert "Test error" in result.stdout

    def test_load_zone_command(self, runner, monkeypatch, mock_zones_yaml_file):
        """Test the load zone command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        created_zones = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"zone-{len(created_zones) + 1}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "mode": kwargs.get("mode"),
                "interfaces": kwargs.get("interfaces", []),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }
            created_zones.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_zone", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_zone)

        # Invoke the command
        result = runner.invoke(test_app, ["--file", str(mock_zones_yaml_file)])

        assert result.exit_code == 0
        assert "Applied zone" in result.stdout
        assert "test-zone" in result.stdout
        assert "test-folder" in result.stdout
        assert len(created_zones) == 1

    def test_load_zone_dry_run(self, runner, monkeypatch, mock_zones_yaml_file):
        """Test the load zone command with dry-run option."""
        # Mock the SCM client method to track if it gets called
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_zone", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_zone)

        # Invoke the command with dry-run
        result = runner.invoke(test_app, ["--file", str(mock_zones_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called  # Ensure the create method was not called

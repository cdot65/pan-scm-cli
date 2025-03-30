"""Tests for the network commands module."""

import typer
from scm_cli.commands.network import delete_command, delete_zone, load_command, load_zone, set_command, set_zone


class TestNetworkCommands:
    """Test the network commands."""

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

        # Invoke the command
        result = runner.invoke(
            set_zone,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-zone",
                "--mode",
                "L3",
                "--interface",
                "ethernet1/1",
                "--interface",
                "ethernet1/2",
                "--description",
                "Test zone",
                "--tag",
                "test",
                "--tag",
                "example",
            ],
        )

        assert result.exit_code == 0
        assert "Created zone" in result.stdout
        assert "ID: zone-12345" in result.stdout
        assert "Name: test-zone" in result.stdout
        assert "Folder: test-folder" in result.stdout
        assert "Mode: L3" in result.stdout
        assert "Interfaces: " in result.stdout
        assert "ethernet1/1" in result.stdout
        assert "ethernet1/2" in result.stdout
        assert "Description: Test zone" in result.stdout
        assert "Tags: " in result.stdout
        assert "test" in result.stdout
        assert "example" in result.stdout

    def test_set_zone_error(self, runner, monkeypatch):
        """Test the set zone command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr(scm_client, "create_zone", mock_create_error)

        # Invoke the command
        result = runner.invoke(set_zone, ["--folder", "test-folder", "--name", "test-zone", "--mode", "L3"])

        assert result.exit_code == 1
        assert "Error creating zone" in result.stdout
        assert "API Error" in result.stdout

    def test_delete_zone_command(self, runner, monkeypatch):
        """Test the delete zone command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_zone", mock_delete)

        # Invoke the command
        result = runner.invoke(delete_zone, ["--folder", "test-folder", "--name", "test-zone"])

        assert result.exit_code == 0
        assert "Deleted zone" in result.stdout
        assert "test-zone" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_zone_error(self, runner, monkeypatch):
        """Test the delete zone command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr(scm_client, "delete_zone", mock_delete_error)

        # Invoke the command
        result = runner.invoke(delete_zone, ["--folder", "test-folder", "--name", "test-zone"])

        assert result.exit_code == 1
        assert "Error deleting zone" in result.stdout
        assert "API Error" in result.stdout

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

        # Invoke the command
        result = runner.invoke(load_zone, ["--file", str(mock_zones_yaml_file)])

        assert result.exit_code == 0
        assert "Loaded 1 zone(s)" in result.stdout
        assert len(created_zones) == 1
        assert created_zones[0]["name"] == "test-zone"
        assert created_zones[0]["folder"] == "test-folder"
        assert created_zones[0]["mode"] == "L3"
        assert "ethernet1/1" in created_zones[0]["interfaces"]

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

        # Invoke the command with dry-run
        result = runner.invoke(load_zone, ["--file", str(mock_zones_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout
        assert "Would create zone" in result.stdout
        assert "test-zone" in result.stdout
        assert not mock_called  # Ensure the mock wasn't called due to dry-run

    def test_load_zone_error(self, runner, monkeypatch, mock_zones_yaml_file):
        """Test the load zone command with an error."""
        # Mock the config loader to simulate an error
        from scm_cli.utils import config

        def mock_load_error(*args, **kwargs):
            raise ValueError("Invalid file format")

        monkeypatch.setattr(config, "load_from_yaml", mock_load_error)

        # Invoke the command
        result = runner.invoke(load_zone, ["--file", str(mock_zones_yaml_file)])

        assert result.exit_code == 1
        assert "Error loading zones" in result.stdout
        assert "Invalid file format" in result.stdout

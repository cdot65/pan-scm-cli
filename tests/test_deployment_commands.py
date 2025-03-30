"""Tests for the deployment commands module."""

import typer
from scm_cli.commands.deployment import (
    delete_bandwidth_allocation,
    delete_command,
    load_bandwidth_allocation,
    load_command,
    set_bandwidth_allocation,
    set_command,
)


class TestDeploymentCommands:
    """Test the deployment commands."""

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


class TestBandwidthAllocationCommands:
    """Test the bandwidth allocation commands."""

    def test_set_bandwidth_allocation_command(self, runner, monkeypatch):
        """Test the set bandwidth allocation command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "ba-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "bandwidth": kwargs.get("bandwidth"),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create)

        # Invoke the command
        result = runner.invoke(
            set_bandwidth_allocation,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-allocation",
                "--bandwidth",
                "1000",
                "--description",
                "Test allocation",
                "--tag",
                "test",
                "--tag",
                "example",
            ],
        )

        assert result.exit_code == 0
        assert "Created bandwidth allocation" in result.stdout
        assert "ID: ba-12345" in result.stdout
        assert "Name: test-allocation" in result.stdout
        assert "Folder: test-folder" in result.stdout
        assert "Bandwidth: 1000" in result.stdout
        assert "Description: Test allocation" in result.stdout
        assert "Tags: " in result.stdout
        assert "test" in result.stdout
        assert "example" in result.stdout

    def test_set_bandwidth_allocation_error(self, runner, monkeypatch):
        """Test the set bandwidth allocation command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create_error)

        # Invoke the command
        result = runner.invoke(
            set_bandwidth_allocation, ["--folder", "test-folder", "--name", "test-allocation", "--bandwidth", "1000"]
        )

        assert result.exit_code == 1
        assert "Error creating bandwidth allocation" in result.stdout
        assert "API Error" in result.stdout

    def test_delete_bandwidth_allocation_command(self, runner, monkeypatch):
        """Test the delete bandwidth allocation command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_bandwidth_allocation", mock_delete)

        # Invoke the command
        result = runner.invoke(delete_bandwidth_allocation, ["--folder", "test-folder", "--name", "test-allocation"])

        assert result.exit_code == 0
        assert "Deleted bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_bandwidth_allocation_error(self, runner, monkeypatch):
        """Test the delete bandwidth allocation command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr(scm_client, "delete_bandwidth_allocation", mock_delete_error)

        # Invoke the command
        result = runner.invoke(delete_bandwidth_allocation, ["--folder", "test-folder", "--name", "test-allocation"])

        assert result.exit_code == 1
        assert "Error deleting bandwidth allocation" in result.stdout
        assert "API Error" in result.stdout

    def test_load_bandwidth_allocation_command(self, runner, monkeypatch, mock_yaml_file):
        """Test the load bandwidth allocation command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        created_allocations = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"ba-{len(created_allocations) + 1}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "bandwidth": kwargs.get("bandwidth"),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }
            created_allocations.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create)

        # Invoke the command
        result = runner.invoke(load_bandwidth_allocation, ["--file", str(mock_yaml_file)])

        assert result.exit_code == 0
        assert "Loaded 1 bandwidth allocation(s)" in result.stdout
        assert len(created_allocations) == 1
        assert created_allocations[0]["name"] == "test-allocation"
        assert created_allocations[0]["folder"] == "test-folder"
        assert created_allocations[0]["bandwidth"] == 1000

    def test_load_bandwidth_allocation_dry_run(self, runner, monkeypatch, mock_yaml_file):
        """Test the load bandwidth allocation command with dry-run option."""
        # Mock the SCM client method to track if it gets called
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create)

        # Invoke the command with dry-run
        result = runner.invoke(load_bandwidth_allocation, ["--file", str(mock_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout
        assert "Would create bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout
        assert not mock_called  # Ensure the mock wasn't called due to dry-run

    def test_load_bandwidth_allocation_error(self, runner, monkeypatch, mock_yaml_file):
        """Test the load bandwidth allocation command with an error."""
        # Mock the config loader to simulate an error
        from scm_cli.utils import config

        def mock_load_error(*args, **kwargs):
            raise ValueError("Invalid file format")

        monkeypatch.setattr(config, "load_from_yaml", mock_load_error)

        # Invoke the command
        result = runner.invoke(load_bandwidth_allocation, ["--file", str(mock_yaml_file)])

        assert result.exit_code == 1
        assert "Error loading bandwidth allocations" in result.stdout
        assert "Invalid file format" in result.stdout

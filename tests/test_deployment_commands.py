"""Tests for the deployment commands module."""

import typer
from scm_cli.commands.deployment import (
    delete_app,
    delete_bandwidth_allocation,
    load_app,
    load_bandwidth_allocation,
    set_app,
    set_bandwidth_allocation,
)


class TestDeploymentCommands:
    """Test the deployment commands."""

    def test_set_command_exists(self):
        """Test that the set command exists."""
        assert set_app

    def test_delete_command_exists(self):
        """Test that the delete command exists."""
        assert delete_app

    def test_load_command_exists(self):
        """Test that the load command exists."""
        assert load_app


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

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-allocation",
                "--bandwidth",
                "1000",
                "--description",
                "Test allocation",
                "--tags",
                "test",
                "--tags",
                "example",
            ],
        )

        assert result.exit_code == 0
        assert "Created bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout
        assert "test-folder" in result.stdout
        assert "1000" in result.stdout

    def test_set_bandwidth_allocation_error(self, runner, monkeypatch):
        """Test the set bandwidth allocation command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-allocation",
                "--bandwidth",
                "1000",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating bandwidth allocation" in result.stdout
        assert "Test error" in result.stdout

    def test_delete_bandwidth_allocation_command(self, runner, monkeypatch):
        """Test the delete bandwidth allocation command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_bandwidth_allocation", mock_delete)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-allocation",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_bandwidth_allocation_error(self, runner, monkeypatch):
        """Test the delete bandwidth allocation command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_bandwidth_allocation", mock_delete_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-allocation",
            ],
        )

        assert result.exit_code == 1
        assert "Error deleting bandwidth allocation" in result.stdout
        assert "Test error" in result.stdout

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

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(test_app, ["--file", str(mock_yaml_file)])

        assert result.exit_code == 0
        assert "Applied bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout
        assert "test-folder" in result.stdout
        assert "1000" in result.stdout
        assert "Loaded 1 bandwidth allocation(s)" in result.stdout
        assert len(created_allocations) == 1

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

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_bandwidth_allocation)

        # Invoke the command with dry-run
        result = runner.invoke(test_app, ["--file", str(mock_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout
        assert "Would create bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout
        assert not mock_called  # Ensure the create method was not called

    def test_load_bandwidth_allocation_error(self, runner, monkeypatch, mock_yaml_file):
        """Test the load bandwidth allocation command with an error."""
        # Import the module directly to get access to its functions
        import scm_cli.commands.deployment as deployment_module
        from scm_cli.utils import config

        # Create a direct mock for load_from_yaml that will be used in the test
        original_load_from_yaml = config.load_from_yaml

        def mock_load_error(*args, **kwargs):
            raise ValueError("YAML parsing error")

        # Apply the mock directly to the imported module
        monkeypatch.setattr(deployment_module, "load_from_yaml", mock_load_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(test_app, ["--file", str(mock_yaml_file)])

        # Restore original function after test
        monkeypatch.setattr(deployment_module, "load_from_yaml", original_load_from_yaml)

        assert result.exit_code == 1
        assert "Error loading bandwidth allocations" in result.stdout
        assert "YAML parsing error" in result.stdout

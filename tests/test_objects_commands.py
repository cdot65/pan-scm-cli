"""Tests for the objects commands module."""

import typer
from scm_cli.commands.objects import (
    delete_address_group,
    delete_app,
    load_address_group,
    load_app,
    set_address_group,
    set_app,
    show_app,
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

    def test_show_command_exists(self):
        """Test that the show command exists."""
        assert show_app


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


class TestShowAddressCommands:
    """Test the show address commands."""

    def test_show_address_list(self, runner, monkeypatch):
        """Test the show address command with --list flag."""
        from scm_cli.commands.objects import show_address, show_app
        from scm_cli.utils.sdk_client import scm_client

        # Mock the list_addresses method to return sample data
        def mock_list_addresses(*args, **kwargs):
            return [
                {
                    "name": "test-address-1",
                    "description": "Test address 1",
                    "ip_netmask": "192.168.1.0/24",
                    "folder": "Shared",
                    "tag": ["test", "network"]
                },
                {
                    "name": "test-address-2",
                    "description": "Test address 2",
                    "fqdn": "example.com",
                    "folder": "Shared"
                }
            ]

        monkeypatch.setattr(scm_client, "list_addresses", mock_list_addresses)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(show_address)

        result = runner.invoke(test_app, ["--folder", "Shared", "--list"])

        assert result.exit_code == 0
        assert "Addresses in folder 'Shared':" in result.stdout
        assert "test-address-1" in result.stdout
        assert "192.168.1.0/24" in result.stdout
        assert "test-address-2" in result.stdout
        assert "example.com" in result.stdout

    def test_show_address_by_name(self, runner, monkeypatch):
        """Test the show address command with --name flag."""
        from scm_cli.commands.objects import show_address
        from scm_cli.utils.sdk_client import scm_client

        # Mock the get_address method to return sample data
        def mock_get_address(*args, **kwargs):
            return {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "webserver",
                "description": "Production web server",
                "ip_netmask": "10.0.1.100/32",
                "folder": "Shared",
                "tag": ["production", "web"]
            }

        monkeypatch.setattr(scm_client, "get_address", mock_get_address)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(show_address)

        result = runner.invoke(test_app, ["--folder", "Shared", "--name", "webserver"])

        assert result.exit_code == 0
        assert "Address: webserver" in result.stdout
        assert "Folder: Shared" in result.stdout
        assert "Description: Production web server" in result.stdout
        assert "Type: IP/Netmask" in result.stdout
        assert "Value: 10.0.1.100/32" in result.stdout
        assert "Tags: production, web" in result.stdout
        assert "ID: 123e4567-e89b-12d3-a456-426614174000" in result.stdout

    def test_show_address_no_options(self, runner, monkeypatch):
        """Test the show address command without --list or --name flags."""
        from scm_cli.commands.objects import show_address

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(show_address)

        result = runner.invoke(test_app, ["--folder", "Shared"])

        assert result.exit_code == 1
        assert "Error: Either --list or --name must be specified" in result.stdout

    def test_show_address_empty_list(self, runner, monkeypatch):
        """Test the show address command with --list flag when no addresses exist."""
        from scm_cli.commands.objects import show_address
        from scm_cli.utils.sdk_client import scm_client

        # Mock the list_addresses method to return empty list
        def mock_list_addresses(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_addresses", mock_list_addresses)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(show_address)

        result = runner.invoke(test_app, ["--folder", "Shared", "--list"])

        assert result.exit_code == 0
        assert "No addresses found in folder 'Shared'" in result.stdout


class TestShowAddressGroupCommands:
    """Test the show address-group commands."""

    def test_show_address_group_list(self, runner, monkeypatch):
        """Test the show address-group command with --list flag."""
        from scm_cli.commands.objects import show_address_group
        from scm_cli.utils.sdk_client import scm_client

        # Mock the list_address_groups method to return sample data
        def mock_list_address_groups(*args, **kwargs):
            return [
                {
                    "name": "web-servers",
                    "description": "Web server address group",
                    "type": "static",
                    "members": ["192.168.1.10", "192.168.1.11", "192.168.1.12"],
                    "folder": "Shared",
                    "tag": ["web", "production"]
                },
                {
                    "name": "dynamic-endpoints",
                    "description": "Dynamic endpoint group",
                    "type": "dynamic",
                    "filter": "'endpoint' and 'corporate'",
                    "folder": "Shared",
                    "tag": ["dynamic"]
                }
            ]

        monkeypatch.setattr(scm_client, "list_address_groups", mock_list_address_groups)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared", "--list"])

        assert result.exit_code == 0
        assert "Address Groups in folder 'Shared':" in result.stdout
        assert "web-servers" in result.stdout
        assert "static" in result.stdout
        assert "192.168.1.10" in result.stdout
        assert "dynamic-endpoints" in result.stdout
        assert "dynamic" in result.stdout
        assert "'endpoint' and 'corporate'" in result.stdout

    def test_show_address_group_by_name_static(self, runner, monkeypatch):
        """Test the show address-group command with --name flag for static group."""
        from scm_cli.commands.objects import show_address_group
        from scm_cli.utils.sdk_client import scm_client

        # Mock the get_address_group method to return sample data
        def mock_get_address_group(*args, **kwargs):
            return {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "web-servers",
                "description": "Production web servers",
                "type": "static",
                "members": ["web-1", "web-2", "web-3"],
                "folder": "Shared",
                "tag": ["production", "web"]
            }

        monkeypatch.setattr(scm_client, "get_address_group", mock_get_address_group)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared", "--name", "web-servers"])

        assert result.exit_code == 0
        assert "Address Group: web-servers" in result.stdout
        assert "Folder: Shared" in result.stdout
        assert "Type: static" in result.stdout
        assert "Description: Production web servers" in result.stdout
        assert "Members (3):" in result.stdout
        assert "- web-1" in result.stdout
        assert "- web-2" in result.stdout
        assert "- web-3" in result.stdout
        assert "Tags: production, web" in result.stdout
        assert "ID: 123e4567-e89b-12d3-a456-426614174001" in result.stdout

    def test_show_address_group_by_name_dynamic(self, runner, monkeypatch):
        """Test the show address-group command with --name flag for dynamic group."""
        from scm_cli.commands.objects import show_address_group
        from scm_cli.utils.sdk_client import scm_client

        # Mock the get_address_group method to return sample data
        def mock_get_address_group(*args, **kwargs):
            return {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "name": "dynamic-endpoints",
                "description": "Dynamic endpoint group",
                "type": "dynamic",
                "filter": "'endpoint' and 'corporate'",
                "folder": "Shared",
                "tag": ["dynamic", "auto"]
            }

        monkeypatch.setattr(scm_client, "get_address_group", mock_get_address_group)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared", "--name", "dynamic-endpoints"])

        assert result.exit_code == 0
        assert "Address Group: dynamic-endpoints" in result.stdout
        assert "Type: dynamic" in result.stdout
        assert "Filter: 'endpoint' and 'corporate'" in result.stdout
        assert "Tags: dynamic, auto" in result.stdout

    def test_show_address_group_no_options(self, runner, monkeypatch):
        """Test the show address-group command without --list or --name flags."""
        from scm_cli.commands.objects import show_address_group

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared"])

        assert result.exit_code == 1
        assert "Error: Either --list or --name must be specified" in result.stdout

    def test_show_address_group_empty_list(self, runner, monkeypatch):
        """Test the show address-group command with --list flag when no groups exist."""
        from scm_cli.commands.objects import show_address_group
        from scm_cli.utils.sdk_client import scm_client

        # Mock the list_address_groups method to return empty list
        def mock_list_address_groups(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_address_groups", mock_list_address_groups)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared", "--list"])

        assert result.exit_code == 0
        assert "No address groups found in folder 'Shared'" in result.stdout

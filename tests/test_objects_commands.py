"""Tests for the objects commands module."""

import typer

from scm_cli.commands.objects import (
    delete_address_group,
    delete_app,
    delete_quarantined_device,
    delete_region,
    delete_schedule,
    load_address_group,
    load_app,
    load_quarantined_device,
    load_region,
    set_address_group,
    set_app,
    set_quarantined_device,
    set_region,
    set_schedule,
    show_app,
    show_quarantined_device,
    show_region,
    show_schedule,
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
        from scm_cli.commands.objects import show_address
        from scm_cli.utils.sdk_client import scm_client

        # Mock the list_addresses method to return sample data
        def mock_list_addresses(*args, **kwargs):
            return [
                {"name": "test-address-1", "description": "Test address 1", "ip_netmask": "192.168.1.0/24", "folder": "Shared", "tag": ["test", "network"]},
                {"name": "test-address-2", "description": "Test address 2", "fqdn": "example.com", "folder": "Shared"},
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
                "tag": ["production", "web"],
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
                    "tag": ["web", "production"],
                },
                {"name": "dynamic-endpoints", "description": "Dynamic endpoint group", "type": "dynamic", "filter": "'endpoint' and 'corporate'", "folder": "Shared", "tag": ["dynamic"]},
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
                "tag": ["production", "web"],
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
                "tag": ["dynamic", "auto"],
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


class TestScheduleCommands:
    """Test the schedule commands."""

    def test_set_schedule_command(self, runner, monkeypatch):
        """Test the set schedule command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "sched-12345",
                "name": "business-hours",
                "folder": "Texas",
                "schedule_type": {"recurring": {"daily": ["09:00-17:00"]}},
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_schedule", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_schedule)
class TestRegionCommands:
    """Test the region commands."""

    def test_set_region_command(self, runner, monkeypatch):
        """Test the set region command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(region_data):
            result = {**region_data, "__action__": "created"}
            return result

        monkeypatch.setattr(scm_client, "create_region", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_region)

        result = runner.invoke(
            test_app,
            [
                "business-hours",
                "--schedule-type",
                "recurring-daily",
                "--time-range",
                "09:00-17:00",
                "--folder",
                "Texas",
                "US-South",
                "--folder",
                "Texas",
                "--latitude",
                "30.2672",
                "--longitude",
                "-97.7431",
                "--address",
                "10.0.0.0/8",
            ],
        )

        assert result.exit_code == 0
        assert "Created schedule" in result.stdout
        assert "business-hours" in result.stdout

    def test_set_schedule_error(self, runner, monkeypatch):
        """Test the set schedule command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_schedule", mock_create_error)

        test_app = typer.Typer()
        test_app.command()(set_schedule)
        assert "Created region" in result.stdout
        assert "US-South" in result.stdout

    def test_set_region_error(self, runner, monkeypatch):
        """Test the set region command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(region_data):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_region", mock_create_error)

        test_app = typer.Typer()
        test_app.command()(set_region)

        result = runner.invoke(
            test_app,
            [
                "bad-sched",
                "--schedule-type",
                "recurring-daily",
                "--time-range",
                "09:00-17:00",
                "US-South",
                "--folder",
                "Texas",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating/updating schedule" in result.stdout

    def test_show_schedule_list(self, runner, monkeypatch):
        """Test the show schedule command listing all."""
        assert "Error creating/updating region" in result.stdout

    def test_delete_region_command(self, runner, monkeypatch):
        """Test the delete region command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {"id": "region-123", "name": "US-South", "folder": "Texas"}

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "get_region", mock_get)
        monkeypatch.setattr(scm_client, "delete_region", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_region)

        result = runner.invoke(
            test_app,
            [
                "US-South",
                "--folder",
                "Texas",
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted region" in result.stdout
        assert "US-South" in result.stdout

    def test_show_region_list(self, runner, monkeypatch):
        """Test the show region command listing all regions."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "name": "BusinessHours",
                    "folder": "Texas",
                    "schedule_type": {"recurring": {"daily": ["09:00-17:00"]}},
                },
            ]

        monkeypatch.setattr(scm_client, "list_schedules", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_schedule)
                    "name": "US-South",
                    "folder": "Texas",
                    "geo_location": {"latitude": 30.2672, "longitude": -97.7431},
                    "address": ["10.0.0.0/8"],
                },
                {
                    "name": "US-East",
                    "folder": "Texas",
                    "geo_location": {"latitude": 40.7128, "longitude": -74.006},
                },
            ]

        monkeypatch.setattr(scm_client, "list_regions", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_region)

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "BusinessHours" in result.stdout
        assert "Total: 1 schedules" in result.stdout

    def test_show_schedule_by_name(self, runner, monkeypatch):
        """Test the show schedule command by name."""
        assert "US-South" in result.stdout
        assert "US-East" in result.stdout
        assert "Total: 2 regions" in result.stdout

    def test_show_region_by_name(self, runner, monkeypatch):
        """Test the show region command with --name flag."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "sched-123",
                "name": "BusinessHours",
                "folder": "Texas",
                "schedule_type": {"recurring": {"daily": ["09:00-17:00"]}},
            }

        monkeypatch.setattr(scm_client, "get_schedule", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_schedule)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "BusinessHours"])

        assert result.exit_code == 0
        assert "Schedule: BusinessHours" in result.stdout
        assert "Recurring Daily" in result.stdout
        assert "09:00-17:00" in result.stdout

    def test_delete_schedule_command(self, runner, monkeypatch):
        """Test the delete schedule command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {"id": "sched-123", "name": "old-sched", "folder": "Texas"}

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "get_schedule", mock_get)
        monkeypatch.setattr(scm_client, "delete_schedule", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_schedule)

        result = runner.invoke(test_app, ["old-sched", "--folder", "Texas", "--force"])

        assert result.exit_code == 0
        assert "Deleted schedule" in result.stdout
        assert "old-sched" in result.stdout
                "id": "region-123",
                "name": "US-South",
                "folder": "Texas",
                "geo_location": {"latitude": 30.2672, "longitude": -97.7431},
                "address": ["10.0.0.0/8", "192.168.1.0/24"],
            }

        monkeypatch.setattr(scm_client, "get_region", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_region)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "US-South"])

        assert result.exit_code == 0
        assert "Region: US-South" in result.stdout
        assert "Latitude: 30.2672" in result.stdout
        assert "Longitude: -97.7431" in result.stdout
        assert "10.0.0.0/8" in result.stdout

    def test_show_region_empty_list(self, runner, monkeypatch):
        """Test the show region command when no regions exist."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_regions", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_region)

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "No regions found" in result.stdout

    def test_load_region_command(self, runner, monkeypatch, tmp_path):
        """Test the load region command."""
        from scm_cli.utils.sdk_client import scm_client

        # Create a test YAML file
        yaml_content = """
regions:
  - name: US-South
    folder: Texas
    latitude: 30.2672
    longitude: -97.7431
    addresses:
      - 10.0.0.0/8
"""
        test_file = tmp_path / "test_regions.yml"
        test_file.write_text(yaml_content)

        def mock_create(region_data):
            return {**region_data, "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_region", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_region)
class TestQuarantinedDeviceCommands:
    """Test the quarantined device commands."""

    def test_set_quarantined_device_command(self, runner, monkeypatch):
        """Test the set quarantined-device command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(device_data):
            return device_data

        monkeypatch.setattr(scm_client, "create_quarantined_device", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_quarantined_device)

        result = runner.invoke(test_app, ["host-123", "--serial-number", "SN-456"])

        assert result.exit_code == 0
        assert "Created quarantined device: host-123" in result.stdout

    def test_set_quarantined_device_no_serial(self, runner, monkeypatch):
        """Test the set quarantined-device command without serial number."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(device_data):
            return device_data

        monkeypatch.setattr(scm_client, "create_quarantined_device", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_quarantined_device)

        result = runner.invoke(test_app, ["host-789"])

        assert result.exit_code == 0
        assert "Created quarantined device: host-789" in result.stdout

    def test_delete_quarantined_device_command(self, runner, monkeypatch):
        """Test the delete quarantined-device command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(host_id):
            pass

        monkeypatch.setattr(scm_client, "delete_quarantined_device", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_quarantined_device)

        result = runner.invoke(test_app, ["host-123"])

        assert result.exit_code == 0
        assert "Deleted quarantined device: host-123" in result.stdout

    def test_show_quarantined_device_list(self, runner, monkeypatch):
        """Test the show quarantined-device command listing all devices."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(host_id=None, serial_number=None):
            return [
                {"host_id": "host-001", "serial_number": "SN-001"},
                {"host_id": "host-002", "serial_number": "SN-002"},
            ]

        monkeypatch.setattr(scm_client, "list_quarantined_devices", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_quarantined_device)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "Host ID: host-001" in result.stdout
        assert "Serial Number: SN-001" in result.stdout
        assert "Host ID: host-002" in result.stdout
        assert "Total: 2 quarantined devices" in result.stdout

    def test_show_quarantined_device_empty(self, runner, monkeypatch):
        """Test the show quarantined-device command when no devices found."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(host_id=None, serial_number=None):
            return []

        monkeypatch.setattr(scm_client, "list_quarantined_devices", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_quarantined_device)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "No quarantined devices found" in result.stdout

    def test_load_quarantined_device_command(self, runner, monkeypatch, tmp_path):
        """Test the load quarantined-device command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(device_data):
            return device_data

        monkeypatch.setattr(scm_client, "create_quarantined_device", mock_create)

        # Create test YAML file
        yaml_content = """
quarantined_devices:
  - host_id: host-001
    serial_number: SN-001
  - host_id: host-002
"""
        test_file = tmp_path / "quarantined_devices.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_quarantined_device)

        result = runner.invoke(test_app, ["--file", str(test_file)])

        assert result.exit_code == 0
        assert "Created region" in result.stdout
        assert "US-South" in result.stdout
        assert "Created quarantined device: host-001" in result.stdout
        assert "Created quarantined device: host-002" in result.stdout
        assert "Processed 2 quarantined devices" in result.stdout

    def test_load_quarantined_device_file_not_found(self, runner):
        """Test the load quarantined-device command with missing file."""
        test_app = typer.Typer()
        test_app.command()(load_quarantined_device)

        result = runner.invoke(test_app, ["--file", "/nonexistent/file.yml"])

        assert result.exit_code == 1
        assert "File not found" in result.stdout

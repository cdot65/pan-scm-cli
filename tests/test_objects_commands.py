"""Tests for the objects commands module."""

import typer

from scm_cli.commands.objects import (  # noqa: F401
    backup_auto_tag_action,
    delete_address_group,
    delete_app,
    delete_auto_tag_action,
    delete_quarantined_device,
    delete_region,
    delete_schedule,
    load_address_group,
    load_app,
    load_auto_tag_action,
    load_quarantined_device,
    load_region,
    set_address_group,
    set_app,
    set_application_filter,
    set_auto_tag_action,
    set_external_dynamic_list,
    set_hip_object,
    set_hip_profile,
    set_http_server_profile,
    set_log_forwarding_profile,
    set_quarantined_device,
    set_region,
    set_schedule,
    set_service_group,
    set_syslog_server_profile,
    show_app,
    show_auto_tag_action,
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

        test_app = typer.Typer()
        test_app.command()(set_address_group)

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
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_address_group", mock_create_error)

        test_app = typer.Typer()
        test_app.command()(set_address_group)

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
                "--description",
                "Test address group",
            ],
        )

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_delete_address_group_command(self, runner, monkeypatch):
        """Test the delete address group command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_address_group", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_address_group)

        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "test-group", "--force"])

        assert result.exit_code == 0
        assert "Deleted address group: test-group" in result.stdout

    def test_delete_address_group_error(self, runner, monkeypatch):
        """Test the delete address group command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_address_group", mock_delete_error)

        test_app = typer.Typer()
        test_app.command()(delete_address_group)

        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "test-group", "--force"])

        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_load_address_group_command(self, runner, monkeypatch, mock_address_groups_yaml_file):
        """Test the load address group command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "ag-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "type": kwargs.get("type"),
                "created": True,
            }

        monkeypatch.setattr(scm_client, "create_address_group", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_address_group)

        result = runner.invoke(test_app, ["--file", str(mock_address_groups_yaml_file)])

        assert result.exit_code == 0
        assert "Successfully processed" in result.stdout
        assert "1 address group" in result.stdout

    def test_show_address_group_list(self, runner, monkeypatch):
        """Test the show address-group command listing all groups (default behavior)."""
        from scm_cli.commands.objects import show_address_group
        from scm_cli.utils.sdk_client import scm_client

        def mock_list_address_groups(*args, **kwargs):
            return [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "test-group",
                    "description": "Test group",
                    "static": ["192.168.1.0/24"],
                    "folder": "Shared",
                },
                {
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                    "name": "test-group-2",
                    "description": "Second test group",
                    "dynamic": {"filter": "'tag1' or 'tag2'"},
                    "folder": "Shared",
                },
            ]

        monkeypatch.setattr(scm_client, "list_address_groups", mock_list_address_groups)

        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared"])

        assert result.exit_code == 0
        assert "test-group" in result.stdout
        assert "test-group-2" in result.stdout

    def test_show_address_group_by_name(self, runner, monkeypatch):
        """Test the show address-group command with --name flag."""
        from scm_cli.commands.objects import show_address_group
        from scm_cli.utils.sdk_client import scm_client

        def mock_get_address_group(*args, **kwargs):
            return {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "test-group",
                "description": "Test group",
                "static": ["192.168.1.0/24", "10.0.0.0/8"],
                "folder": "Shared",
                "tag": ["production", "webservers"],
            }

        monkeypatch.setattr(scm_client, "get_address_group", mock_get_address_group)

        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared", "--name", "test-group"])

        assert result.exit_code == 0
        assert "Address Group: test-group" in result.stdout
        assert "Type: static" in result.stdout
        assert "192.168.1.0/24" in result.stdout
        assert "Tags: production, webservers" in result.stdout

    def test_show_address_group_dynamic_by_name(self, runner, monkeypatch):
        """Test the show address-group command with --name flag for dynamic group."""
        from scm_cli.commands.objects import show_address_group
        from scm_cli.utils.sdk_client import scm_client

        def mock_get_address_group(*args, **kwargs):
            return {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "name": "dynamic-endpoints",
                "description": "Dynamic endpoint group",
                "dynamic": {"filter": "'endpoint' and 'corporate'"},
                "folder": "Shared",
                "tag": ["dynamic", "auto"],
            }

        monkeypatch.setattr(scm_client, "get_address_group", mock_get_address_group)

        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared", "--name", "dynamic-endpoints"])

        assert result.exit_code == 0
        assert "Address Group: dynamic-endpoints" in result.stdout
        assert "Type: dynamic" in result.stdout
        assert "Filter: 'endpoint' and 'corporate'" in result.stdout
        assert "Tags: dynamic, auto" in result.stdout

    def test_show_address_group_no_options(self, runner, monkeypatch):
        """Test the show address-group command without --name defaults to listing all."""
        from scm_cli.commands.objects import show_address_group
        from scm_cli.utils.sdk_client import scm_client

        def mock_list_address_groups(*args, **kwargs):
            return [
                {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "test-group",
                    "static": ["192.168.1.0/24"],
                    "folder": "Shared",
                },
            ]

        monkeypatch.setattr(scm_client, "list_address_groups", mock_list_address_groups)

        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared"])

        assert result.exit_code == 0
        assert "test-group" in result.stdout

    def test_show_address_group_empty_list(self, runner, monkeypatch):
        """Test the show address-group command when no groups exist."""
        from scm_cli.commands.objects import show_address_group
        from scm_cli.utils.sdk_client import scm_client

        def mock_list_address_groups(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_address_groups", mock_list_address_groups)

        test_app = typer.Typer()
        test_app.command()(show_address_group)

        result = runner.invoke(test_app, ["--folder", "Shared"])

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

        result = runner.invoke(
            test_app,
            [
                "bad-sched",
                "--schedule-type",
                "recurring-daily",
                "--time-range",
                "09:00-17:00",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating/updating schedule" in result.stdout

    def test_show_schedule_list(self, runner, monkeypatch):
        """Test the show schedule command listing all."""
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

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "BusinessHours" in result.stdout
        assert "Total: 1 schedules" in result.stdout

    def test_show_schedule_by_name(self, runner, monkeypatch):
        """Test the show schedule command by name."""
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
                "US-South",
                "--folder",
                "Texas",
            ],
        )

        assert result.exit_code == 1
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
        assert "US-South" in result.stdout
        assert "US-East" in result.stdout
        assert "Total: 2 regions" in result.stdout

    def test_show_region_by_name(self, runner, monkeypatch):
        """Test the show region command with --name flag."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
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

        result = runner.invoke(test_app, ["--file", str(test_file)])

        assert result.exit_code == 0
        assert "Created region" in result.stdout
        assert "US-South" in result.stdout


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

        result = runner.invoke(test_app, ["host-123", "--force"])

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


class TestAutoTagActionCommands:
    """Test the auto tag action commands."""

    def test_set_auto_tag_action_command(self, runner, monkeypatch):
        """Test the set auto-tag-action command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            data = args[0] if args else kwargs
            return {
                "id": "ata-test",
                "name": data.get("name", "test"),
                "folder": data.get("folder", "Texas"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_auto_tag_action", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_auto_tag_action)

        result = runner.invoke(
            test_app,
            [
                "test-action",
                "--folder",
                "Texas",
                "--description",
                "Test action",
                "--log-type",
                "traffic",
            ],
        )

        assert result.exit_code == 0
        assert "Created auto tag action" in result.stdout

    def test_show_auto_tag_action_list(self, runner, monkeypatch):
        """Test the show auto-tag-action list command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "ata-1", "name": "action-1", "folder": "Texas", "log_type": "traffic"},
                {"id": "ata-2", "name": "action-2", "folder": "Texas", "log_type": "threat"},
            ]

        monkeypatch.setattr(scm_client, "list_auto_tag_actions", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_auto_tag_action)

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "action-1" in result.stdout
        assert "action-2" in result.stdout

    def test_delete_auto_tag_action_command(self, runner, monkeypatch):
        """Test the delete auto-tag-action command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return None

        monkeypatch.setattr(scm_client, "delete_auto_tag_action", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_auto_tag_action)

        result = runner.invoke(test_app, ["test-action", "--folder", "Texas", "--force"])

        assert result.exit_code == 0
        assert "Deleted auto tag action" in result.stdout


class TestApplicationFilterUpsert:
    """Test application filter updated/no_change actions."""

    def test_set_application_filter_updated(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "af-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_application_filter", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_application_filter)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "high-risk-apps",
             "--category", "business-systems", "--subcategory", "database",
             "--technology", "client-server", "--risk", "4"],
        )

        assert result.exit_code == 0
        assert "Updated application filter" in result.stdout

    def test_set_application_filter_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "af-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_application_filter", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_application_filter)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "high-risk-apps",
             "--category", "business-systems", "--subcategory", "database",
             "--technology", "client-server", "--risk", "4"],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout


class TestExternalDynamicListUpsert:
    """Test external dynamic list updated/no_change actions."""

    def test_set_external_dynamic_list_updated(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "edl-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_external_dynamic_list", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_external_dynamic_list)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Texas",
                "--name", "test-edl",
                "--type", "ip",
                "--url", "https://example.com/blocklist.txt",
                "--recurring", "hourly",
            ],
        )

        assert result.exit_code == 0
        assert "Updated external dynamic list" in result.stdout

    def test_set_external_dynamic_list_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "edl-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_external_dynamic_list", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_external_dynamic_list)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Texas",
                "--name", "test-edl",
                "--type", "ip",
                "--url", "https://example.com/blocklist.txt",
                "--recurring", "hourly",
            ],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout


class TestHIPObjectUpsert:
    """Test HIP object updated/no_change actions."""

    def test_set_hip_object_updated(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "hip-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_hip_object", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_hip_object)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Texas",
                "--name", "wifi-only",
                "--network-info-type", "is",
                "--network-info-value", "wifi",
            ],
        )

        assert result.exit_code == 0
        assert "Updated HIP object" in result.stdout

    def test_set_hip_object_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "hip-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_hip_object", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_hip_object)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Texas",
                "--name", "wifi-only",
                "--network-info-type", "is",
                "--network-info-value", "wifi",
            ],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout


class TestHIPProfileUpsert:
    """Test HIP profile updated/no_change actions."""

    def test_set_hip_profile_updated(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "hpp-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_hip_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_hip_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "test-profile", "--match", "\"wifi-only\" is"],
        )

        assert result.exit_code == 0
        assert "Updated HIP profile" in result.stdout

    def test_set_hip_profile_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "hpp-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_hip_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_hip_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "test-profile", "--match", "\"wifi-only\" is"],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout


class TestHTTPServerProfileUpsert:
    """Test HTTP server profile updated/no_change actions."""

    def test_set_http_server_profile_updated(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "hsp-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_http_server_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_http_server_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Texas",
                "--name", "test-http-profile",
                "--servers", '[{"name": "srv1", "address": "192.168.1.100", "protocol": "HTTPS", "port": 443, "http_method": "POST"}]',
            ],
        )

        assert result.exit_code == 0
        assert "Updated HTTP server profile" in result.stdout

    def test_set_http_server_profile_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "hsp-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_http_server_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_http_server_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Texas",
                "--name", "test-http-profile",
                "--servers", '[{"name": "srv1", "address": "192.168.1.100", "protocol": "HTTPS", "port": 443, "http_method": "POST"}]',
            ],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout


class TestLogForwardingProfileUpsert:
    """Test log forwarding profile updated/no_change actions."""

    def test_set_log_forwarding_profile_updated(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "lfp-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_log_forwarding_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_log_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "test-lfp"],
        )

        assert result.exit_code == 0
        assert "Updated log forwarding profile" in result.stdout

    def test_set_log_forwarding_profile_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "lfp-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_log_forwarding_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_log_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "test-lfp"],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout


class TestServiceGroupUpsert:
    """Test service group updated/no_change actions."""

    def test_set_service_group_updated(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "sg-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_service_group", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_service_group)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "web-services", "--members", "http,https"],
        )

        assert result.exit_code == 0
        assert "Updated service group" in result.stdout

    def test_set_service_group_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "sg-123",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_service_group", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_service_group)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "web-services", "--members", "http,https"],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout


class TestSyslogServerProfileUpsert:
    """Test syslog server profile updated/no_change actions."""

    def test_set_syslog_server_profile_updated(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "ssp-123",
                "name": "test-syslog",
                "folder": "Texas",
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_syslog_server_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_syslog_server_profile)

        result = runner.invoke(
            test_app,
            [
                "test-syslog",
                "--server-name", "syslog-srv",
                "--server-address", "10.0.0.1",
                "--transport", "UDP",
                "--port", "514",
                "--format", "BSD",
                "--facility", "LOG_USER",
                "--folder", "Texas",
            ],
        )

        assert result.exit_code == 0
        assert "Updated syslog server profile" in result.stdout

    def test_set_syslog_server_profile_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "ssp-123",
                "name": "test-syslog",
                "folder": "Texas",
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_syslog_server_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_syslog_server_profile)

        result = runner.invoke(
            test_app,
            [
                "test-syslog",
                "--server-name", "syslog-srv",
                "--server-address", "10.0.0.1",
                "--transport", "UDP",
                "--port", "514",
                "--format", "BSD",
                "--facility", "LOG_USER",
                "--folder", "Texas",
            ],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout

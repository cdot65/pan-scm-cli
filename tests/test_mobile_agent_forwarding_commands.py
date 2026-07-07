"""Tests for the mobile agent forwarding profile and destination commands."""

import pytest
import typer  # noqa: I001
from pydantic import ValidationError

from scm_cli.commands.mobile_agent import (
    backup_forwarding_profile,
    backup_forwarding_profile_destination,
    delete_forwarding_profile,
    delete_forwarding_profile_destination,
    load_forwarding_profile,
    load_forwarding_profile_destination,
    set_forwarding_profile,
    set_forwarding_profile_destination,
    show_forwarding_profile,
    show_forwarding_profile_destination,
)
from scm_cli.utils.validators import ForwardingProfile, ForwardingProfileDestination

# =============================================================================================================================================================================================
# VALIDATOR TESTS
# =============================================================================================================================================================================================


class TestForwardingProfileValidator:
    """Test the ForwardingProfile validator model."""

    def test_requires_folder(self):
        """Test that a missing folder raises a validation error."""
        with pytest.raises(ValidationError):
            ForwardingProfile(name="profile1")

    def test_invalid_definition_method(self):
        """Test that an invalid definition method is rejected."""
        with pytest.raises(ValidationError):
            ForwardingProfile(name="profile1", folder="Mobile Users", definition_method="bogus")

    def test_invalid_type_key(self):
        """Test that an unknown profile type key is rejected."""
        with pytest.raises(ValidationError):
            ForwardingProfile(name="profile1", folder="Mobile Users", type={"bogus_type": {}})

    def test_multiple_type_keys_rejected(self):
        """Test that more than one profile type key is rejected."""
        with pytest.raises(ValidationError):
            ForwardingProfile(
                name="profile1",
                folder="Mobile Users",
                type={"pac_file": {}, "ztna_agent": {}},
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = ForwardingProfile(
            name="ztna-profile",
            folder="Mobile Users",
            description="ZTNA profile",
            definition_method="rules",
            type={"ztna_agent": {"pac_upload": False}},
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "ztna-profile"
        assert sdk_data["folder"] == "Mobile Users"
        assert sdk_data["description"] == "ZTNA profile"
        assert sdk_data["definition_method"] == "rules"
        assert sdk_data["type"] == {"ztna_agent": {"pac_upload": False}}

    def test_rules_and_block_rule_pass_through(self):
        """Test that nested forwarding rules and block rule validate."""
        profile = ForwardingProfile(
            name="pac-profile",
            folder="Mobile Users",
            type={
                "pac_file": {
                    "pac_upload": True,
                    "forwarding_rules": [
                        {"name": "rule1", "enabled": True, "connectivity": "direct"},
                    ],
                    "block_rule": {"enable": True},
                }
            },
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["type"]["pac_file"]["forwarding_rules"][0]["name"] == "rule1"


class TestForwardingProfileDestinationValidator:
    """Test the ForwardingProfileDestination validator model."""

    def test_requires_folder(self):
        """Test that a missing folder raises a validation error."""
        with pytest.raises(ValidationError):
            ForwardingProfileDestination(name="dest1")

    def test_fqdn_string_with_port_parsed(self):
        """Test that 'host:port' fqdn strings are parsed into entries."""
        dest = ForwardingProfileDestination(
            name="dest1",
            folder="Mobile Users",
            fqdn=["*.example.com:8080", "app.internal"],
        )
        sdk_data = dest.to_sdk_model()
        assert sdk_data["fqdn"] == [
            {"name": "*.example.com", "port": 8080},
            {"name": "app.internal"},
        ]

    def test_ip_string_with_port_parsed(self):
        """Test that 'ip:port' strings are parsed into entries."""
        dest = ForwardingProfileDestination(
            name="dest1",
            folder="Mobile Users",
            ip_addresses=["10.0.0.0/8", "192.168.1.1:443"],
        )
        sdk_data = dest.to_sdk_model()
        assert sdk_data["ip_addresses"] == [
            {"name": "10.0.0.0/8"},
            {"name": "192.168.1.1", "port": 443},
        ]

    def test_fqdn_dict_entries_accepted(self):
        """Test that dict-style fqdn entries (YAML load path) are accepted."""
        dest = ForwardingProfileDestination(
            name="dest1",
            folder="Mobile Users",
            fqdn=[{"name": "app.example.com", "port": 443}],
        )
        sdk_data = dest.to_sdk_model()
        assert sdk_data["fqdn"] == [{"name": "app.example.com", "port": 443}]

    def test_invalid_port_rejected(self):
        """Test that an out-of-range port is rejected."""
        with pytest.raises(ValidationError):
            ForwardingProfileDestination(
                name="dest1",
                folder="Mobile Users",
                fqdn=["app.example.com:99999"],
            )


# =============================================================================================================================================================================================
# FORWARDING PROFILE COMMAND TESTS
# =============================================================================================================================================================================================


class TestForwardingProfileCommands:
    """Test the forwarding profile commands."""

    def test_set_forwarding_profile(self, runner, monkeypatch):
        """Test creating a forwarding profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "11111111-1111-1111-1111-111111111111",
                "name": kwargs.get("name"),
                "definition_method": kwargs.get("definition_method"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "ztna-profile",
                "--profile-type", "ztna-agent",
            ],
        )

        assert result.exit_code == 0
        assert "Created forwarding profile" in result.stdout
        assert "ztna-profile" in result.stdout

    def test_set_forwarding_profile_builds_type_skeleton(self, runner, monkeypatch):
        """Test that --profile-type builds the correct type wrapper."""
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_create(*args, **kwargs):
            captured.update(kwargs)
            return {"name": kwargs.get("name"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_forwarding_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "proxy-profile",
                "--profile-type", "global-protect-proxy",
                "--pac-upload",
            ],
        )

        assert result.exit_code == 0
        assert captured["type"] == {"global_protect_proxy": {"pac_upload": True}}

    def test_set_forwarding_profile_updated(self, runner, monkeypatch):
        """Test updating a forwarding profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"name": kwargs.get("name"), "__action__": "updated"}

        monkeypatch.setattr(scm_client, "create_forwarding_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "ztna-profile"],
        )

        assert result.exit_code == 0
        assert "Updated forwarding profile" in result.stdout

    def test_set_forwarding_profile_no_change(self, runner, monkeypatch):
        """Test set forwarding profile with no changes."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"name": kwargs.get("name"), "__action__": "no_change"}

        monkeypatch.setattr(scm_client, "create_forwarding_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "ztna-profile"],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout

    def test_set_forwarding_profile_missing_folder(self, runner, monkeypatch):
        """Test that a missing folder fails container validation."""
        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile)

        result = runner.invoke(test_app, ["ztna-profile"])

        assert result.exit_code == 1

    def test_set_forwarding_profile_error(self, runner, monkeypatch):
        """Test set forwarding profile with an API error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "create_forwarding_profile", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "fail-profile"],
        )

        assert result.exit_code == 1

    def test_show_forwarding_profile_list(self, runner, monkeypatch):
        """Test listing forwarding profiles."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "name": "ztna-profile",
                    "definition_method": "rules",
                },
                {
                    "id": "22222222-2222-2222-2222-222222222222",
                    "name": "pac-profile",
                    "definition_method": "pac-file",
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profiles", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "ztna-profile" in result.stdout
        assert "pac-profile" in result.stdout

    def test_show_forwarding_profile_by_name(self, runner, monkeypatch):
        """Test showing a forwarding profile by name."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "11111111-1111-1111-1111-111111111111",
                "name": "ztna-profile",
                "description": "ZTNA profile",
                "definition_method": "rules",
                "type": {"ztna_agent": {"pac_upload": False}},
            }

        monkeypatch.setattr(scm_client, "get_forwarding_profile", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "ztna-profile"],
        )

        assert result.exit_code == 0
        assert "ztna-profile" in result.stdout
        assert "ztna_agent" in result.stdout

    def test_show_forwarding_profile_by_id(self, runner, monkeypatch):
        """Test showing a forwarding profile by UUID."""
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_get(*args, **kwargs):
            captured.update(kwargs)
            return {
                "id": "11111111-1111-1111-1111-111111111111",
                "name": "ztna-profile",
            }

        monkeypatch.setattr(scm_client, "get_forwarding_profile", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--id", "11111111-1111-1111-1111-111111111111"],
        )

        assert result.exit_code == 0
        assert captured["profile_id"] == "11111111-1111-1111-1111-111111111111"
        assert "ztna-profile" in result.stdout

    def test_show_forwarding_profile_empty(self, runner, monkeypatch):
        """Test listing forwarding profiles when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_forwarding_profiles", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "No results found" in result.stdout

    def test_show_forwarding_profile_error(self, runner, monkeypatch):
        """Test showing forwarding profiles with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "list_forwarding_profiles", mock_error)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 1

    def test_delete_forwarding_profile(self, runner, monkeypatch):
        """Test deleting a forwarding profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_forwarding_profile", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "ztna-profile", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted forwarding profile" in result.stdout

    def test_delete_forwarding_profile_requires_name_or_id(self, runner, monkeypatch):
        """Delete without NAME or --id fails with a clear error."""
        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--force"],
        )

        assert result.exit_code == 1
        assert "provide NAME or --id" in result.output

    def test_show_forwarding_profile_max_results(self, runner, monkeypatch):
        """--max-results slices the profile list client-side."""
        import json

        from scm_cli.utils.sdk_client import scm_client

        profiles = [{"id": f"fp-{i}", "folder": "Mobile Users", "name": f"profile-{i}", "definition_method": "rules"} for i in range(4)]
        monkeypatch.setattr(scm_client, "list_forwarding_profiles", lambda *a, **k: profiles)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users", "--max-results", "3", "--output", "json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == profiles[:3]

    def test_delete_forwarding_profile_error(self, runner, monkeypatch):
        """Test deleting a forwarding profile with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "delete_forwarding_profile", mock_error)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "nonexistent", "--force"],
        )

        assert result.exit_code == 1

    def test_load_forwarding_profile(self, runner, monkeypatch, tmp_path):
        """Test loading forwarding profiles from YAML."""
        from scm_cli.utils.sdk_client import scm_client

        yaml_content = """
forwarding_profiles:
  - name: ztna-profile
    folder: "Mobile Users"
    definition_method: rules
    type:
      ztna_agent:
        pac_upload: false
        forwarding_rules:
          - name: rule1
            traffic_type: dns
        block_rule:
          block_all_other_unmatched_outbound_connections: true
  - name: pac-profile
    folder: "Mobile Users"
    definition_method: pac-file
    type:
      pac_file:
        pac_upload: true
"""
        test_file = tmp_path / "forwarding_profiles.yml"
        test_file.write_text(yaml_content)

        def mock_create(*args, **kwargs):
            return {"name": kwargs.get("name"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_forwarding_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile)

        result = runner.invoke(test_app, ["--file", str(test_file)])

        assert result.exit_code == 0
        assert "Created forwarding profile" in result.stdout
        assert "2 created" in result.stdout

    def test_load_forwarding_profile_dry_run(self, runner, monkeypatch, tmp_path):
        """Test loading forwarding profiles in dry run mode."""
        yaml_content = """
forwarding_profiles:
  - name: ztna-profile
    folder: "Mobile Users"
"""
        test_file = tmp_path / "forwarding_profiles.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile)

        result = runner.invoke(test_app, ["--file", str(test_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout

    def test_backup_forwarding_profile(self, runner, monkeypatch, tmp_path):
        """Test backing up forwarding profiles."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "name": "ztna-profile",
                    "definition_method": "rules",
                    "type": {"ztna_agent": {"pac_upload": False}},
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profiles", mock_list)
        monkeypatch.chdir(tmp_path)

        test_app = typer.Typer()
        test_app.command()(backup_forwarding_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "Successfully backed up" in result.stdout
        assert "1 forwarding profiles" in result.stdout


# =============================================================================================================================================================================================
# FORWARDING PROFILE DESTINATION COMMAND TESTS
# =============================================================================================================================================================================================


class TestForwardingProfileDestinationCommands:
    """Test the forwarding profile destination commands."""

    def test_set_forwarding_profile_destination(self, runner, monkeypatch):
        """Test creating a forwarding profile destination."""
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_create(*args, **kwargs):
            captured.update(kwargs)
            return {
                "id": "33333333-3333-3333-3333-333333333333",
                "name": kwargs.get("name"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_destination", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_destination)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "internal-apps",
                "--fqdn", "*.example.com:8080",
                "--fqdn", "app.internal",
                "--ip-address", "10.0.0.0/8",
            ],
        )

        assert result.exit_code == 0
        assert "Created forwarding profile destination" in result.stdout
        assert captured["fqdn"] == [
            {"name": "*.example.com", "port": 8080},
            {"name": "app.internal"},
        ]
        assert captured["ip_addresses"] == [{"name": "10.0.0.0/8"}]

    def test_set_forwarding_profile_destination_missing_folder(self, runner):
        """Test that a missing folder fails container validation."""
        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_destination)

        result = runner.invoke(test_app, ["internal-apps"])

        assert result.exit_code == 1

    def test_set_forwarding_profile_destination_error(self, runner, monkeypatch):
        """Test set destination with an API error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "create_forwarding_profile_destination", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_destination)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "fail-dest"],
        )

        assert result.exit_code == 1

    def test_show_forwarding_profile_destination_list(self, runner, monkeypatch):
        """Test listing forwarding profile destinations."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "33333333-3333-3333-3333-333333333333",
                    "name": "internal-apps",
                    "fqdn": [{"name": "app.internal"}],
                },
                {
                    "id": "44444444-4444-4444-4444-444444444444",
                    "name": "corp-ranges",
                    "ip_addresses": [{"name": "10.0.0.0/8"}],
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profile_destinations", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_destination)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "internal-apps" in result.stdout
        assert "corp-ranges" in result.stdout

    def test_show_forwarding_profile_destination_by_name(self, runner, monkeypatch):
        """Test showing a forwarding profile destination by name."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "33333333-3333-3333-3333-333333333333",
                "name": "internal-apps",
                "description": "Internal applications",
                "fqdn": [{"name": "app.internal", "port": 443}],
            }

        monkeypatch.setattr(scm_client, "get_forwarding_profile_destination", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_destination)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "internal-apps"],
        )

        assert result.exit_code == 0
        assert "internal-apps" in result.stdout
        assert "app.internal" in result.stdout

    def test_show_forwarding_profile_destination_by_id(self, runner, monkeypatch):
        """Test showing a forwarding profile destination by UUID."""
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_get(*args, **kwargs):
            captured.update(kwargs)
            return {
                "id": "33333333-3333-3333-3333-333333333333",
                "name": "internal-apps",
            }

        monkeypatch.setattr(scm_client, "get_forwarding_profile_destination", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_destination)

        result = runner.invoke(
            test_app,
            ["--id", "33333333-3333-3333-3333-333333333333"],
        )

        assert result.exit_code == 0
        assert captured["destination_id"] == "33333333-3333-3333-3333-333333333333"

    def test_show_forwarding_profile_destination_empty(self, runner, monkeypatch):
        """Test listing destinations when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_forwarding_profile_destinations", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_destination)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "No results found" in result.stdout

    def test_delete_forwarding_profile_destination(self, runner, monkeypatch):
        """Test deleting a forwarding profile destination."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_forwarding_profile_destination", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile_destination)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "internal-apps", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted forwarding profile destination" in result.stdout

    def test_delete_forwarding_profile_destination_error(self, runner, monkeypatch):
        """Test deleting a destination with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "delete_forwarding_profile_destination", mock_error)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile_destination)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "nonexistent", "--force"],
        )

        assert result.exit_code == 1

    def test_load_forwarding_profile_destination(self, runner, monkeypatch, tmp_path):
        """Test loading forwarding profile destinations from YAML."""
        from scm_cli.utils.sdk_client import scm_client

        yaml_content = """
forwarding_profile_destinations:
  - name: internal-apps
    folder: "Mobile Users"
    fqdn:
      - name: app.internal
        port: 443
  - name: corp-ranges
    folder: "Mobile Users"
    ip_addresses:
      - name: 10.0.0.0/8
"""
        test_file = tmp_path / "destinations.yml"
        test_file.write_text(yaml_content)

        def mock_create(*args, **kwargs):
            return {"name": kwargs.get("name"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_forwarding_profile_destination", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile_destination)

        result = runner.invoke(test_app, ["--file", str(test_file)])

        assert result.exit_code == 0
        assert "Created forwarding profile destination" in result.stdout
        assert "2 created" in result.stdout

    def test_load_forwarding_profile_destination_dry_run(self, runner, tmp_path):
        """Test loading destinations in dry run mode."""
        yaml_content = """
forwarding_profile_destinations:
  - name: internal-apps
    folder: "Mobile Users"
"""
        test_file = tmp_path / "destinations.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile_destination)

        result = runner.invoke(test_app, ["--file", str(test_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout

    def test_backup_forwarding_profile_destination(self, runner, monkeypatch, tmp_path):
        """Test backing up forwarding profile destinations."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "33333333-3333-3333-3333-333333333333",
                    "name": "internal-apps",
                    "fqdn": [{"name": "app.internal"}],
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profile_destinations", mock_list)
        monkeypatch.chdir(tmp_path)

        test_app = typer.Typer()
        test_app.command()(backup_forwarding_profile_destination)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "Successfully backed up" in result.stdout
        assert "1 forwarding profile destinations" in result.stdout


class TestShowJsonOutput:
    """Test the --output json format for show commands."""

    def test_show_forwarding_profile_list_json(self, runner, monkeypatch):
        """Test listing forwarding profiles as JSON."""
        import json

        from scm_cli.utils.sdk_client import scm_client

        profiles = [
            {"id": "fp-1", "folder": "Mobile Users", "name": "ztna-profile", "type": {"ztna_agent": {}}},
            {"id": "fp-2", "folder": "Mobile Users", "name": "pac-profile", "type": {"pac_file": {}}},
        ]
        monkeypatch.setattr(scm_client, "list_forwarding_profiles", lambda *a, **k: profiles)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users", "--output", "json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == profiles

    def test_show_forwarding_profile_destination_detail_json(self, runner, monkeypatch):
        """Test showing a forwarding profile destination as JSON."""
        import json

        from scm_cli.utils.sdk_client import scm_client

        destination = {
            "id": "fpd-1",
            "folder": "Mobile Users",
            "name": "internal-apps",
            "fqdn": [{"name": "app.internal", "port": 443}],
            "ip_addresses": [{"name": "10.0.0.0/8"}],
        }
        monkeypatch.setattr(scm_client, "get_forwarding_profile_destination", lambda *a, **k: destination)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_destination)

        result = runner.invoke(test_app, ["--folder", "Mobile Users", "internal-apps", "--output", "json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == destination

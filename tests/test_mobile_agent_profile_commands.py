"""Tests for the mobile agent agent-profile and tunnel-profile commands."""

import pytest  # noqa: I001
import typer
from pydantic import ValidationError
from scm_cli.commands.mobile_agent import (
    backup_agent_profile,
    backup_tunnel_profile,
    delete_agent_profile,
    delete_tunnel_profile,
    load_agent_profile,
    load_tunnel_profile,
    set_agent_profile,
    set_tunnel_profile,
    show_agent_profile,
    show_tunnel_profile,
)
from scm_cli.utils.validators import AgentProfile, TunnelProfile


class TestAgentProfileValidator:
    """Test the AgentProfile validator model."""

    def test_to_sdk_model_folds_app_config_flags(self):
        """Test connect_method and tunnel_mtu fold into gp_app_config."""
        profile = AgentProfile(
            name="corp-app-settings",
            folder="Mobile Users",
            connect_method="user-logon",
            tunnel_mtu=1400,
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["gp_app_config"] == {
            "config": [
                {"name": "connect-method", "value": ["user-logon"]},
                {"name": "tunnel-mtu", "value": [1400]},
            ]
        }

    def test_to_sdk_model_explicit_gp_app_config_wins(self):
        """Test explicit gp_app_config takes precedence over convenience flags."""
        explicit = {"config": [{"name": "connect-method", "value": ["on-demand"]}]}
        profile = AgentProfile(
            name="corp-app-settings",
            connect_method="user-logon",
            gp_app_config=explicit,
        )
        assert profile.to_sdk_model()["gp_app_config"] == explicit

    def test_invalid_folder_rejected(self):
        """Test folder other than 'Mobile Users' is rejected."""
        with pytest.raises(ValidationError, match="Mobile Users"):
            AgentProfile(name="x", folder="Shared")

    def test_invalid_connect_method_rejected(self):
        """Test invalid connect_method is rejected."""
        with pytest.raises(ValidationError, match="connect_method"):
            AgentProfile(name="x", connect_method="always-on")

    def test_invalid_os_rejected(self):
        """Test invalid os value is rejected."""
        with pytest.raises(ValidationError, match="os values"):
            AgentProfile(name="x", os=["Solaris"])

    def test_invalid_save_user_credentials_rejected(self):
        """Test invalid save_user_credentials is rejected."""
        with pytest.raises(ValidationError, match="save_user_credentials"):
            AgentProfile(name="x", save_user_credentials="9")

    def test_tunnel_mtu_range_enforced(self):
        """Test tunnel_mtu outside 1000-1420 is rejected."""
        with pytest.raises(ValidationError):
            AgentProfile(name="x", tunnel_mtu=999)


class TestTunnelProfileValidator:
    """Test the TunnelProfile validator model."""

    def test_to_sdk_model_folds_split_tunneling_flags(self):
        """Test route/application flags fold into split_tunneling."""
        profile = TunnelProfile(
            name="corp-tunnel",
            access_route=["10.0.0.0/8"],
            exclude_access_route=["192.168.1.0/24"],
            include_applications=["slack"],
            exclude_applications=["spotify"],
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["split_tunneling"] == {
            "access_route": ["10.0.0.0/8"],
            "exclude_access_route": ["192.168.1.0/24"],
            "include_applications": ["slack"],
            "exclude_applications": ["spotify"],
        }

    def test_to_sdk_model_explicit_split_tunneling_wins(self):
        """Test explicit split_tunneling takes precedence over convenience flags."""
        explicit = {"access_route": ["172.16.0.0/12"]}
        profile = TunnelProfile(
            name="corp-tunnel",
            access_route=["10.0.0.0/8"],
            split_tunneling=explicit,
        )
        assert profile.to_sdk_model()["split_tunneling"] == explicit

    def test_invalid_folder_rejected(self):
        """Test folder other than 'Mobile Users' is rejected."""
        with pytest.raises(ValidationError, match="Mobile Users"):
            TunnelProfile(name="x", folder="Shared")

    def test_name_max_length_enforced(self):
        """Test name longer than 31 chars is rejected."""
        with pytest.raises(ValidationError):
            TunnelProfile(name="x" * 32)


class TestAgentProfileCommands:
    """Test the agent profile commands."""

    def test_set_agent_profile(self, runner, monkeypatch):
        """Test creating an agent profile."""
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_create(*args, **kwargs):
            captured.update(kwargs)
            return {
                "id": "ap-corp",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "gp_app_config": kwargs.get("gp_app_config"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_agent_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_agent_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "corp-app-settings",
                "--connect-method", "user-logon",
                "--tunnel-mtu", "1400",
                "--os", "Windows",
                "--os", "Mac",
            ],
        )

        assert result.exit_code == 0
        assert "Created agent profile" in result.stdout
        assert captured["gp_app_config"] == {
            "config": [
                {"name": "connect-method", "value": ["user-logon"]},
                {"name": "tunnel-mtu", "value": [1400]},
            ]
        }
        assert captured["os"] == ["Windows", "Mac"]

    def test_set_agent_profile_update(self, runner, monkeypatch):
        """Test updating an agent profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"id": "ap-corp", "name": kwargs.get("name"), "__action__": "updated"}

        monkeypatch.setattr(scm_client, "create_agent_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_agent_profile)

        result = runner.invoke(
            test_app,
            ["--name", "corp-app-settings", "--save-user-credentials", "1"],
        )

        assert result.exit_code == 0
        assert "Updated agent profile" in result.stdout

    def test_set_agent_profile_no_change(self, runner, monkeypatch):
        """Test set agent profile with no changes."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"id": "ap-corp", "name": kwargs.get("name"), "__action__": "no_change"}

        monkeypatch.setattr(scm_client, "create_agent_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_agent_profile)

        result = runner.invoke(test_app, ["--name", "corp-app-settings"])

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout

    def test_set_agent_profile_invalid_folder(self, runner, monkeypatch):
        """Test set agent profile with invalid folder fails validation."""
        test_app = typer.Typer()
        test_app.command()(set_agent_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Shared", "--name", "corp-app-settings"],
        )

        assert result.exit_code == 1
        assert "Validation error" in result.output

    def test_set_agent_profile_error(self, runner, monkeypatch):
        """Test set agent profile with API error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "create_agent_profile", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_agent_profile)

        result = runner.invoke(test_app, ["--name", "fail-profile"])

        assert result.exit_code == 1

    def test_show_agent_profile_list(self, runner, monkeypatch):
        """Test listing agent profiles."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "ap-1", "folder": "Mobile Users", "name": "corp-app-settings", "os": ["Windows"]},
                {"id": "ap-2", "folder": "Mobile Users", "name": "byod-app-settings", "os": ["iOS", "Android"]},
            ]

        monkeypatch.setattr(scm_client, "list_agent_profiles", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_agent_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "corp-app-settings" in result.stdout
        assert "byod-app-settings" in result.stdout

    def test_show_agent_profile_detail(self, runner, monkeypatch):
        """Test showing a specific agent profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "ap-corp",
                "folder": "Mobile Users",
                "name": "corp-app-settings",
                "os": ["Windows", "Mac"],
                "save_user_credentials": "0",
                "gp_app_config": {"config": [{"name": "connect-method", "value": ["user-logon"]}]},
            }

        monkeypatch.setattr(scm_client, "get_agent_profile", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_agent_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "corp-app-settings"],
        )

        assert result.exit_code == 0
        assert "corp-app-settings" in result.stdout
        assert "Windows, Mac" in result.stdout
        assert "connect-method" in result.stdout

    def test_show_agent_profile_empty(self, runner, monkeypatch):
        """Test listing agent profiles when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_agent_profiles", lambda *a, **kw: [])

        test_app = typer.Typer()
        test_app.command()(show_agent_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "No results found" in result.stdout

    def test_delete_agent_profile(self, runner, monkeypatch):
        """Test deleting an agent profile."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "delete_agent_profile", lambda *a, **kw: True)

        test_app = typer.Typer()
        test_app.command()(delete_agent_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "corp-app-settings", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted agent profile" in result.stdout

    def test_delete_agent_profile_error(self, runner, monkeypatch):
        """Test deleting an agent profile with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "delete_agent_profile", mock_error)

        test_app = typer.Typer()
        test_app.command()(delete_agent_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "nonexistent", "--force"],
        )

        assert result.exit_code == 1

    def test_load_agent_profile(self, runner, monkeypatch, tmp_path):
        """Test loading agent profiles from YAML."""
        from scm_cli.utils.sdk_client import scm_client

        yaml_content = """
agent_profiles:
  - name: corp-app-settings
    folder: "Mobile Users"
    connect_method: user-logon
    os:
      - Windows
  - name: byod-app-settings
    folder: "Mobile Users"
    save_user_credentials: "3"
"""
        test_file = tmp_path / "agent_profiles.yml"
        test_file.write_text(yaml_content)

        def mock_create(*args, **kwargs):
            return {"name": kwargs.get("name"), "folder": kwargs.get("folder"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_agent_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_agent_profile)

        result = runner.invoke(test_app, ["--file", str(test_file)])

        assert result.exit_code == 0
        assert "Created agent profile" in result.stdout
        assert "2 created" in result.stdout

    def test_load_agent_profile_dry_run(self, runner, tmp_path):
        """Test loading agent profiles in dry run mode."""
        yaml_content = """
agent_profiles:
  - name: corp-app-settings
    folder: "Mobile Users"
"""
        test_file = tmp_path / "agent_profiles.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_agent_profile)

        result = runner.invoke(test_app, ["--file", str(test_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout

    def test_backup_agent_profile(self, runner, monkeypatch, tmp_path):
        """Test backing up agent profiles."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "ap-1", "folder": "Mobile Users", "name": "corp-app-settings", "os": ["Windows"]},
            ]

        monkeypatch.setattr(scm_client, "list_agent_profiles", mock_list)
        monkeypatch.chdir(tmp_path)

        test_app = typer.Typer()
        test_app.command()(backup_agent_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "Successfully backed up" in result.stdout
        assert "1 agent profiles" in result.stdout


class TestTunnelProfileCommands:
    """Test the tunnel profile commands."""

    def test_set_tunnel_profile(self, runner, monkeypatch):
        """Test creating a tunnel profile."""
        from scm_cli.utils.sdk_client import scm_client

        captured = {}

        def mock_create(*args, **kwargs):
            captured.update(kwargs)
            return {
                "id": "tp-corp",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_tunnel_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_tunnel_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "corp-tunnel",
                "--access-route", "10.0.0.0/8",
                "--no-direct-access-to-local-network",
            ],
        )

        assert result.exit_code == 0
        assert "Created tunnel profile" in result.stdout
        assert captured["split_tunneling"] == {"access_route": ["10.0.0.0/8"]}
        assert captured["no_direct_access_to_local_network"] is True

    def test_set_tunnel_profile_update(self, runner, monkeypatch):
        """Test updating a tunnel profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"id": "tp-corp", "name": kwargs.get("name"), "__action__": "updated"}

        monkeypatch.setattr(scm_client, "create_tunnel_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_tunnel_profile)

        result = runner.invoke(
            test_app,
            ["--name", "corp-tunnel", "--retrieve-framed-ip-address"],
        )

        assert result.exit_code == 0
        assert "Updated tunnel profile" in result.stdout

    def test_set_tunnel_profile_no_change(self, runner, monkeypatch):
        """Test set tunnel profile with no changes."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"id": "tp-corp", "name": kwargs.get("name"), "__action__": "no_change"}

        monkeypatch.setattr(scm_client, "create_tunnel_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_tunnel_profile)

        result = runner.invoke(test_app, ["--name", "corp-tunnel"])

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout

    def test_set_tunnel_profile_invalid_folder(self, runner):
        """Test set tunnel profile with invalid folder fails validation."""
        test_app = typer.Typer()
        test_app.command()(set_tunnel_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Shared", "--name", "corp-tunnel"],
        )

        assert result.exit_code == 1
        assert "Validation error" in result.output

    def test_set_tunnel_profile_error(self, runner, monkeypatch):
        """Test set tunnel profile with API error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "create_tunnel_profile", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_tunnel_profile)

        result = runner.invoke(test_app, ["--name", "fail-tunnel"])

        assert result.exit_code == 1

    def test_show_tunnel_profile_list(self, runner, monkeypatch):
        """Test listing tunnel profiles."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "tp-1", "folder": "Mobile Users", "name": "corp-tunnel"},
                {"id": "tp-2", "folder": "Mobile Users", "name": "byod-tunnel", "no_direct_access_to_local_network": True},
            ]

        monkeypatch.setattr(scm_client, "list_tunnel_profiles", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_tunnel_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "corp-tunnel" in result.stdout
        assert "byod-tunnel" in result.stdout

    def test_show_tunnel_profile_detail(self, runner, monkeypatch):
        """Test showing a specific tunnel profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "tp-corp",
                "folder": "Mobile Users",
                "name": "corp-tunnel",
                "no_direct_access_to_local_network": False,
                "split_tunneling": {"access_route": ["10.0.0.0/8"]},
            }

        monkeypatch.setattr(scm_client, "get_tunnel_profile", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_tunnel_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "corp-tunnel"],
        )

        assert result.exit_code == 0
        assert "corp-tunnel" in result.stdout
        assert "10.0.0.0/8" in result.stdout

    def test_show_tunnel_profile_empty(self, runner, monkeypatch):
        """Test listing tunnel profiles when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_tunnel_profiles", lambda *a, **kw: [])

        test_app = typer.Typer()
        test_app.command()(show_tunnel_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "No results found" in result.stdout

    def test_delete_tunnel_profile(self, runner, monkeypatch):
        """Test deleting a tunnel profile."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "delete_tunnel_profile", lambda *a, **kw: True)

        test_app = typer.Typer()
        test_app.command()(delete_tunnel_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "corp-tunnel", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted tunnel profile" in result.stdout

    def test_delete_tunnel_profile_error(self, runner, monkeypatch):
        """Test deleting a tunnel profile with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "delete_tunnel_profile", mock_error)

        test_app = typer.Typer()
        test_app.command()(delete_tunnel_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "nonexistent", "--force"],
        )

        assert result.exit_code == 1

    def test_load_tunnel_profile(self, runner, monkeypatch, tmp_path):
        """Test loading tunnel profiles from YAML."""
        from scm_cli.utils.sdk_client import scm_client

        yaml_content = """
tunnel_profiles:
  - name: corp-tunnel
    folder: "Mobile Users"
    access_route:
      - 10.0.0.0/8
  - name: byod-tunnel
    folder: "Mobile Users"
    no_direct_access_to_local_network: true
"""
        test_file = tmp_path / "tunnel_profiles.yml"
        test_file.write_text(yaml_content)

        def mock_create(*args, **kwargs):
            return {"name": kwargs.get("name"), "folder": kwargs.get("folder"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_tunnel_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_tunnel_profile)

        result = runner.invoke(test_app, ["--file", str(test_file)])

        assert result.exit_code == 0
        assert "Created tunnel profile" in result.stdout
        assert "2 created" in result.stdout

    def test_load_tunnel_profile_dry_run(self, runner, tmp_path):
        """Test loading tunnel profiles in dry run mode."""
        yaml_content = """
tunnel_profiles:
  - name: corp-tunnel
    folder: "Mobile Users"
"""
        test_file = tmp_path / "tunnel_profiles.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_tunnel_profile)

        result = runner.invoke(test_app, ["--file", str(test_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout

    def test_backup_tunnel_profile(self, runner, monkeypatch, tmp_path):
        """Test backing up tunnel profiles."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"id": "tp-1", "folder": "Mobile Users", "name": "corp-tunnel", "split_tunneling": {"access_route": ["10.0.0.0/8"]}},
            ]

        monkeypatch.setattr(scm_client, "list_tunnel_profiles", mock_list)
        monkeypatch.chdir(tmp_path)

        test_app = typer.Typer()
        test_app.command()(backup_tunnel_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users"])

        assert result.exit_code == 0
        assert "Successfully backed up" in result.stdout
        assert "1 tunnel profiles" in result.stdout


class TestShowJsonOutput:
    """Test the --output json format for show commands."""

    def test_show_agent_profile_detail_json(self, runner, monkeypatch):
        """Test showing an agent profile as JSON."""
        import json

        from scm_cli.utils.sdk_client import scm_client

        profile = {
            "id": "ap-corp",
            "folder": "Mobile Users",
            "name": "corp-app-settings",
            "os": ["Windows", "Mac"],
            "gp_app_config": {"config": [{"name": "connect-method", "value": ["user-logon"]}]},
        }
        monkeypatch.setattr(scm_client, "get_agent_profile", lambda *a, **k: profile)

        test_app = typer.Typer()
        test_app.command()(show_agent_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users", "--name", "corp-app-settings", "--output", "json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == profile

    def test_show_tunnel_profile_list_json(self, runner, monkeypatch):
        """Test listing tunnel profiles as JSON."""
        import json

        from scm_cli.utils.sdk_client import scm_client

        profiles = [
            {"id": "tp-1", "folder": "Mobile Users", "name": "corp-tunnel", "split_tunneling": {"access_route": ["10.0.0.0/8"]}},
            {"id": "tp-2", "folder": "Mobile Users", "name": "byod-tunnel"},
        ]
        monkeypatch.setattr(scm_client, "list_tunnel_profiles", lambda *a, **k: profiles)

        test_app = typer.Typer()
        test_app.command()(show_tunnel_profile)

        result = runner.invoke(test_app, ["--folder", "Mobile Users", "--output", "json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == profiles

"""Tests for the mobile agent infrastructure setting and global setting commands."""

import typer  # noqa: I001
from scm_cli.commands.mobile_agent import (
    backup_infrastructure_setting,
    delete_infrastructure_setting,
    load_infrastructure_setting,
    set_global_setting,
    set_infrastructure_setting,
    show_global_setting,
    show_infrastructure_setting,
)

DNS_SERVERS_JSON = '[{"name": "dns-1", "dns_suffix": ["example.com"]}]'
IP_POOLS_JSON = '[{"name": "pool-1", "ip_pool": ["10.0.0.0/16"]}]'
PORTAL_HOSTNAME_JSON = '{"default_domain": {"hostname": "acme"}}'


class TestInfrastructureSettingCommands:
    """Test the infrastructure setting commands."""

    def test_set_infrastructure_setting(self, runner, monkeypatch):
        """Test creating an infrastructure setting."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "is-gp-infra",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "dns_servers": kwargs.get("dns_servers"),
                "ip_pools": kwargs.get("ip_pools"),
                "portal_hostname": kwargs.get("portal_hostname"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_infrastructure_setting", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_infrastructure_setting)

        result = runner.invoke(
            test_app,
            [
                "--name", "gp-infra",
                "--dns-servers", DNS_SERVERS_JSON,
                "--ip-pools", IP_POOLS_JSON,
                "--portal-hostname", PORTAL_HOSTNAME_JSON,
            ],
        )

        assert result.exit_code == 0
        assert "Created infrastructure setting" in result.stdout
        assert "gp-infra" in result.stdout

    def test_set_infrastructure_setting_update(self, runner, monkeypatch):
        """Test updating an infrastructure setting."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "is-gp-infra",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_infrastructure_setting", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_infrastructure_setting)

        result = runner.invoke(
            test_app,
            [
                "--name", "gp-infra",
                "--dns-servers", DNS_SERVERS_JSON,
                "--ip-pools", IP_POOLS_JSON,
                "--portal-hostname", PORTAL_HOSTNAME_JSON,
                "--ipv6",
            ],
        )

        assert result.exit_code == 0
        assert "Updated infrastructure setting" in result.stdout

    def test_set_infrastructure_setting_no_change(self, runner, monkeypatch):
        """Test set infrastructure setting with no changes."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "is-gp-infra",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_infrastructure_setting", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_infrastructure_setting)

        result = runner.invoke(
            test_app,
            [
                "--name", "gp-infra",
                "--dns-servers", DNS_SERVERS_JSON,
                "--ip-pools", IP_POOLS_JSON,
                "--portal-hostname", PORTAL_HOSTNAME_JSON,
            ],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout

    def test_set_infrastructure_setting_invalid_json(self, runner, monkeypatch):
        """Test set infrastructure setting with malformed JSON option."""
        test_app = typer.Typer()
        test_app.command()(set_infrastructure_setting)

        result = runner.invoke(
            test_app,
            [
                "--name", "gp-infra",
                "--dns-servers", "not-json",
                "--ip-pools", IP_POOLS_JSON,
                "--portal-hostname", PORTAL_HOSTNAME_JSON,
            ],
        )

        assert result.exit_code == 1

    def test_set_infrastructure_setting_invalid_folder(self, runner, monkeypatch):
        """Test set infrastructure setting with a folder other than Mobile Users."""
        test_app = typer.Typer()
        test_app.command()(set_infrastructure_setting)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Texas",
                "--name", "gp-infra",
                "--dns-servers", DNS_SERVERS_JSON,
                "--ip-pools", IP_POOLS_JSON,
                "--portal-hostname", PORTAL_HOSTNAME_JSON,
            ],
        )

        assert result.exit_code == 1

    def test_set_infrastructure_setting_error(self, runner, monkeypatch):
        """Test set infrastructure setting with an API error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "create_infrastructure_setting", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_infrastructure_setting)

        result = runner.invoke(
            test_app,
            [
                "--name", "gp-infra",
                "--dns-servers", DNS_SERVERS_JSON,
                "--ip-pools", IP_POOLS_JSON,
                "--portal-hostname", PORTAL_HOSTNAME_JSON,
            ],
        )

        assert result.exit_code == 1

    def test_show_infrastructure_setting(self, runner, monkeypatch):
        """Test showing an infrastructure setting."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "is-gp-infra",
                "folder": "Mobile Users",
                "name": "gp-infra",
                "dns_servers": [{"name": "dns-1", "dns_suffix": ["example.com"]}],
                "ip_pools": [{"name": "pool-1", "ip_pool": ["10.0.0.0/16"]}],
                "portal_hostname": {"default_domain": {"hostname": "acme"}},
                "ipv6": True,
            }

        monkeypatch.setattr(scm_client, "get_infrastructure_setting", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_infrastructure_setting)

        result = runner.invoke(
            test_app,
            ["--name", "gp-infra"],
        )

        assert result.exit_code == 0
        assert "gp-infra" in result.stdout
        assert "10.0.0.0/16" in result.stdout
        assert "Ipv6" in result.stdout

    def test_show_infrastructure_setting_error(self, runner, monkeypatch):
        """Test showing an infrastructure setting with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "get_infrastructure_setting", mock_error)

        test_app = typer.Typer()
        test_app.command()(show_infrastructure_setting)

        result = runner.invoke(
            test_app,
            ["--name", "nonexistent"],
        )

        assert result.exit_code == 1

    def test_delete_infrastructure_setting(self, runner, monkeypatch):
        """Test deleting an infrastructure setting."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_infrastructure_setting", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_infrastructure_setting)

        result = runner.invoke(
            test_app,
            ["--name", "gp-infra", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted infrastructure setting" in result.stdout

    def test_delete_infrastructure_setting_error(self, runner, monkeypatch):
        """Test deleting an infrastructure setting with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "delete_infrastructure_setting", mock_error)

        test_app = typer.Typer()
        test_app.command()(delete_infrastructure_setting)

        result = runner.invoke(
            test_app,
            ["--name", "nonexistent", "--force"],
        )

        assert result.exit_code == 1

    def test_backup_infrastructure_setting(self, runner, monkeypatch, tmp_path):
        """Test backing up an infrastructure setting."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "is-gp-infra",
                    "folder": "Mobile Users",
                    "name": "gp-infra",
                    "dns_servers": [{"name": "dns-1", "dns_suffix": ["example.com"]}],
                    "ip_pools": [{"name": "pool-1", "ip_pool": ["10.0.0.0/16"]}],
                    "portal_hostname": {"default_domain": {"hostname": "acme"}},
                },
            ]

        monkeypatch.setattr(scm_client, "list_infrastructure_settings", mock_list)
        monkeypatch.chdir(tmp_path)

        test_app = typer.Typer()
        test_app.command()(backup_infrastructure_setting)

        result = runner.invoke(
            test_app,
            ["--name", "gp-infra"],
        )

        assert result.exit_code == 0
        assert "Successfully backed up" in result.stdout
        assert "1 infrastructure settings" in result.stdout

    def test_backup_infrastructure_setting_empty(self, runner, monkeypatch, tmp_path):
        """Test backing up when no infrastructure setting matches."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_infrastructure_settings", mock_list)
        monkeypatch.chdir(tmp_path)

        test_app = typer.Typer()
        test_app.command()(backup_infrastructure_setting)

        result = runner.invoke(
            test_app,
            ["--name", "missing"],
        )

        assert result.exit_code == 0
        assert "No infrastructure settings named" in result.stdout

    def test_load_infrastructure_setting(self, runner, monkeypatch, tmp_path):
        """Test loading infrastructure settings from YAML."""
        from scm_cli.utils.sdk_client import scm_client

        yaml_content = """
infrastructure_settings:
  - name: gp-infra
    folder: "Mobile Users"
    dns_servers:
      - name: dns-1
        dns_suffix:
          - example.com
    ip_pools:
      - name: pool-1
        ip_pool:
          - 10.0.0.0/16
    portal_hostname:
      default_domain:
        hostname: acme
"""
        test_file = tmp_path / "infrastructure_settings.yml"
        test_file.write_text(yaml_content)

        def mock_create(*args, **kwargs):
            return {
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_infrastructure_setting", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_infrastructure_setting)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file)],
        )

        assert result.exit_code == 0
        assert "Created infrastructure setting" in result.stdout
        assert "1 created" in result.stdout

    def test_load_infrastructure_setting_dry_run(self, runner, monkeypatch, tmp_path):
        """Test loading infrastructure settings in dry run mode."""
        yaml_content = """
infrastructure_settings:
  - name: gp-infra
    folder: "Mobile Users"
    dns_servers: []
    ip_pools: []
    portal_hostname: {}
"""
        test_file = tmp_path / "infrastructure_settings.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_infrastructure_setting)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file), "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout


class TestGlobalSettingCommands:
    """Test the global setting commands."""

    def test_show_global_setting(self, runner, monkeypatch):
        """Test showing the global settings."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "agent_version": "6.2.0",
                "manual_gateway": {"region": [{"name": "americas", "locations": ["us-east-1"]}]},
            }

        monkeypatch.setattr(scm_client, "get_global_settings", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_global_setting)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "6.2.0" in result.stdout
        assert "americas" in result.stdout

    def test_show_global_setting_error(self, runner, monkeypatch):
        """Test showing global settings with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "get_global_settings", mock_error)

        test_app = typer.Typer()
        test_app.command()(show_global_setting)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 1

    def test_set_global_setting_agent_version(self, runner, monkeypatch):
        """Test updating the global settings agent version."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_update(*args, **kwargs):
            return {
                "agent_version": kwargs.get("agent_version"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "update_global_settings", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_global_setting)

        result = runner.invoke(
            test_app,
            ["--agent-version", "6.2.0"],
        )

        assert result.exit_code == 0
        assert "Updated GlobalProtect global settings" in result.stdout

    def test_set_global_setting_manual_gateway(self, runner, monkeypatch):
        """Test updating the global settings manual gateway."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_update(*args, **kwargs):
            return {
                "manual_gateway": kwargs.get("manual_gateway"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "update_global_settings", mock_update)

        test_app = typer.Typer()
        test_app.command()(set_global_setting)

        result = runner.invoke(
            test_app,
            ["--manual-gateway", '{"region": [{"name": "americas", "locations": ["us-east-1"]}]}'],
        )

        assert result.exit_code == 0
        assert "Updated GlobalProtect global settings" in result.stdout

    def test_set_global_setting_no_fields(self, runner, monkeypatch):
        """Test set global setting with no fields fails validation."""
        test_app = typer.Typer()
        test_app.command()(set_global_setting)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 1

    def test_set_global_setting_invalid_json(self, runner, monkeypatch):
        """Test set global setting with malformed JSON option."""
        test_app = typer.Typer()
        test_app.command()(set_global_setting)

        result = runner.invoke(
            test_app,
            ["--manual-gateway", "not-json"],
        )

        assert result.exit_code == 1

    def test_set_global_setting_error(self, runner, monkeypatch):
        """Test set global setting with an API error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "update_global_settings", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_global_setting)

        result = runner.invoke(
            test_app,
            ["--agent-version", "6.2.0"],
        )

        assert result.exit_code == 1


class TestShowJsonOutput:
    """Test the --output json format for show commands."""

    def test_show_infrastructure_setting_json(self, runner, monkeypatch):
        """Test showing an infrastructure setting as JSON."""
        import json

        from scm_cli.utils.sdk_client import scm_client

        setting = {
            "id": "is-gp-infra",
            "folder": "Mobile Users",
            "name": "gp-infra",
            "dns_servers": [{"name": "dns-1", "dns_suffix": ["example.com"]}],
            "ip_pools": [{"name": "pool-1", "ip_pool": ["10.0.0.0/16"]}],
            "portal_hostname": {"default_domain": {"hostname": "acme"}},
            "ipv6": True,
        }
        monkeypatch.setattr(scm_client, "get_infrastructure_setting", lambda *a, **k: setting)

        test_app = typer.Typer()
        test_app.command()(show_infrastructure_setting)

        result = runner.invoke(test_app, ["--name", "gp-infra", "--output", "json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == setting

    def test_show_global_setting_json(self, runner, monkeypatch):
        """Test showing global settings as JSON."""
        import json

        from scm_cli.utils.sdk_client import scm_client

        setting = {
            "agent_version": "6.2.0",
            "manual_gateway": {"region": [{"name": "americas", "locations": ["us-east-1"]}]},
        }
        monkeypatch.setattr(scm_client, "get_global_settings", lambda *a, **k: setting)

        test_app = typer.Typer()
        test_app.command()(show_global_setting)

        result = runner.invoke(test_app, ["--output", "json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == setting

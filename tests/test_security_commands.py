"""Tests for the security commands module."""

import typer

from scm_cli.commands.security import (
    delete_app,
    delete_dns_security_profile,
    delete_security_rule,
    delete_wildfire_antivirus_profile,
    load_app,
    load_security_rule,
    load_wildfire_antivirus_profile,
    set_app,
    set_dns_security_profile,
    set_security_rule,
    set_wildfire_antivirus_profile,
    show_dns_security_profile,
    show_wildfire_antivirus_profile,
)


class TestSecurityCommands:
    """Test the security commands."""

    def test_set_command_exists(self):
        """Test that the set command exists."""
        assert set_app

    def test_delete_command_exists(self):
        """Test that the delete command exists."""
        assert delete_app

    def test_load_command_exists(self):
        """Test that the load command exists."""
        assert load_app


class TestSecurityRuleCommands:
    """Test the security rule commands."""

    def test_set_security_rule_command(self, runner, monkeypatch):
        """Test the set security rule command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "sr-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "source_zones": kwargs.get("source_zones", []),
                "destination_zones": kwargs.get("destination_zones", []),
                "source_addresses": kwargs.get("source_addresses", ["any"]),
                "destination_addresses": kwargs.get("destination_addresses", ["any"]),
                "applications": kwargs.get("applications", ["any"]),
                "action": kwargs.get("action", "allow"),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
                "enabled": kwargs.get("enabled", True),
            }

        monkeypatch.setattr(scm_client, "create_security_rule", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_security_rule)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-rule",
                "--source-zones",
                "trust",
                "--destination-zones",
                "untrust",
                "--source-addresses",
                "192.168.1.0/24",
                "--destination-addresses",
                "any",
                "--applications",
                "web-browsing",
                "--applications",
                "ssl",
                "--action",
                "allow",
                "--description",
                "Test security rule",
                "--tags",
                "test",
                "--tags",
                "example",
                "--enabled",
            ],
        )

        assert result.exit_code == 0
        assert "Created security rule" in result.stdout
        assert "test-rule" in result.stdout
        assert "test-folder" in result.stdout

    def test_set_security_rule_error(self, runner, monkeypatch):
        """Test the set security rule command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_security_rule", mock_create_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_security_rule)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-rule",
                "--source-zones",
                "trust",
                "--destination-zones",
                "untrust",
                "--action",
                "allow",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating security rule" in result.stdout
        assert "Test error" in result.stdout

    def test_delete_security_rule_command(self, runner, monkeypatch):
        """Test the delete security rule command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_security_rule", mock_delete)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_security_rule)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-rule",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted security rule" in result.stdout
        assert "test-rule" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_security_rule_error(self, runner, monkeypatch):
        """Test the delete security rule command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_security_rule", mock_delete_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_security_rule)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-rule",
            ],
        )

        assert result.exit_code == 1
        assert "Error deleting security rule" in result.stdout
        assert "Test error" in result.stdout

    def test_load_security_rule_command(self, runner, monkeypatch, mock_security_rules_yaml_file):
        """Test the load security rule command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        created_rules = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"sr-{len(created_rules) + 1}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "source_zones": kwargs.get("source_zones", []),
                "destination_zones": kwargs.get("destination_zones", []),
                "source_addresses": kwargs.get("source_addresses", ["any"]),
                "destination_addresses": kwargs.get("destination_addresses", ["any"]),
                "applications": kwargs.get("applications", ["any"]),
                "action": kwargs.get("action", "allow"),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
                "enabled": kwargs.get("enabled", True),
            }
            created_rules.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_security_rule", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_security_rule)

        # Invoke the command
        result = runner.invoke(test_app, ["--file", str(mock_security_rules_yaml_file)])

        assert result.exit_code == 0
        assert "Applied security rule" in result.stdout
        assert "test-rule" in result.stdout
        assert "test-folder" in result.stdout
        assert len(created_rules) == 1

    def test_load_security_rule_dry_run(self, runner, monkeypatch, mock_security_rules_yaml_file):
        """Test the load security rule command with dry-run option."""
        # Mock the SCM client method to track if it gets called
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_security_rule", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_security_rule)

        # Invoke the command with dry-run
        result = runner.invoke(test_app, ["--file", str(mock_security_rules_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called  # Ensure the create method was not called


class TestWildfireAntivirusProfileCommands:
    """Test the WildFire antivirus profile commands."""

    def _mock_scm_client(self, monkeypatch):
        """Set up a mock SCM client to avoid real API calls."""
        from unittest.mock import MagicMock

        import scm_cli.commands.security as sec_module

        mock_client = MagicMock()
        monkeypatch.setattr(sec_module, "scm_client", mock_client)
        return mock_client

    def test_set_wildfire_antivirus_profile_command(self, runner, monkeypatch):
        """Test the set wildfire-antivirus-profile command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_wildfire_antivirus_profile.return_value = {
            "id": "wfav-12345",
            "name": "wf-test",
            "folder": "Texas",
            "rules": [],
        }

        test_app = typer.Typer()
        test_app.command()(set_wildfire_antivirus_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "wf-test",
                "--description",
                "Test WildFire profile",
            ],
        )

        assert result.exit_code == 0
        assert "Created WildFire antivirus profile" in result.stdout
        assert "wf-test" in result.stdout

    def test_set_wildfire_antivirus_profile_with_rules_json(self, runner, monkeypatch):
        """Test set wildfire-antivirus-profile with custom rules JSON."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_wildfire_antivirus_profile.return_value = {
            "id": "wfav-12345",
            "name": "wf-custom",
            "folder": "Texas",
            "rules": [],
        }

        test_app = typer.Typer()
        test_app.command()(set_wildfire_antivirus_profile)

        rules = '[{"name":"Forward All","direction":"both","analysis":"public-cloud","application":["any"],"file_type":["any"]}]'
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "wf-custom",
                "--rules",
                rules,
            ],
        )

        assert result.exit_code == 0
        assert "Created WildFire antivirus profile" in result.stdout

    def test_set_wildfire_antivirus_profile_error(self, runner, monkeypatch):
        """Test the set wildfire-antivirus-profile command with an error."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_wildfire_antivirus_profile.side_effect = ValueError("Test error")

        test_app = typer.Typer()
        test_app.command()(set_wildfire_antivirus_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "wf-test",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating WildFire antivirus profile" in result.stdout

    def test_delete_wildfire_antivirus_profile_command(self, runner, monkeypatch):
        """Test the delete wildfire-antivirus-profile command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.delete_wildfire_antivirus_profile.return_value = True

        test_app = typer.Typer()
        test_app.command()(delete_wildfire_antivirus_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "wf-test",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted WildFire antivirus profile" in result.stdout
        assert "wf-test" in result.stdout

    def test_show_wildfire_antivirus_profile_list(self, runner, monkeypatch):
        """Test the show wildfire-antivirus-profile command (list mode)."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.list_wildfire_antivirus_profiles.return_value = [
            {
                "id": "wfav-1",
                "folder": "Texas",
                "name": "WF Profile 1",
                "description": "First profile",
                "rules": [{"name": "rule1", "direction": "both"}],
            },
            {
                "id": "wfav-2",
                "folder": "Texas",
                "name": "WF Profile 2",
                "rules": [{"name": "rule2", "direction": "upload"}],
            },
        ]

        test_app = typer.Typer()
        test_app.command()(show_wildfire_antivirus_profile)

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "WF Profile 1" in result.stdout
        assert "WF Profile 2" in result.stdout

    def test_show_wildfire_antivirus_profile_single(self, runner, monkeypatch):
        """Test the show wildfire-antivirus-profile command (single profile)."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.get_wildfire_antivirus_profile.return_value = {
            "id": "wfav-1",
            "folder": "Texas",
            "name": "WF Test",
            "description": "Test profile",
            "packet_capture": True,
            "rules": [
                {
                    "name": "Forward All",
                    "direction": "both",
                    "analysis": "public-cloud",
                    "application": ["any"],
                    "file_type": ["any"],
                }
            ],
        }

        test_app = typer.Typer()
        test_app.command()(show_wildfire_antivirus_profile)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "WF Test"])

        assert result.exit_code == 0
        assert "WF Test" in result.stdout
        assert "Packet Capture: Enabled" in result.stdout
        assert "Forward All" in result.stdout

    def test_load_wildfire_antivirus_profile_command(self, runner, monkeypatch, tmp_path):
        """Test the load wildfire-antivirus-profile command."""
        mock_client = self._mock_scm_client(monkeypatch)
        call_count = {"n": 0}

        def mock_create(*args, **kwargs):
            call_count["n"] += 1
            return {
                "id": f"wfav-{call_count['n']}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "rules": kwargs.get("rules", []),
            }

        mock_client.create_wildfire_antivirus_profile.side_effect = mock_create

        # Create a test YAML file
        yaml_content = """
wildfire_antivirus_profiles:
  - name: wf-test
    folder: Texas
    rules:
      - name: Forward All
        direction: both
        analysis: public-cloud
        application:
          - any
        file_type:
          - any
"""
        test_file = tmp_path / "wf_profiles.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_wildfire_antivirus_profile)

        result = runner.invoke(test_app, ["--file", str(test_file)])

        assert result.exit_code == 0
        assert "Successfully processed" in result.stdout
        assert call_count["n"] == 1

    def test_load_wildfire_antivirus_profile_dry_run(self, runner, monkeypatch, tmp_path):
        """Test the load wildfire-antivirus-profile command with dry-run."""
        mock_client = self._mock_scm_client(monkeypatch)

        yaml_content = """
wildfire_antivirus_profiles:
  - name: wf-test
    folder: Texas
    rules:
      - name: Forward All
        direction: both
        application:
          - any
        file_type:
          - any
"""
        test_file = tmp_path / "wf_profiles.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_wildfire_antivirus_profile)

        result = runner.invoke(test_app, ["--file", str(test_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        mock_client.create_wildfire_antivirus_profile.assert_not_called()


class TestDNSSecurityProfileCommands:
    """Test the DNS security profile commands."""

    def _mock_scm_client(self, monkeypatch):
        """Set up a mock SCM client to avoid real API calls."""
        from unittest.mock import MagicMock

        import scm_cli.commands.security as sec_module

        mock_client = MagicMock()
        monkeypatch.setattr(sec_module, "scm_client", mock_client)
        return mock_client

    def test_set_dns_security_profile_command(self, runner, monkeypatch):
        """Test the set DNS security profile command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_dns_security_profile.return_value = {
            "id": "dns-sec-12345",
            "name": "dns-sec-test",
            "folder": "Texas",
            "botnet_domains": {},
            "__action__": "created",
        }

        test_app = typer.Typer()
        test_app.command()(set_dns_security_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "dns-sec-test",
                "--description",
                "Test DNS security profile",
                "--botnet-domains",
                '{"dns_security_categories": [{"name": "pan-dns-sec-malware", "action": "sinkhole"}]}',
            ],
        )

        assert result.exit_code == 0
        assert "Created DNS security profile" in result.stdout
        assert "dns-sec-test" in result.stdout

    def test_set_dns_security_profile_error(self, runner, monkeypatch):
        """Test the set DNS security profile command with an error."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_dns_security_profile.side_effect = ValueError("Test error")

        test_app = typer.Typer()
        test_app.command()(set_dns_security_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "dns-sec-test",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating DNS security profile" in result.stdout

    def test_delete_dns_security_profile_command(self, runner, monkeypatch):
        """Test the delete DNS security profile command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.delete_dns_security_profile.return_value = True

        test_app = typer.Typer()
        test_app.command()(delete_dns_security_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "dns-sec-test",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted DNS security profile" in result.stdout
        assert "dns-sec-test" in result.stdout

    def test_show_dns_security_profile_list(self, runner, monkeypatch):
        """Test the show DNS security profile command listing all profiles."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.list_dns_security_profiles.return_value = [
            {
                "id": "dns-sec-mock1",
                "name": "DNS-Security-Default",
                "folder": "Texas",
                "description": "Default DNS security profile",
                "botnet_domains": {
                    "dns_security_categories": [
                        {"name": "pan-dns-sec-malware", "action": "sinkhole"},
                    ],
                    "sinkhole": {"ipv4_address": "pan-sinkhole-default-ip", "ipv6_address": "::1"},
                },
            },
        ]

        test_app = typer.Typer()
        test_app.command()(show_dns_security_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
            ],
        )

        assert result.exit_code == 0
        assert "DNS-Security-Default" in result.stdout

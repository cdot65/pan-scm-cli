"""Tests for the security commands module."""

import typer

from scm_cli.commands.security import (  # noqa: F401
    delete_app,
    delete_app_override_rule,
    delete_authentication_rule,
    delete_decryption_rule,
    delete_dns_security_profile,
    delete_security_rule,
    delete_url_access_profile,
    delete_url_category,
    delete_vulnerability_protection_profile,
    delete_wildfire_antivirus_profile,
    load_app,
    load_security_rule,
    load_vulnerability_protection_profile,
    load_wildfire_antivirus_profile,
    move_app,
    move_app_override_rule_cmd,
    move_authentication_rule_cmd,
    move_decryption_rule_cmd,
    move_security_rule_cmd,
    set_app,
    set_app_override_rule,
    set_authentication_rule,
    set_decryption_rule,
    set_dns_security_profile,
    set_security_rule,
    set_url_access_profile,
    set_url_category,
    set_vulnerability_protection_profile,
    set_wildfire_antivirus_profile,
    show_app_override_rule,
    show_authentication_rule,
    show_decryption_rule,
    show_dns_security_profile,
    show_url_access_profile,
    show_url_category,
    show_vulnerability_protection_profile,
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
                "--force",
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
                "--force",
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
        assert "Successfully processed 1 security rule(s)" in result.stdout
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
                "--force",
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
                "--force",
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


class TestVulnerabilityProtectionProfileCommands:
    """Test the vulnerability protection profile commands."""

    def test_set_vulnerability_protection_profile_command(self, runner, monkeypatch):
        """Test the set vulnerability protection profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "vpp-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "rules": kwargs.get("rules", []),
                "description": kwargs.get("description", ""),
            }

        monkeypatch.setattr(scm_client, "create_vulnerability_protection_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_vulnerability_protection_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-vuln-profile",
                "--description",
                "Test vulnerability protection",
            ],
        )

        assert result.exit_code == 0
        assert "Created vulnerability protection profile" in result.stdout
        assert "test-vuln-profile" in result.stdout

    def test_set_vulnerability_protection_profile_block_critical_high(self, runner, monkeypatch):
        """Test the set command with --block-critical-high flag."""
        from scm_cli.utils.sdk_client import scm_client

        captured_kwargs = {}

        def mock_create(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return {
                "id": "vpp-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "rules": kwargs.get("rules", []),
            }

        monkeypatch.setattr(scm_client, "create_vulnerability_protection_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_vulnerability_protection_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "strict-vuln",
                "--block-critical-high",
            ],
        )

        assert result.exit_code == 0
        assert captured_kwargs.get("rules") is not None
        assert len(captured_kwargs["rules"]) == 1
        assert "critical" in captured_kwargs["rules"][0]["severity"]
        assert "high" in captured_kwargs["rules"][0]["severity"]

    def test_set_vulnerability_protection_profile_error(self, runner, monkeypatch):
        """Test the set command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_vulnerability_protection_profile", mock_create_error)

        test_app = typer.Typer()
        test_app.command()(set_vulnerability_protection_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-vuln",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating vulnerability protection profile" in result.stdout

    def test_delete_vulnerability_protection_profile_command(self, runner, monkeypatch):
        """Test the delete vulnerability protection profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_vulnerability_protection_profile", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_vulnerability_protection_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-vuln",
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted vulnerability protection profile" in result.stdout
        assert "test-vuln" in result.stdout

    def test_delete_vulnerability_protection_profile_error(self, runner, monkeypatch):
        """Test the delete command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_vulnerability_protection_profile", mock_delete_error)

        test_app = typer.Typer()
        test_app.command()(delete_vulnerability_protection_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-vuln",
                "--force",
            ],
        )

        assert result.exit_code == 1
        assert "Error deleting vulnerability protection profile" in result.stdout

    def test_show_vulnerability_protection_profile_single(self, runner, monkeypatch):
        """Test the show command for a single profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "vpp-12345",
                "name": "test-vuln",
                "folder": "Texas",
                "description": "Test profile",
                "rules": [
                    {
                        "name": "Block Critical",
                        "severity": ["critical", "high"],
                        "category": "any",
                        "host": "any",
                        "action": {"alert": {}},
                        "packet_capture": "single-packet",
                    }
                ],
            }

        monkeypatch.setattr(scm_client, "get_vulnerability_protection_profile", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_vulnerability_protection_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-vuln",
            ],
        )

        assert result.exit_code == 0
        assert "Vulnerability Protection Profile: test-vuln" in result.stdout
        assert "Block Critical" in result.stdout

    def test_show_vulnerability_protection_profile_list(self, runner, monkeypatch):
        """Test the show command listing all profiles."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "vpp-1",
                    "name": "strict-vuln",
                    "folder": "Texas",
                    "rules": [{"name": "r1", "action": {"alert": {}}}],
                },
                {
                    "id": "vpp-2",
                    "name": "standard-vuln",
                    "folder": "Texas",
                    "rules": [{"name": "r2", "action": {"default": {}}}],
                },
            ]

        monkeypatch.setattr(scm_client, "list_vulnerability_protection_profiles", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_vulnerability_protection_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
            ],
        )

        assert result.exit_code == 0
        assert "strict-vuln" in result.stdout
        assert "standard-vuln" in result.stdout

    def test_load_vulnerability_protection_profile_command(self, runner, monkeypatch, tmp_path):
        """Test the load vulnerability protection profile command."""
        from scm_cli.utils.sdk_client import scm_client

        created_profiles = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"vpp-{len(created_profiles) + 1}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "rules": kwargs.get("rules", []),
            }
            created_profiles.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_vulnerability_protection_profile", mock_create)

        # Create YAML file
        yaml_file = tmp_path / "vuln_profiles.yml"
        yaml_file.write_text("""
vulnerability_protection_profiles:
  - name: test-vuln
    folder: Texas
    rules:
      - name: Block Critical
        severity:
          - critical
          - high
        category: any
        host: any
        action:
          alert: {}
""")

        test_app = typer.Typer()
        test_app.command()(load_vulnerability_protection_profile)

        result = runner.invoke(test_app, ["--file", str(yaml_file)])

        assert result.exit_code == 0
        assert "Successfully processed 1 vulnerability protection profile(s)" in result.stdout
        assert len(created_profiles) == 1

    def test_load_vulnerability_protection_profile_dry_run(self, runner, monkeypatch, tmp_path):
        """Test the load command with dry-run option."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_vulnerability_protection_profile", mock_create)

        yaml_file = tmp_path / "vuln_profiles.yml"
        yaml_file.write_text("""
vulnerability_protection_profiles:
  - name: test-vuln
    folder: Texas
    rules:
      - name: Block Critical
        severity:
          - critical
        category: any
        host: any
""")

        test_app = typer.Typer()
        test_app.command()(load_vulnerability_protection_profile)

        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called


class TestURLCategoryCommands:
    """Test the URL category commands."""

    def test_set_url_category_command(self, runner, monkeypatch):
        """Test the set URL category command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "urlcat-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "type": kwargs.get("type", "URL List"),
                "list": kwargs.get("list", []),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_url_category", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_url_category)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "custom-block",
                "--url",
                "malware.example.com",
                "--url",
                "phishing.test.org",
            ],
        )

        assert result.exit_code == 0
        assert "Created URL category" in result.stdout
        assert "custom-block" in result.stdout

    def test_set_url_category_error(self, runner, monkeypatch):
        """Test the set URL category command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_url_category", mock_create_error)

        test_app = typer.Typer()
        test_app.command()(set_url_category)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-category",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating URL category" in result.stdout

    def test_delete_url_category_command(self, runner, monkeypatch):
        """Test the delete URL category command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_url_category", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_url_category)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "custom-block",
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted URL category" in result.stdout
        assert "custom-block" in result.stdout

    def test_show_url_category_list(self, runner, monkeypatch):
        """Test the show URL category command for listing."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "urlcat-1",
                    "name": "Custom-Block-List",
                    "folder": "Texas",
                    "type": "URL List",
                    "list": ["malware.example.com"],
                },
            ]

        monkeypatch.setattr(scm_client, "list_url_categories", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_url_category)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
            ],
        )

        assert result.exit_code == 0
        assert "Custom-Block-List" in result.stdout

    def test_show_url_category_by_name(self, runner, monkeypatch):
        """Test the show URL category command for a specific category."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "urlcat-1",
                "name": "Custom-Block-List",
                "folder": "Texas",
                "description": "Custom blocked URLs",
                "type": "URL List",
                "list": ["malware.example.com", "phishing.test.org"],
            }

        monkeypatch.setattr(scm_client, "get_url_category", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_url_category)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "Custom-Block-List",
            ],
        )

        assert result.exit_code == 0
        assert "Custom-Block-List" in result.stdout
        assert "malware.example.com" in result.stdout
        assert "phishing.test.org" in result.stdout


class TestAppOverrideRuleCommands:
    """Test the app override rule commands."""

    def _mock_scm_client(self, monkeypatch):
        """Set up a mock SCM client."""
        from unittest.mock import MagicMock

        import scm_cli.commands.security as sec_module

        mock_client = MagicMock()
        monkeypatch.setattr(sec_module, "scm_client", mock_client)
        return mock_client

    def test_set_app_override_rule(self, runner, monkeypatch):
        """Test the set app-override-rule command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_app_override_rule.return_value = {
            "id": "aor-1",
            "name": "override-https",
            "folder": "Texas",
            "application": "ssl",
            "port": "8443",
            "protocol": "tcp",
        }

        test_app = typer.Typer()
        test_app.command()(set_app_override_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "override-https",
                "--application",
                "ssl",
                "--port",
                "8443",
                "--protocol",
                "tcp",
            ],
        )

        assert result.exit_code == 0
        assert "Created app override rule" in result.stdout
        assert "override-https" in result.stdout

    def test_set_app_override_rule_error(self, runner, monkeypatch):
        """Test the set command with error."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_app_override_rule.side_effect = ValueError("Test error")

        test_app = typer.Typer()
        test_app.command()(set_app_override_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test",
                "--application",
                "ssl",
                "--port",
                "443",
                "--protocol",
                "tcp",
            ],
        )

        assert result.exit_code == 1

    def test_delete_app_override_rule(self, runner, monkeypatch):
        """Test the delete app-override-rule command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.delete_app_override_rule.return_value = True

        test_app = typer.Typer()
        test_app.command()(delete_app_override_rule)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "override-https", "--force"])

        assert result.exit_code == 0
        assert "Deleted app override rule" in result.stdout

    def test_show_app_override_rule_list(self, runner, monkeypatch):
        """Test the show command listing all rules."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.list_app_override_rules.return_value = [
            {"id": "aor-1", "name": "Override Web", "application": "web-browsing", "port": "443", "protocol": "tcp"},
        ]

        test_app = typer.Typer()
        test_app.command()(show_app_override_rule)

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "Override Web" in result.stdout

    def test_show_app_override_rule_single(self, runner, monkeypatch):
        """Test the show command for a single rule."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.get_app_override_rule.return_value = {
            "id": "aor-1",
            "name": "override-https",
            "folder": "Texas",
            "application": "ssl",
            "port": "8443",
            "protocol": "tcp",
        }

        test_app = typer.Typer()
        test_app.command()(show_app_override_rule)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "override-https"])

        assert result.exit_code == 0
        assert "App Override Rule: override-https" in result.stdout
        assert "ssl" in result.stdout


class TestAuthenticationRuleCommands:
    """Test the authentication rule commands."""

    def _mock_scm_client(self, monkeypatch):
        """Set up a mock SCM client."""
        from unittest.mock import MagicMock

        import scm_cli.commands.security as sec_module

        mock_client = MagicMock()
        monkeypatch.setattr(sec_module, "scm_client", mock_client)
        return mock_client

    def test_set_authentication_rule(self, runner, monkeypatch):
        """Test the set authentication-rule command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_authentication_rule.return_value = {
            "id": "authr-1",
            "name": "auth-web",
            "folder": "Texas",
        }

        test_app = typer.Typer()
        test_app.command()(set_authentication_rule)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "auth-web"])

        assert result.exit_code == 0
        assert "Created authentication rule" in result.stdout

    def test_set_authentication_rule_error(self, runner, monkeypatch):
        """Test the set command with error."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_authentication_rule.side_effect = ValueError("Test error")

        test_app = typer.Typer()
        test_app.command()(set_authentication_rule)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "test"])

        assert result.exit_code == 1

    def test_delete_authentication_rule(self, runner, monkeypatch):
        """Test the delete authentication-rule command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.delete_authentication_rule.return_value = True

        test_app = typer.Typer()
        test_app.command()(delete_authentication_rule)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "auth-web", "--force"])

        assert result.exit_code == 0
        assert "Deleted authentication rule" in result.stdout

    def test_show_authentication_rule_list(self, runner, monkeypatch):
        """Test the show command listing all rules."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.list_authentication_rules.return_value = [
            {"id": "authr-1", "name": "Auth Rule 1", "from": ["any"], "to": ["any"]},
        ]

        test_app = typer.Typer()
        test_app.command()(show_authentication_rule)

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "Auth Rule 1" in result.stdout

    def test_show_authentication_rule_single(self, runner, monkeypatch):
        """Test the show command for a single rule."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.get_authentication_rule.return_value = {
            "id": "authr-1",
            "name": "auth-web",
            "folder": "Texas",
            "from": ["trust"],
            "to": ["untrust"],
            "authentication_enforcement": "default-auth",
        }

        test_app = typer.Typer()
        test_app.command()(show_authentication_rule)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "auth-web"])

        assert result.exit_code == 0
        assert "Authentication Rule: auth-web" in result.stdout


class TestDecryptionRuleCommands:
    """Test the decryption rule commands."""

    def _mock_scm_client(self, monkeypatch):
        """Set up a mock SCM client."""
        from unittest.mock import MagicMock

        import scm_cli.commands.security as sec_module

        mock_client = MagicMock()
        monkeypatch.setattr(sec_module, "scm_client", mock_client)
        return mock_client

    def test_set_decryption_rule(self, runner, monkeypatch):
        """Test the set decryption-rule command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_decryption_rule.return_value = {
            "id": "decr-1",
            "name": "no-decrypt-internal",
            "folder": "Texas",
            "action": "no-decrypt",
        }

        test_app = typer.Typer()
        test_app.command()(set_decryption_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "no-decrypt-internal",
                "--action",
                "no-decrypt",
            ],
        )

        assert result.exit_code == 0
        assert "Created decryption rule" in result.stdout

    def test_set_decryption_rule_error(self, runner, monkeypatch):
        """Test the set command with error."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_decryption_rule.side_effect = ValueError("Test error")

        test_app = typer.Typer()
        test_app.command()(set_decryption_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test",
                "--action",
                "decrypt",
            ],
        )

        assert result.exit_code == 1

    def test_delete_decryption_rule(self, runner, monkeypatch):
        """Test the delete decryption-rule command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.delete_decryption_rule.return_value = True

        test_app = typer.Typer()
        test_app.command()(delete_decryption_rule)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "decrypt-web", "--force"])

        assert result.exit_code == 0
        assert "Deleted decryption rule" in result.stdout

    def test_show_decryption_rule_list(self, runner, monkeypatch):
        """Test the show command listing all rules."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.list_decryption_rules.return_value = [
            {"id": "decr-1", "name": "Decrypt Rule 1", "action": "no-decrypt"},
        ]

        test_app = typer.Typer()
        test_app.command()(show_decryption_rule)

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "Decrypt Rule 1" in result.stdout

    def test_show_decryption_rule_single(self, runner, monkeypatch):
        """Test the show command for a single rule."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.get_decryption_rule.return_value = {
            "id": "decr-1",
            "name": "decrypt-outbound",
            "folder": "Texas",
            "action": "decrypt",
            "from": ["trust"],
            "to": ["untrust"],
        }

        test_app = typer.Typer()
        test_app.command()(show_decryption_rule)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "decrypt-outbound"])

        assert result.exit_code == 0
        assert "Decryption Rule: decrypt-outbound" in result.stdout


class TestURLAccessProfileCommands:
    """Test the URL access profile commands."""

    def _mock_scm_client(self, monkeypatch):
        """Set up a mock SCM client."""
        from unittest.mock import MagicMock

        import scm_cli.commands.security as sec_module

        mock_client = MagicMock()
        monkeypatch.setattr(sec_module, "scm_client", mock_client)
        return mock_client

    def test_set_url_access_profile(self, runner, monkeypatch):
        """Test the set url-access-profile command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_url_access_profile.return_value = {
            "id": "uap-1",
            "name": "strict-url",
            "folder": "Texas",
        }

        test_app = typer.Typer()
        test_app.command()(set_url_access_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "strict-url",
                "--block",
                "adult",
                "--block",
                "malware",
            ],
        )

        assert result.exit_code == 0
        assert "Created URL access profile" in result.stdout

    def test_set_url_access_profile_error(self, runner, monkeypatch):
        """Test the set command with error."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.create_url_access_profile.side_effect = ValueError("Test error")

        test_app = typer.Typer()
        test_app.command()(set_url_access_profile)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "test"])

        assert result.exit_code == 1

    def test_delete_url_access_profile(self, runner, monkeypatch):
        """Test the delete url-access-profile command."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.delete_url_access_profile.return_value = True

        test_app = typer.Typer()
        test_app.command()(delete_url_access_profile)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "strict-url", "--force"])

        assert result.exit_code == 0
        assert "Deleted URL access profile" in result.stdout

    def test_show_url_access_profile_list(self, runner, monkeypatch):
        """Test the show command listing all profiles."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.list_url_access_profiles.return_value = [
            {"id": "uap-1", "name": "URL Profile 1", "block": ["adult", "malware"]},
        ]

        test_app = typer.Typer()
        test_app.command()(show_url_access_profile)

        result = runner.invoke(test_app, ["--folder", "Texas"])

        assert result.exit_code == 0
        assert "URL Profile 1" in result.stdout

    def test_show_url_access_profile_single(self, runner, monkeypatch):
        """Test the show command for a single profile."""
        mock_client = self._mock_scm_client(monkeypatch)
        mock_client.get_url_access_profile.return_value = {
            "id": "uap-1",
            "name": "strict-url",
            "folder": "Texas",
            "block": ["adult", "malware"],
            "alert": ["hacking"],
        }

        test_app = typer.Typer()
        test_app.command()(show_url_access_profile)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "strict-url"])

        assert result.exit_code == 0
        assert "URL Access Profile: strict-url" in result.stdout


class TestMoveCommands:
    """Test the move commands."""

    def test_move_app_exists(self):
        """Test that the move app exists."""
        assert move_app

    def test_move_commands_exist(self):
        """Test that all move commands exist."""
        assert move_security_rule_cmd
        assert move_app_override_rule_cmd
        assert move_authentication_rule_cmd
        assert move_decryption_rule_cmd

    # ------------------------------------------------------------------------------- Security Rule Move -------------------------------------------------------------------------------

    def test_move_security_rule_top(self, runner, monkeypatch):
        """Test moving a security rule to top."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called_with = {}

        def mock_move(*args, **kwargs):
            mock_called_with.update(kwargs)

        monkeypatch.setattr(scm_client, "move_security_rule", mock_move)

        test_app = typer.Typer()
        test_app.command()(move_security_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "Allow Web", "--destination", "top"],
        )

        assert result.exit_code == 0
        assert "Moved security rule" in result.stdout
        assert mock_called_with["name"] == "Allow Web"
        assert mock_called_with["destination"] == "top"

    def test_move_security_rule_bottom(self, runner, monkeypatch):
        """Test moving a security rule to bottom."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_move(*args, **kwargs):
            pass

        monkeypatch.setattr(scm_client, "move_security_rule", mock_move)

        test_app = typer.Typer()
        test_app.command()(move_security_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "Allow Web", "--destination", "bottom"],
        )

        assert result.exit_code == 0
        assert "Moved security rule" in result.stdout
        assert "bottom" in result.stdout

    def test_move_security_rule_before(self, runner, monkeypatch):
        """Test moving a security rule before a reference rule."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called_with = {}

        def mock_move(*args, **kwargs):
            mock_called_with.update(kwargs)

        monkeypatch.setattr(scm_client, "move_security_rule", mock_move)

        test_app = typer.Typer()
        test_app.command()(move_security_rule_cmd)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "Allow Web",
                "--destination",
                "before",
                "--destination-rule",
                "abc-123",
            ],
        )

        assert result.exit_code == 0
        assert mock_called_with["destination"] == "before"
        assert mock_called_with["destination_rule"] == "abc-123"

    def test_move_security_rule_after(self, runner, monkeypatch):
        """Test moving a security rule after a reference rule."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called_with = {}

        def mock_move(*args, **kwargs):
            mock_called_with.update(kwargs)

        monkeypatch.setattr(scm_client, "move_security_rule", mock_move)

        test_app = typer.Typer()
        test_app.command()(move_security_rule_cmd)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "Allow Web",
                "--destination",
                "after",
                "--destination-rule",
                "def-456",
            ],
        )

        assert result.exit_code == 0
        assert mock_called_with["destination"] == "after"
        assert mock_called_with["destination_rule"] == "def-456"

    def test_move_security_rule_before_missing_reference(self, runner, monkeypatch):
        """Test error when before destination is used without reference rule."""
        test_app = typer.Typer()
        test_app.command()(move_security_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "Allow Web", "--destination", "before"],
        )

        assert result.exit_code == 1
        assert "--destination-rule is required" in result.output

    def test_move_security_rule_after_missing_reference(self, runner, monkeypatch):
        """Test error when after destination is used without reference rule."""
        test_app = typer.Typer()
        test_app.command()(move_security_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "Allow Web", "--destination", "after"],
        )

        assert result.exit_code == 1
        assert "--destination-rule is required" in result.output

    def test_move_security_rule_error(self, runner, monkeypatch):
        """Test error handling when move fails."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_move_error(*args, **kwargs):
            raise ValueError("Rule not found")

        monkeypatch.setattr(scm_client, "move_security_rule", mock_move_error)

        test_app = typer.Typer()
        test_app.command()(move_security_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "Nonexistent", "--destination", "top"],
        )

        assert result.exit_code == 1
        assert "Error moving security rule" in result.output

    def test_move_security_rule_post_rulebase(self, runner, monkeypatch):
        """Test moving a security rule in post rulebase."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called_with = {}

        def mock_move(*args, **kwargs):
            mock_called_with.update(kwargs)

        monkeypatch.setattr(scm_client, "move_security_rule", mock_move)

        test_app = typer.Typer()
        test_app.command()(move_security_rule_cmd)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "Allow Web",
                "--destination",
                "top",
                "--rulebase",
                "post",
            ],
        )

        assert result.exit_code == 0
        assert mock_called_with["rulebase"] == "post"

    # ----------------------------------------------------------------------------- App Override Rule Move -----------------------------------------------------------------------------

    def test_move_app_override_rule_top(self, runner, monkeypatch):
        """Test moving an app override rule to top."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called_with = {}

        def mock_move(*args, **kwargs):
            mock_called_with.update(kwargs)

        monkeypatch.setattr(scm_client, "move_app_override_rule", mock_move)

        test_app = typer.Typer()
        test_app.command()(move_app_override_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "override-https", "--destination", "top"],
        )

        assert result.exit_code == 0
        assert "Moved app override rule" in result.stdout
        assert mock_called_with["name"] == "override-https"

    def test_move_app_override_rule_before_missing_reference(self, runner, monkeypatch):
        """Test error when before destination without reference rule."""
        test_app = typer.Typer()
        test_app.command()(move_app_override_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "override-https", "--destination", "before"],
        )

        assert result.exit_code == 1
        assert "--destination-rule is required" in result.output

    def test_move_app_override_rule_error(self, runner, monkeypatch):
        """Test error handling for app override rule move."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_move_error(*args, **kwargs):
            raise ValueError("Rule not found")

        monkeypatch.setattr(scm_client, "move_app_override_rule", mock_move_error)

        test_app = typer.Typer()
        test_app.command()(move_app_override_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "Nonexistent", "--destination", "top"],
        )

        assert result.exit_code == 1
        assert "Error moving app override rule" in result.output

    # ---------------------------------------------------------------------------- Authentication Rule Move ----------------------------------------------------------------------------

    def test_move_authentication_rule_bottom(self, runner, monkeypatch):
        """Test moving an authentication rule to bottom."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called_with = {}

        def mock_move(*args, **kwargs):
            mock_called_with.update(kwargs)

        monkeypatch.setattr(scm_client, "move_authentication_rule", mock_move)

        test_app = typer.Typer()
        test_app.command()(move_authentication_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "auth-rule", "--destination", "bottom"],
        )

        assert result.exit_code == 0
        assert "Moved authentication rule" in result.stdout
        assert mock_called_with["name"] == "auth-rule"

    def test_move_authentication_rule_after_missing_reference(self, runner, monkeypatch):
        """Test error when after destination without reference rule."""
        test_app = typer.Typer()
        test_app.command()(move_authentication_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "auth-rule", "--destination", "after"],
        )

        assert result.exit_code == 1
        assert "--destination-rule is required" in result.output

    def test_move_authentication_rule_error(self, runner, monkeypatch):
        """Test error handling for authentication rule move."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_move_error(*args, **kwargs):
            raise ValueError("Rule not found")

        monkeypatch.setattr(scm_client, "move_authentication_rule", mock_move_error)

        test_app = typer.Typer()
        test_app.command()(move_authentication_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "Nonexistent", "--destination", "top"],
        )

        assert result.exit_code == 1
        assert "Error moving authentication rule" in result.output

    # ------------------------------------------------------------------------------- Decryption Rule Move -------------------------------------------------------------------------------

    def test_move_decryption_rule_top(self, runner, monkeypatch):
        """Test moving a decryption rule to top."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called_with = {}

        def mock_move(*args, **kwargs):
            mock_called_with.update(kwargs)

        monkeypatch.setattr(scm_client, "move_decryption_rule", mock_move)

        test_app = typer.Typer()
        test_app.command()(move_decryption_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "decrypt-rule", "--destination", "top"],
        )

        assert result.exit_code == 0
        assert "Moved decryption rule" in result.stdout
        assert mock_called_with["name"] == "decrypt-rule"

    def test_move_decryption_rule_before_with_reference(self, runner, monkeypatch):
        """Test moving a decryption rule before a reference rule."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called_with = {}

        def mock_move(*args, **kwargs):
            mock_called_with.update(kwargs)

        monkeypatch.setattr(scm_client, "move_decryption_rule", mock_move)

        test_app = typer.Typer()
        test_app.command()(move_decryption_rule_cmd)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "decrypt-rule",
                "--destination",
                "before",
                "--destination-rule",
                "ref-uuid",
            ],
        )

        assert result.exit_code == 0
        assert mock_called_with["destination"] == "before"
        assert mock_called_with["destination_rule"] == "ref-uuid"

    def test_move_decryption_rule_before_missing_reference(self, runner, monkeypatch):
        """Test error when before destination without reference rule."""
        test_app = typer.Typer()
        test_app.command()(move_decryption_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "decrypt-rule", "--destination", "before"],
        )

        assert result.exit_code == 1
        assert "--destination-rule is required" in result.output

    def test_move_decryption_rule_error(self, runner, monkeypatch):
        """Test error handling for decryption rule move."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_move_error(*args, **kwargs):
            raise ValueError("Rule not found")

        monkeypatch.setattr(scm_client, "move_decryption_rule", mock_move_error)

        test_app = typer.Typer()
        test_app.command()(move_decryption_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "Nonexistent", "--destination", "top"],
        )

        assert result.exit_code == 1
        assert "Error moving decryption rule" in result.output

    # ---------------------------------------------------------------------------- No Location Param Tests ----------------------------------------------------------------------------

    def test_move_security_rule_no_location(self, runner, monkeypatch):
        """Test error when no location parameter is provided."""
        test_app = typer.Typer()
        test_app.command()(move_security_rule_cmd)

        result = runner.invoke(
            test_app,
            ["--name", "Allow Web", "--destination", "top"],
        )

        assert result.exit_code == 1
        assert "must be specified" in result.output

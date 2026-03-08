"""Tests for the network commands module."""

import typer  # noqa: I001
from scm_cli.commands.network import (
    delete_aggregate_interface,
    delete_app,
    delete_ike_crypto_profile,
    delete_ike_gateway,
    delete_ipsec_crypto_profile,
    delete_nat_rule,
    delete_zone,
    load_aggregate_interface,
    load_app,
    load_ike_crypto_profile,
    load_ike_gateway,
    load_ipsec_crypto_profile,
    load_nat_rule,
    load_security_zone as load_zone,
    set_aggregate_interface,
    set_app,
    set_ike_crypto_profile,
    set_ike_gateway,
    set_ipsec_crypto_profile,
    set_nat_rule,
    set_zone,
    show_aggregate_interface,
    show_ike_crypto_profile,
    show_ike_gateway,
    show_ipsec_crypto_profile,
    show_nat_rule,
)


class TestNetworkCommands:
    """Test the network commands."""

    def test_set_command_exists(self):
        """Test that the set command exists."""
        assert set_app

    def test_delete_command_exists(self):
        """Test that the delete command exists."""
        assert delete_app

    def test_load_command_exists(self):
        """Test that the load command exists."""
        assert load_app


class TestZoneCommands:
    """Test the zone commands."""

    def test_set_zone_command(self, runner, monkeypatch):
        """Test the set zone command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "zone-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "mode": kwargs.get("mode"),
                "interfaces": kwargs.get("interfaces", []),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }

        monkeypatch.setattr(scm_client, "create_zone", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_zone)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-zone",
                "--mode",
                "L3",
                "--interfaces",
                "ethernet1/1",
                "--interfaces",
                "ethernet1/2",
                "--description",
                "Test zone",
                "--tags",
                "test",
                "--tags",
                "example",
            ],
        )

        assert result.exit_code == 0
        assert "Created zone" in result.stdout
        assert "test-zone" in result.stdout
        assert "test-folder" in result.stdout

    def test_set_zone_error(self, runner, monkeypatch):
        """Test the set zone command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_zone", mock_create_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_zone)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-zone",
                "--mode",
                "L3",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating security zone" in result.stdout
        assert "Test error" in result.stdout

    def test_delete_zone_command(self, runner, monkeypatch):
        """Test the delete zone command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_zone", mock_delete)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_zone)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-zone",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted zone" in result.stdout
        assert "test-zone" in result.stdout
        assert "test-folder" in result.stdout

    def test_delete_zone_error(self, runner, monkeypatch):
        """Test the delete zone command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_zone", mock_delete_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_zone)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--folder",
                "test-folder",
                "--name",
                "test-zone",
            ],
        )

        assert result.exit_code == 1
        assert "Error deleting security zone" in result.stdout
        assert "Test error" in result.stdout

    def test_load_zone_command(self, runner, monkeypatch, mock_zones_yaml_file):
        """Test the load zone command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        created_zones = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"zone-{len(created_zones) + 1}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "mode": kwargs.get("mode"),
                "interfaces": kwargs.get("interfaces", []),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }
            created_zones.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_zone", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_zone)

        # Invoke the command
        result = runner.invoke(test_app, ["--file", str(mock_zones_yaml_file)])

        assert result.exit_code == 0
        assert "Applied zone" in result.stdout
        assert "test-zone" in result.stdout
        assert "test-folder" in result.stdout
        assert len(created_zones) == 1

    def test_load_zone_dry_run(self, runner, monkeypatch, mock_zones_yaml_file):
        """Test the load zone command with dry-run option."""
        # Mock the SCM client method to track if it gets called
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_zone", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_zone)

        # Invoke the command with dry-run
        result = runner.invoke(test_app, ["--file", str(mock_zones_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called  # Ensure the create method was not called


class TestIKECryptoProfileCommands:
    """Test the IKE crypto profile commands."""

    def test_set_ike_crypto_profile_created(self, runner, monkeypatch):
        """Test set ike-crypto-profile command creates a new profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(profile_data):
            result = profile_data.copy()
            result["id"] = "ike-12345"
            result["__action__"] = "created"
            return result

        monkeypatch.setattr(scm_client, "create_ike_crypto_profile", mock_create)
        test_app = typer.Typer()
        test_app.command()(set_ike_crypto_profile)
        result = runner.invoke(test_app, ["test-profile", "--hash", "sha256", "--dh-group", "group14", "--encryption", "aes-256-cbc", "--folder", "test-folder", "--lifetime-hours", "8"])
        assert result.exit_code == 0
        assert "Created IKE crypto profile" in result.stdout
        assert "test-profile" in result.stdout

    def test_set_ike_crypto_profile_error(self, runner, monkeypatch):
        """Test set ike-crypto-profile command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(profile_data):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_ike_crypto_profile", mock_create_error)
        test_app = typer.Typer()
        test_app.command()(set_ike_crypto_profile)
        result = runner.invoke(test_app, ["test-profile", "--hash", "sha256", "--dh-group", "group14", "--encryption", "aes-256-cbc", "--folder", "test-folder"])
        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_show_ike_crypto_profile_list(self, runner, monkeypatch):
        """Test show ike-crypto-profile command lists profiles."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(**kwargs):
            return [
                {
                    "id": "ike-1",
                    "name": "profile-1",
                    "folder": "test-folder",
                    "hash": ["sha256"],
                    "dh_group": ["group14"],
                    "encryption": ["aes-256-cbc"],
                    "lifetime": {"hours": 8},
                    "authentication_multiple": 0,
                }
            ]

        monkeypatch.setattr(scm_client, "list_ike_crypto_profiles", mock_list)
        test_app = typer.Typer()
        test_app.command()(show_ike_crypto_profile)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "profile-1" in result.stdout

    def test_show_ike_crypto_profile_specific(self, runner, monkeypatch):
        """Test show ike-crypto-profile command shows a specific profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(**kwargs):
            return {
                "id": "ike-1",
                "name": "profile-1",
                "folder": "test-folder",
                "hash": ["sha256", "sha384"],
                "dh_group": ["group14"],
                "encryption": ["aes-256-cbc"],
                "lifetime": {"hours": 8},
                "authentication_multiple": 3,
            }

        monkeypatch.setattr(scm_client, "get_ike_crypto_profile", mock_get)
        test_app = typer.Typer()
        test_app.command()(show_ike_crypto_profile)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "profile-1"])
        assert result.exit_code == 0
        assert "profile-1" in result.stdout
        assert "sha256" in result.stdout

    def test_delete_ike_crypto_profile_command(self, runner, monkeypatch):
        """Test delete ike-crypto-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(**kwargs):
            return {"id": "ike-1", "name": "test-profile", "folder": "test-folder"}

        def mock_delete(**kwargs):
            return None

        monkeypatch.setattr(scm_client, "get_ike_crypto_profile", mock_get)
        monkeypatch.setattr(scm_client, "delete_ike_crypto_profile", mock_delete)
        test_app = typer.Typer()
        test_app.command()(delete_ike_crypto_profile)
        result = runner.invoke(test_app, ["test-profile", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted IKE crypto profile" in result.stdout

    def test_load_ike_crypto_profile_command(self, runner, monkeypatch, tmp_path):
        """Test load ike-crypto-profile command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {
            "ike_crypto_profiles": [{"name": "test-profile", "folder": "test-folder", "hash": ["sha256"], "dh_group": ["group14"], "encryption": ["aes-256-cbc"], "lifetime_hours": 8}]
        }
        yaml_file = tmp_path / "ike-profiles.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        def mock_create(profile_data):
            result = profile_data.copy()
            result["id"] = "ike-12345"
            result["__action__"] = "created"
            return result

        monkeypatch.setattr(scm_client, "create_ike_crypto_profile", mock_create)
        test_app = typer.Typer()
        test_app.command()(load_ike_crypto_profile)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created IKE crypto profile" in result.stdout
        assert "test-profile" in result.stdout


class TestIKEGatewayCommands:
    """Test the IKE gateway commands."""

    def test_set_ike_gateway_created(self, runner, monkeypatch):
        """Test set ike-gateway command creates a new gateway."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(gateway_data):
            result = gateway_data.copy()
            result["id"] = "ike-gw-12345"
            result["__action__"] = "created"
            return result

        monkeypatch.setattr(scm_client, "create_ike_gateway", mock_create)
        test_app = typer.Typer()
        test_app.command()(set_ike_gateway)
        result = runner.invoke(
            test_app,
            [
                "test-gw",
                "--folder",
                "test-folder",
                "--pre-shared-key",
                "my-secret",
                "--peer-address-ip",
                "203.0.113.1",
                "--protocol-version",
                "ikev2-preferred",
                "--ike-crypto-profile",
                "default",
            ],
        )
        assert result.exit_code == 0
        assert "Created IKE gateway" in result.stdout
        assert "test-gw" in result.stdout

    def test_set_ike_gateway_error(self, runner, monkeypatch):
        """Test set ike-gateway command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(gateway_data):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_ike_gateway", mock_create_error)
        test_app = typer.Typer()
        test_app.command()(set_ike_gateway)
        result = runner.invoke(
            test_app,
            [
                "test-gw",
                "--folder",
                "test-folder",
                "--pre-shared-key",
                "my-secret",
                "--peer-address-ip",
                "203.0.113.1",
            ],
        )
        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_set_ike_gateway_missing_auth(self, runner, monkeypatch):
        """Test set ike-gateway command requires authentication."""
        test_app = typer.Typer()
        test_app.command()(set_ike_gateway)
        result = runner.invoke(
            test_app,
            [
                "test-gw",
                "--folder",
                "test-folder",
                "--peer-address-ip",
                "203.0.113.1",
            ],
        )
        assert result.exit_code == 1

    def test_set_ike_gateway_missing_peer_address(self, runner, monkeypatch):
        """Test set ike-gateway command requires peer address."""
        test_app = typer.Typer()
        test_app.command()(set_ike_gateway)
        result = runner.invoke(
            test_app,
            [
                "test-gw",
                "--folder",
                "test-folder",
                "--pre-shared-key",
                "my-secret",
            ],
        )
        assert result.exit_code == 1

    def test_show_ike_gateway_list(self, runner, monkeypatch):
        """Test show ike-gateway command lists gateways."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(**kwargs):
            return [
                {
                    "id": "ike-gw-1",
                    "name": "gw-site-a",
                    "folder": "test-folder",
                    "authentication": {"pre_shared_key": {"key": "k"}},
                    "peer_address": {"ip": "203.0.113.1"},
                    "protocol": {"version": "ikev2-preferred"},
                },
            ]

        monkeypatch.setattr(scm_client, "list_ike_gateways", mock_list)
        test_app = typer.Typer()
        test_app.command()(show_ike_gateway)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "gw-site-a" in result.stdout

    def test_show_ike_gateway_specific(self, runner, monkeypatch):
        """Test show ike-gateway command shows a specific gateway."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(**kwargs):
            return {
                "id": "ike-gw-1",
                "name": "gw-site-a",
                "folder": "test-folder",
                "authentication": {"pre_shared_key": {"key": "k"}},
                "peer_address": {"ip": "203.0.113.1"},
                "protocol": {"version": "ikev2-preferred", "ikev2": {"ike_crypto_profile": "default"}},
                "peer_id": {"type": "fqdn", "id": "peer.example.com"},
                "protocol_common": {"nat_traversal": {"enable": True}},
            }

        monkeypatch.setattr(scm_client, "get_ike_gateway", mock_get)
        test_app = typer.Typer()
        test_app.command()(show_ike_gateway)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "gw-site-a"])
        assert result.exit_code == 0
        assert "gw-site-a" in result.stdout
        assert "203.0.113.1" in result.stdout
        assert "Pre-Shared Key" in result.stdout

    def test_delete_ike_gateway_command(self, runner, monkeypatch):
        """Test delete ike-gateway command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(**kwargs):
            return {"id": "ike-gw-1", "name": "test-gw", "folder": "test-folder"}

        def mock_delete(**kwargs):
            return None

        monkeypatch.setattr(scm_client, "get_ike_gateway", mock_get)
        monkeypatch.setattr(scm_client, "delete_ike_gateway", mock_delete)
        test_app = typer.Typer()
        test_app.command()(delete_ike_gateway)
        result = runner.invoke(test_app, ["test-gw", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted IKE gateway" in result.stdout

    def test_load_ike_gateway_command(self, runner, monkeypatch, tmp_path):
        """Test load ike-gateway command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {
            "ike_gateways": [
                {
                    "name": "test-gw",
                    "folder": "test-folder",
                    "authentication": {"pre_shared_key": {"key": "secret"}},
                    "peer_address": {"ip": "203.0.113.1"},
                    "protocol": {"version": "ikev2-preferred", "ikev1": {"ike_crypto_profile": "default"}, "ikev2": {"ike_crypto_profile": "default"}},
                }
            ]
        }
        yaml_file = tmp_path / "ike-gateways.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        def mock_create(gateway_data):
            result = gateway_data.copy()
            result["id"] = "ike-gw-12345"
            result["__action__"] = "created"
            return result

        monkeypatch.setattr(scm_client, "create_ike_gateway", mock_create)
        test_app = typer.Typer()
        test_app.command()(load_ike_gateway)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created IKE gateway" in result.stdout
        assert "test-gw" in result.stdout

    def test_load_ike_gateway_dry_run(self, runner, monkeypatch, tmp_path):
        """Test load ike-gateway command with dry-run."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {
            "ike_gateways": [
                {
                    "name": "test-gw",
                    "folder": "test-folder",
                    "authentication": {"pre_shared_key": {"key": "secret"}},
                    "peer_address": {"ip": "203.0.113.1"},
                    "protocol": {"version": "ikev2", "ikev2": {"ike_crypto_profile": "default"}},
                }
            ]
        }
        yaml_file = tmp_path / "ike-gateways.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        mock_called = False

        def mock_create(gateway_data):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_ike_gateway", mock_create)
        test_app = typer.Typer()
        test_app.command()(load_ike_gateway)
        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called


class TestIPsecCryptoProfileCommands:
    """Test the IPsec crypto profile commands."""

    def test_set_ipsec_crypto_profile_command(self, runner, monkeypatch):
        """Test the set ipsec-crypto-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "ipsec-crypto-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "esp": {
                    "encryption": kwargs.get("esp_encryption", ["aes-256-cbc"]),
                    "authentication": kwargs.get("esp_authentication", ["sha256"]),
                },
                "dh_group": kwargs.get("dh_group", "group14"),
                "lifetime": kwargs.get("lifetime", {"hours": 1}),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_ipsec_crypto_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_ipsec_crypto_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-profile",
                "--esp-encryption",
                "aes-256-cbc",
                "--esp-authentication",
                "sha256",
                "--dh-group",
                "group14",
            ],
        )

        assert result.exit_code == 0
        assert "test-profile" in result.stdout
        assert "created" in result.stdout

    def test_set_ipsec_crypto_profile_error(self, runner, monkeypatch):
        """Test the set ipsec-crypto-profile command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_ipsec_crypto_profile", mock_create_error)

        test_app = typer.Typer()
        test_app.command()(set_ipsec_crypto_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-profile",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating IPsec crypto profile" in result.stdout

    def test_delete_ipsec_crypto_profile_command(self, runner, monkeypatch):
        """Test the delete ipsec-crypto-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_ipsec_crypto_profile", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_ipsec_crypto_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-profile",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted IPsec crypto profile" in result.stdout
        assert "test-profile" in result.stdout

    def test_show_ipsec_crypto_profile_single(self, runner, monkeypatch):
        """Test the show ipsec-crypto-profile command for a single profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "ipsec-crypto-12345",
                "name": "test-profile",
                "folder": "Texas",
                "esp": {
                    "encryption": ["aes-256-cbc"],
                    "authentication": ["sha256"],
                },
                "dh_group": "group14",
                "lifetime": {"hours": 1},
            }

        monkeypatch.setattr(scm_client, "get_ipsec_crypto_profile", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_ipsec_crypto_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-profile",
            ],
        )

        assert result.exit_code == 0
        assert "test-profile" in result.stdout
        assert "aes-256-cbc" in result.stdout
        assert "group14" in result.stdout

    def test_show_ipsec_crypto_profile_list(self, runner, monkeypatch):
        """Test the show ipsec-crypto-profile command for listing."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "ipsec-crypto-1",
                    "name": "profile-1",
                    "folder": "Texas",
                    "esp": {
                        "encryption": ["aes-256-cbc"],
                        "authentication": ["sha256"],
                    },
                    "dh_group": "group14",
                    "lifetime": {"hours": 1},
                },
                {
                    "id": "ipsec-crypto-2",
                    "name": "profile-2",
                    "folder": "Texas",
                    "esp": {
                        "encryption": ["aes-128-cbc"],
                        "authentication": ["sha1"],
                    },
                    "dh_group": "group2",
                    "lifetime": {"seconds": 3600},
                },
            ]

        monkeypatch.setattr(scm_client, "list_ipsec_crypto_profiles", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_ipsec_crypto_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
            ],
        )

        assert result.exit_code == 0
        assert "profile-1" in result.stdout
        assert "profile-2" in result.stdout

    def test_load_ipsec_crypto_profile_command(self, runner, monkeypatch, mock_ipsec_crypto_profiles_yaml_file):
        """Test the load ipsec-crypto-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        created_profiles = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"ipsec-crypto-{len(created_profiles) + 1}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "esp": {
                    "encryption": kwargs.get("esp_encryption", ["aes-256-cbc"]),
                    "authentication": kwargs.get("esp_authentication", ["sha256"]),
                },
                "dh_group": kwargs.get("dh_group", "group14"),
                "lifetime": kwargs.get("lifetime", {"hours": 1}),
                "__action__": "created",
            }
            created_profiles.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_ipsec_crypto_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_ipsec_crypto_profile)

        result = runner.invoke(test_app, ["--file", str(mock_ipsec_crypto_profiles_yaml_file)])

        assert result.exit_code == 0
        assert "test-ipsec-profile" in result.stdout
        assert "created" in result.stdout
        assert len(created_profiles) == 1

    def test_load_ipsec_crypto_profile_dry_run(self, runner, monkeypatch, mock_ipsec_crypto_profiles_yaml_file):
        """Test the load ipsec-crypto-profile command with dry-run."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_ipsec_crypto_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_ipsec_crypto_profile)

        result = runner.invoke(test_app, ["--file", str(mock_ipsec_crypto_profiles_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called


class TestNATRuleCommands:
    """Test the NAT rule commands."""

    def test_set_nat_rule_command(self, runner, monkeypatch):
        """Test the set nat-rule command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "nat-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "from_": kwargs.get("from_zones", ["any"]),
                "to_": kwargs.get("to_zones", ["any"]),
                "source": kwargs.get("source", ["any"]),
                "destination": kwargs.get("destination", ["any"]),
                "service": kwargs.get("service", "any"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_nat_rule", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_nat_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "outbound-nat",
                "--from-zone",
                "trust",
                "--to-zone",
                "untrust",
            ],
        )

        assert result.exit_code == 0
        assert "Created NAT rule" in result.stdout
        assert "outbound-nat" in result.stdout

    def test_set_nat_rule_with_translation(self, runner, monkeypatch):
        """Test the set nat-rule command with source translation."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "nat-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "source_translation": kwargs.get("source_translation"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_nat_rule", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_nat_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "outbound-nat",
                "--source-translation",
                '{"dynamic_ip_and_port": {"type": "dynamic_ip_and_port", "translated_address": ["10.0.0.1"]}}',
            ],
        )

        assert result.exit_code == 0
        assert "Created NAT rule" in result.stdout

    def test_set_nat_rule_error(self, runner, monkeypatch):
        """Test the set nat-rule command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_nat_rule", mock_create_error)

        test_app = typer.Typer()
        test_app.command()(set_nat_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "outbound-nat",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating NAT rule" in result.stdout

    def test_delete_nat_rule_command(self, runner, monkeypatch):
        """Test the delete nat-rule command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_nat_rule", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_nat_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "outbound-nat",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted NAT rule" in result.stdout
        assert "outbound-nat" in result.stdout

    def test_delete_nat_rule_error(self, runner, monkeypatch):
        """Test the delete nat-rule command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_nat_rule", mock_delete_error)

        test_app = typer.Typer()
        test_app.command()(delete_nat_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "outbound-nat",
            ],
        )

        assert result.exit_code == 1
        assert "Error deleting NAT rule" in result.stdout

    def test_show_nat_rule_single(self, runner, monkeypatch):
        """Test showing a single NAT rule."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "nat-12345",
                "folder": "Texas",
                "name": "outbound-nat",
                "nat_type": "ipv4",
                "from_": ["trust"],
                "to_": ["untrust"],
                "source": ["any"],
                "destination": ["any"],
                "service": "any",
            }

        monkeypatch.setattr(scm_client, "get_nat_rule", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_nat_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "outbound-nat",
            ],
        )

        assert result.exit_code == 0
        assert "outbound-nat" in result.stdout
        assert "trust" in result.stdout

    def test_show_nat_rule_list(self, runner, monkeypatch):
        """Test listing NAT rules."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "nat-1",
                    "folder": "Texas",
                    "name": "outbound-nat",
                    "from_": ["trust"],
                    "to_": ["untrust"],
                    "source": ["any"],
                    "destination": ["any"],
                    "service": "any",
                },
                {
                    "id": "nat-2",
                    "folder": "Texas",
                    "name": "inbound-web",
                    "from_": ["untrust"],
                    "to_": ["trust"],
                    "source": ["any"],
                    "destination": ["203.0.113.10"],
                    "service": "service-http",
                },
            ]

        monkeypatch.setattr(scm_client, "list_nat_rules", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_nat_rule)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
            ],
        )

        assert result.exit_code == 0
        assert "outbound-nat" in result.stdout
        assert "inbound-web" in result.stdout

    def test_load_nat_rule_command(self, runner, monkeypatch, mock_nat_rules_yaml_file):
        """Test the load nat-rule command."""
        from scm_cli.utils.sdk_client import scm_client

        created_rules = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"nat-{len(created_rules) + 1}",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "created",
            }
            created_rules.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_nat_rule", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_nat_rule)

        result = runner.invoke(test_app, ["--file", str(mock_nat_rules_yaml_file)])

        assert result.exit_code == 0
        assert "Successfully processed" in result.stdout
        assert len(created_rules) == 1

    def test_load_nat_rule_dry_run(self, runner, monkeypatch, mock_nat_rules_yaml_file):
        """Test the load nat-rule command with dry-run option."""
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_nat_rule", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_nat_rule)

        result = runner.invoke(test_app, ["--file", str(mock_nat_rules_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called


class TestAggregateInterfaceCommands:
    """Test the aggregate interface commands."""

    def test_set_aggregate_interface_created(self, runner, monkeypatch):
        """Test set aggregate-interface command creates a new interface."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(iface_data):
            result = iface_data.copy()
            result["id"] = "ae-12345"
            result["__action__"] = "created"
            return result

        monkeypatch.setattr(scm_client, "create_aggregate_interface", mock_create)
        test_app = typer.Typer()
        test_app.command()(set_aggregate_interface)
        result = runner.invoke(
            test_app,
            [
                "ae1",
                "--folder",
                "test-folder",
                "--layer3-json",
                '{"mtu": 1500}',
            ],
        )
        assert result.exit_code == 0
        assert "Created aggregate interface" in result.stdout
        assert "ae1" in result.stdout

    def test_set_aggregate_interface_error(self, runner, monkeypatch):
        """Test set aggregate-interface command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(iface_data):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_aggregate_interface", mock_create_error)
        test_app = typer.Typer()
        test_app.command()(set_aggregate_interface)
        result = runner.invoke(
            test_app,
            [
                "ae1",
                "--folder",
                "test-folder",
                "--layer3-json",
                '{"mtu": 1500}',
            ],
        )
        assert result.exit_code == 1
        assert "Error" in result.stdout

    def test_show_aggregate_interface_list(self, runner, monkeypatch):
        """Test show aggregate-interface command lists interfaces."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(**kwargs):
            return [
                {
                    "id": "ae-1",
                    "name": "ae1",
                    "folder": "test-folder",
                    "layer3": {"mtu": 1500},
                },
            ]

        monkeypatch.setattr(scm_client, "list_aggregate_interfaces", mock_list)
        test_app = typer.Typer()
        test_app.command()(show_aggregate_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "ae1" in result.stdout

    def test_show_aggregate_interface_specific(self, runner, monkeypatch):
        """Test show aggregate-interface command shows a specific interface."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(**kwargs):
            return {
                "id": "ae-1",
                "name": "ae1",
                "folder": "test-folder",
                "comment": "test interface",
                "layer3": {"mtu": 9000, "ip": [{"name": "10.0.0.1/24"}]},
            }

        monkeypatch.setattr(scm_client, "get_aggregate_interface", mock_get)
        test_app = typer.Typer()
        test_app.command()(show_aggregate_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "ae1"])
        assert result.exit_code == 0
        assert "ae1" in result.stdout
        assert "9000" in result.stdout

    def test_delete_aggregate_interface_command(self, runner, monkeypatch):
        """Test delete aggregate-interface command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(**kwargs):
            return {"id": "ae-1", "name": "ae1", "folder": "test-folder"}

        def mock_delete(**kwargs):
            return None

        monkeypatch.setattr(scm_client, "get_aggregate_interface", mock_get)
        monkeypatch.setattr(scm_client, "delete_aggregate_interface", mock_delete)
        test_app = typer.Typer()
        test_app.command()(delete_aggregate_interface)
        result = runner.invoke(test_app, ["ae1", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted aggregate interface" in result.stdout

    def test_load_aggregate_interface_command(self, runner, monkeypatch, tmp_path):
        """Test load aggregate-interface command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {
            "aggregate_interfaces": [
                {
                    "name": "ae1",
                    "folder": "test-folder",
                    "layer3": {"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]},
                }
            ]
        }
        yaml_file = tmp_path / "aggregate-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        def mock_create(iface_data):
            result = iface_data.copy()
            result["id"] = "ae-12345"
            result["__action__"] = "created"
            return result

        monkeypatch.setattr(scm_client, "create_aggregate_interface", mock_create)
        test_app = typer.Typer()
        test_app.command()(load_aggregate_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created aggregate interface" in result.stdout
        assert "ae1" in result.stdout

    def test_load_aggregate_interface_dry_run(self, runner, monkeypatch, tmp_path):
        """Test load aggregate-interface command with dry-run."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {
            "aggregate_interfaces": [
                {
                    "name": "ae1",
                    "folder": "test-folder",
                    "layer3": {"mtu": 1500},
                }
            ]
        }
        yaml_file = tmp_path / "aggregate-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        mock_called = False

        def mock_create(iface_data):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_aggregate_interface", mock_create)
        test_app = typer.Typer()
        test_app.command()(load_aggregate_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout
        assert not mock_called

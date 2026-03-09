"""Tests for the network commands module."""

import typer  # noqa: I001
from scm_cli.commands.network import (
    delete_aggregate_interface,
    delete_app,
    delete_bgp_address_family_profile,
    delete_bgp_auth_profile,
    delete_bgp_filtering_profile,
    delete_bgp_redistribution_profile,
    delete_bgp_route_map,
    delete_bgp_route_map_redistribution,
    delete_dhcp_interface,
    delete_dns_proxy,
    delete_ethernet_interface,
    delete_ike_crypto_profile,
    delete_ike_gateway,
    delete_ipsec_crypto_profile,
    delete_layer2_subinterface,
    delete_layer3_subinterface,
    delete_loopback_interface,
    delete_nat_rule,
    delete_ospf_auth_profile,
    delete_pbf_rule,
    delete_qos_profile,
    delete_qos_rule,
    delete_route_access_list,
    delete_route_prefix_list,
    delete_tunnel_interface,
    delete_vlan_interface,
    delete_zone,
    load_aggregate_interface,
    load_app,
    load_bgp_address_family_profile,
    load_bgp_auth_profile,
    load_bgp_filtering_profile,
    load_bgp_route_map,
    load_bgp_route_map_redistribution,
    load_dhcp_interface,
    load_dns_proxy,
    load_ethernet_interface,
    load_ike_crypto_profile,
    load_ike_gateway,
    load_ipsec_crypto_profile,
    load_layer2_subinterface,
    load_layer3_subinterface,
    load_loopback_interface,
    load_nat_rule,
    load_ospf_auth_profile,
    load_pbf_rule,
    load_qos_profile,
    load_qos_rule,
    load_route_access_list,
    load_route_prefix_list,
    load_security_zone as load_zone,
    load_tunnel_interface,
    load_vlan_interface,
    set_aggregate_interface,
    set_app,
    set_bgp_address_family_profile,
    set_bgp_auth_profile,
    set_bgp_filtering_profile,
    set_bgp_redistribution_profile,
    set_bgp_route_map,
    set_bgp_route_map_redistribution,
    set_dhcp_interface,
    set_dns_proxy,
    set_ethernet_interface,
    set_ike_crypto_profile,
    set_ike_gateway,
    set_ipsec_crypto_profile,
    set_layer2_subinterface,
    set_layer3_subinterface,
    set_loopback_interface,
    set_nat_rule,
    set_ospf_auth_profile,
    set_pbf_rule,
    set_qos_profile,
    set_qos_rule,
    set_route_access_list,
    set_route_prefix_list,
    set_tunnel_interface,
    set_vlan_interface,
    set_zone,
    show_aggregate_interface,
    show_bgp_address_family_profile,
    show_bgp_auth_profile,
    show_bgp_filtering_profile,
    show_bgp_redistribution_profile,
    show_bgp_route_map,
    show_bgp_route_map_redistribution,
    show_dhcp_interface,
    show_dns_proxy,
    show_ethernet_interface,
    show_ike_crypto_profile,
    show_ike_gateway,
    show_ipsec_crypto_profile,
    show_layer2_subinterface,
    show_layer3_subinterface,
    show_loopback_interface,
    show_nat_rule,
    show_ospf_auth_profile,
    show_pbf_rule,
    show_qos_profile,
    show_qos_rule,
    show_route_access_list,
    show_route_prefix_list,
    show_tunnel_interface,
    show_vlan_interface,
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
                "layer3",
                "--interfaces",
                "ethernet1/1",
                "--interfaces",
                "ethernet1/2",
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
                "layer3",
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


class TestDhcpInterfaceCommands:
    """Test the DHCP interface commands."""

    def test_set_dhcp_interface_created(self, runner, monkeypatch):
        """Test set dhcp-interface command creates a new interface."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(iface_data):
            result = iface_data.copy()
            result["id"] = "dhcp-12345"
            result["__action__"] = "created"
            return result

        monkeypatch.setattr(scm_client, "create_dhcp_interface", mock_create)
        test_app = typer.Typer()
        test_app.command()(set_dhcp_interface)
        result = runner.invoke(test_app, ["ethernet1/1", "--folder", "test-folder", "--server-json", '{"mode": "auto"}'])
        assert result.exit_code == 0
        assert "Created DHCP interface" in result.stdout

    def test_set_dhcp_interface_error(self, runner, monkeypatch):
        """Test set dhcp-interface command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_dhcp_interface", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_dhcp_interface)
        result = runner.invoke(test_app, ["ethernet1/1", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_dhcp_interface_list(self, runner, monkeypatch):
        """Test show dhcp-interface command lists interfaces."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_dhcp_interfaces", lambda **kwargs: [{"id": "dhcp-1", "name": "ethernet1/1", "folder": "test-folder", "server": {"mode": "auto"}}])
        test_app = typer.Typer()
        test_app.command()(show_dhcp_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "ethernet1/1" in result.stdout

    def test_show_dhcp_interface_specific(self, runner, monkeypatch):
        """Test show dhcp-interface command shows a specific interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_dhcp_interface", lambda **kwargs: {"id": "dhcp-1", "name": "ethernet1/1", "folder": "test-folder", "server": {"mode": "auto"}})
        test_app = typer.Typer()
        test_app.command()(show_dhcp_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "ethernet1/1"])
        assert result.exit_code == 0
        assert "ethernet1/1" in result.stdout

    def test_delete_dhcp_interface_command(self, runner, monkeypatch):
        """Test delete dhcp-interface command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_dhcp_interface", lambda **kwargs: {"id": "dhcp-1", "name": "ethernet1/1", "folder": "test-folder"})
        monkeypatch.setattr(scm_client, "delete_dhcp_interface", lambda **kwargs: None)
        test_app = typer.Typer()
        test_app.command()(delete_dhcp_interface)
        result = runner.invoke(test_app, ["ethernet1/1", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted DHCP interface" in result.stdout

    def test_load_dhcp_interface_command(self, runner, monkeypatch, tmp_path):
        """Test load dhcp-interface command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"dhcp_interfaces": [{"name": "ethernet1/1", "folder": "test-folder", "server": {"mode": "auto"}}]}
        yaml_file = tmp_path / "dhcp-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        monkeypatch.setattr(scm_client, "create_dhcp_interface", lambda d: {**d, "id": "dhcp-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_dhcp_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created DHCP interface" in result.stdout

    def test_load_dhcp_interface_dry_run(self, runner, monkeypatch, tmp_path):
        """Test load dhcp-interface command with dry-run."""
        import yaml

        yaml_data = {"dhcp_interfaces": [{"name": "ethernet1/1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "dhcp-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        test_app = typer.Typer()
        test_app.command()(load_dhcp_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout


class TestEthernetInterfaceCommands:
    """Test the ethernet interface commands."""

    def test_set_ethernet_interface_created(self, runner, monkeypatch):
        """Test set ethernet-interface command creates a new interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_ethernet_interface", lambda d: {**d, "id": "eth-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_ethernet_interface)
        result = runner.invoke(test_app, ["$eth1", "--folder", "test-folder", "--layer3-json", '{"mtu": 1500}'])
        assert result.exit_code == 0
        assert "Created ethernet interface" in result.stdout

    def test_set_ethernet_interface_error(self, runner, monkeypatch):
        """Test set ethernet-interface command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_ethernet_interface", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_ethernet_interface)
        result = runner.invoke(test_app, ["$eth1", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_ethernet_interface_list(self, runner, monkeypatch):
        """Test show ethernet-interface command lists interfaces."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_ethernet_interfaces", lambda **kwargs: [{"id": "eth-1", "name": "$eth1", "folder": "test-folder", "layer3": {"mtu": 1500}}])
        test_app = typer.Typer()
        test_app.command()(show_ethernet_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "$eth1" in result.stdout

    def test_show_ethernet_interface_specific(self, runner, monkeypatch):
        """Test show ethernet-interface command shows a specific interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(
            scm_client, "get_ethernet_interface", lambda **kwargs: {"id": "eth-1", "name": "$eth1", "folder": "test-folder", "layer3": {"mtu": 9000, "ip": [{"name": "10.0.0.1/24"}]}}
        )
        test_app = typer.Typer()
        test_app.command()(show_ethernet_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "$eth1"])
        assert result.exit_code == 0
        assert "$eth1" in result.stdout
        assert "9000" in result.stdout

    def test_delete_ethernet_interface_command(self, runner, monkeypatch):
        """Test delete ethernet-interface command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_ethernet_interface", lambda **kwargs: {"id": "eth-1", "name": "$eth1", "folder": "test-folder"})
        monkeypatch.setattr(scm_client, "delete_ethernet_interface", lambda **kwargs: None)
        test_app = typer.Typer()
        test_app.command()(delete_ethernet_interface)
        result = runner.invoke(test_app, ["$eth1", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted ethernet interface" in result.stdout

    def test_load_ethernet_interface_command(self, runner, monkeypatch, tmp_path):
        """Test load ethernet-interface command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"ethernet_interfaces": [{"name": "$eth1", "folder": "test-folder", "layer3": {"mtu": 1500}}]}
        yaml_file = tmp_path / "ethernet-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        monkeypatch.setattr(scm_client, "create_ethernet_interface", lambda d: {**d, "id": "eth-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_ethernet_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created ethernet interface" in result.stdout

    def test_load_ethernet_interface_dry_run(self, runner, monkeypatch, tmp_path):
        """Test load ethernet-interface command with dry-run."""
        import yaml

        yaml_data = {"ethernet_interfaces": [{"name": "$eth1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "ethernet-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        test_app = typer.Typer()
        test_app.command()(load_ethernet_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout


class TestLayer2SubinterfaceCommands:
    """Test the layer2 subinterface commands."""

    def test_set_layer2_subinterface_created(self, runner, monkeypatch):
        """Test set layer2-subinterface command creates a new interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_layer2_subinterface", lambda d: {**d, "id": "l2sub-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_layer2_subinterface)
        result = runner.invoke(test_app, ["ethernet1/1.100", "--folder", "test-folder", "--vlan-tag", "100"])
        assert result.exit_code == 0
        assert "Created layer2 subinterface" in result.stdout

    def test_set_layer2_subinterface_error(self, runner, monkeypatch):
        """Test set layer2-subinterface command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_layer2_subinterface", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_layer2_subinterface)
        result = runner.invoke(test_app, ["ethernet1/1.100", "--folder", "test-folder", "--vlan-tag", "100"])
        assert result.exit_code == 1

    def test_show_layer2_subinterface_list(self, runner, monkeypatch):
        """Test show layer2-subinterface command lists interfaces."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_layer2_subinterfaces", lambda **kwargs: [{"id": "l2-1", "name": "ethernet1/1.100", "folder": "test-folder", "vlan_tag": "100"}])
        test_app = typer.Typer()
        test_app.command()(show_layer2_subinterface)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "ethernet1/1.100" in result.stdout

    def test_show_layer2_subinterface_specific(self, runner, monkeypatch):
        """Test show layer2-subinterface command shows a specific interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(
            scm_client, "get_layer2_subinterface", lambda **kwargs: {"id": "l2-1", "name": "ethernet1/1.100", "folder": "test-folder", "vlan_tag": "100", "parent_interface": "ethernet1/1"}
        )
        test_app = typer.Typer()
        test_app.command()(show_layer2_subinterface)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "ethernet1/1.100"])
        assert result.exit_code == 0
        assert "ethernet1/1.100" in result.stdout

    def test_delete_layer2_subinterface_command(self, runner, monkeypatch):
        """Test delete layer2-subinterface command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_layer2_subinterface", lambda **kwargs: {"id": "l2-1", "name": "ethernet1/1.100", "folder": "test-folder"})
        monkeypatch.setattr(scm_client, "delete_layer2_subinterface", lambda **kwargs: None)
        test_app = typer.Typer()
        test_app.command()(delete_layer2_subinterface)
        result = runner.invoke(test_app, ["ethernet1/1.100", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted layer2 subinterface" in result.stdout

    def test_load_layer2_subinterface_command(self, runner, monkeypatch, tmp_path):
        """Test load layer2-subinterface command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"layer2_subinterfaces": [{"name": "ethernet1/1.100", "folder": "test-folder", "vlan_tag": "100"}]}
        yaml_file = tmp_path / "l2-subinterfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        monkeypatch.setattr(scm_client, "create_layer2_subinterface", lambda d: {**d, "id": "l2sub-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_layer2_subinterface)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created layer2 subinterface" in result.stdout

    def test_load_layer2_subinterface_dry_run(self, runner, monkeypatch, tmp_path):
        """Test load layer2-subinterface command with dry-run."""
        import yaml

        yaml_data = {"layer2_subinterfaces": [{"name": "ethernet1/1.100", "folder": "test-folder", "vlan_tag": "100"}]}
        yaml_file = tmp_path / "l2-subinterfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        test_app = typer.Typer()
        test_app.command()(load_layer2_subinterface)
        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout


class TestLayer3SubinterfaceCommands:
    """Test the layer3 subinterface commands."""

    def test_set_layer3_subinterface_created(self, runner, monkeypatch):
        """Test set layer3-subinterface command creates a new interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_layer3_subinterface", lambda d: {**d, "id": "l3sub-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_layer3_subinterface)
        result = runner.invoke(test_app, ["ethernet1/1.100", "--folder", "test-folder", "--tag", "100", "--mtu", "1500"])
        assert result.exit_code == 0
        assert "Created layer3 subinterface" in result.stdout

    def test_set_layer3_subinterface_error(self, runner, monkeypatch):
        """Test set layer3-subinterface command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_layer3_subinterface", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_layer3_subinterface)
        result = runner.invoke(test_app, ["ethernet1/1.100", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_layer3_subinterface_list(self, runner, monkeypatch):
        """Test show layer3-subinterface command lists interfaces."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_layer3_subinterfaces", lambda **kwargs: [{"id": "l3-1", "name": "ethernet1/1.100", "folder": "test-folder", "tag": 100, "mtu": 1500}])
        test_app = typer.Typer()
        test_app.command()(show_layer3_subinterface)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "ethernet1/1.100" in result.stdout

    def test_show_layer3_subinterface_specific(self, runner, monkeypatch):
        """Test show layer3-subinterface command shows a specific interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(
            scm_client, "get_layer3_subinterface", lambda **kwargs: {"id": "l3-1", "name": "ethernet1/1.100", "folder": "test-folder", "tag": 100, "mtu": 9000, "ip": [{"name": "10.0.1.1/24"}]}
        )
        test_app = typer.Typer()
        test_app.command()(show_layer3_subinterface)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "ethernet1/1.100"])
        assert result.exit_code == 0
        assert "ethernet1/1.100" in result.stdout
        assert "9000" in result.stdout

    def test_delete_layer3_subinterface_command(self, runner, monkeypatch):
        """Test delete layer3-subinterface command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_layer3_subinterface", lambda **kwargs: {"id": "l3-1", "name": "ethernet1/1.100", "folder": "test-folder"})
        monkeypatch.setattr(scm_client, "delete_layer3_subinterface", lambda **kwargs: None)
        test_app = typer.Typer()
        test_app.command()(delete_layer3_subinterface)
        result = runner.invoke(test_app, ["ethernet1/1.100", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted layer3 subinterface" in result.stdout

    def test_load_layer3_subinterface_command(self, runner, monkeypatch, tmp_path):
        """Test load layer3-subinterface command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"layer3_subinterfaces": [{"name": "ethernet1/1.100", "folder": "test-folder", "tag": 100, "ip": [{"name": "10.0.1.1/24"}]}]}
        yaml_file = tmp_path / "l3-subinterfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        monkeypatch.setattr(scm_client, "create_layer3_subinterface", lambda d: {**d, "id": "l3sub-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_layer3_subinterface)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created layer3 subinterface" in result.stdout

    def test_load_layer3_subinterface_dry_run(self, runner, monkeypatch, tmp_path):
        """Test load layer3-subinterface command with dry-run."""
        import yaml

        yaml_data = {"layer3_subinterfaces": [{"name": "ethernet1/1.100", "folder": "test-folder"}]}
        yaml_file = tmp_path / "l3-subinterfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        test_app = typer.Typer()
        test_app.command()(load_layer3_subinterface)
        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout


class TestLoopbackInterfaceCommands:
    """Test the loopback interface commands."""

    def test_set_loopback_interface_created(self, runner, monkeypatch):
        """Test set loopback-interface command creates a new interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_loopback_interface", lambda d: {**d, "id": "lo-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_loopback_interface)
        result = runner.invoke(test_app, ["$lo1", "--folder", "test-folder", "--ip-json", '[{"name": "10.0.0.1/32"}]'])
        assert result.exit_code == 0
        assert "Created loopback interface" in result.stdout

    def test_set_loopback_interface_error(self, runner, monkeypatch):
        """Test set loopback-interface command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_loopback_interface", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_loopback_interface)
        result = runner.invoke(test_app, ["$lo1", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_loopback_interface_list(self, runner, monkeypatch):
        """Test show loopback-interface command lists interfaces."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_loopback_interfaces", lambda **kwargs: [{"id": "lo-1", "name": "$lo1", "folder": "test-folder", "ip": [{"name": "10.0.0.1/32"}]}])
        test_app = typer.Typer()
        test_app.command()(show_loopback_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "$lo1" in result.stdout

    def test_show_loopback_interface_specific(self, runner, monkeypatch):
        """Test show loopback-interface command shows a specific interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(
            scm_client, "get_loopback_interface", lambda **kwargs: {"id": "lo-1", "name": "$lo1", "folder": "test-folder", "comment": "test lo", "ip": [{"name": "10.0.0.1/32"}]}
        )
        test_app = typer.Typer()
        test_app.command()(show_loopback_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "$lo1"])
        assert result.exit_code == 0
        assert "$lo1" in result.stdout

    def test_delete_loopback_interface_command(self, runner, monkeypatch):
        """Test delete loopback-interface command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_loopback_interface", lambda **kwargs: {"id": "lo-1", "name": "$lo1", "folder": "test-folder"})
        monkeypatch.setattr(scm_client, "delete_loopback_interface", lambda **kwargs: None)
        test_app = typer.Typer()
        test_app.command()(delete_loopback_interface)
        result = runner.invoke(test_app, ["$lo1", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted loopback interface" in result.stdout

    def test_load_loopback_interface_command(self, runner, monkeypatch, tmp_path):
        """Test load loopback-interface command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"loopback_interfaces": [{"name": "$lo1", "folder": "test-folder", "ip": [{"name": "10.0.0.1/32"}]}]}
        yaml_file = tmp_path / "loopback-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        monkeypatch.setattr(scm_client, "create_loopback_interface", lambda d: {**d, "id": "lo-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_loopback_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created loopback interface" in result.stdout

    def test_load_loopback_interface_dry_run(self, runner, monkeypatch, tmp_path):
        """Test load loopback-interface command with dry-run."""
        import yaml

        yaml_data = {"loopback_interfaces": [{"name": "$lo1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "loopback-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        test_app = typer.Typer()
        test_app.command()(load_loopback_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout


class TestTunnelInterfaceCommands:
    """Test the tunnel interface commands."""

    def test_set_tunnel_interface_created(self, runner, monkeypatch):
        """Test set tunnel-interface command creates a new interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_tunnel_interface", lambda d: {**d, "id": "tun-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_tunnel_interface)
        result = runner.invoke(test_app, ["tunnel1", "--folder", "test-folder", "--mtu", "1400"])
        assert result.exit_code == 0
        assert "Created tunnel interface" in result.stdout

    def test_set_tunnel_interface_error(self, runner, monkeypatch):
        """Test set tunnel-interface command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_tunnel_interface", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_tunnel_interface)
        result = runner.invoke(test_app, ["tunnel1", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_tunnel_interface_list(self, runner, monkeypatch):
        """Test show tunnel-interface command lists interfaces."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_tunnel_interfaces", lambda **kwargs: [{"id": "tun-1", "name": "tunnel1", "folder": "test-folder", "mtu": 1400}])
        test_app = typer.Typer()
        test_app.command()(show_tunnel_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "tunnel1" in result.stdout

    def test_show_tunnel_interface_specific(self, runner, monkeypatch):
        """Test show tunnel-interface command shows a specific interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_tunnel_interface", lambda **kwargs: {"id": "tun-1", "name": "tunnel1", "folder": "test-folder", "mtu": 1400, "ip": [{"name": "10.0.0.1/30"}]})
        test_app = typer.Typer()
        test_app.command()(show_tunnel_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "tunnel1"])
        assert result.exit_code == 0
        assert "tunnel1" in result.stdout
        assert "1400" in result.stdout

    def test_delete_tunnel_interface_command(self, runner, monkeypatch):
        """Test delete tunnel-interface command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_tunnel_interface", lambda **kwargs: {"id": "tun-1", "name": "tunnel1", "folder": "test-folder"})
        monkeypatch.setattr(scm_client, "delete_tunnel_interface", lambda **kwargs: None)
        test_app = typer.Typer()
        test_app.command()(delete_tunnel_interface)
        result = runner.invoke(test_app, ["tunnel1", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted tunnel interface" in result.stdout

    def test_load_tunnel_interface_command(self, runner, monkeypatch, tmp_path):
        """Test load tunnel-interface command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"tunnel_interfaces": [{"name": "tunnel1", "folder": "test-folder", "mtu": 1400}]}
        yaml_file = tmp_path / "tunnel-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        monkeypatch.setattr(scm_client, "create_tunnel_interface", lambda d: {**d, "id": "tun-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_tunnel_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created tunnel interface" in result.stdout

    def test_load_tunnel_interface_dry_run(self, runner, monkeypatch, tmp_path):
        """Test load tunnel-interface command with dry-run."""
        import yaml

        yaml_data = {"tunnel_interfaces": [{"name": "tunnel1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "tunnel-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        test_app = typer.Typer()
        test_app.command()(load_tunnel_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout


class TestVlanInterfaceCommands:
    """Test the VLAN interface commands."""

    def test_set_vlan_interface_created(self, runner, monkeypatch):
        """Test set vlan-interface command creates a new interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_vlan_interface", lambda d: {**d, "id": "vlan-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_vlan_interface)
        result = runner.invoke(test_app, ["vlan1", "--folder", "test-folder", "--vlan-tag", "100"])
        assert result.exit_code == 0
        assert "Created VLAN interface" in result.stdout

    def test_set_vlan_interface_error(self, runner, monkeypatch):
        """Test set vlan-interface command handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_vlan_interface", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_vlan_interface)
        result = runner.invoke(test_app, ["vlan1", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_vlan_interface_list(self, runner, monkeypatch):
        """Test show vlan-interface command lists interfaces."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_vlan_interfaces", lambda **kwargs: [{"id": "vlan-1", "name": "vlan1", "folder": "test-folder", "vlan_tag": "100"}])
        test_app = typer.Typer()
        test_app.command()(show_vlan_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "vlan1" in result.stdout

    def test_show_vlan_interface_specific(self, runner, monkeypatch):
        """Test show vlan-interface command shows a specific interface."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_vlan_interface", lambda **kwargs: {"id": "vlan-1", "name": "vlan1", "folder": "test-folder", "vlan_tag": "100", "ip": [{"name": "10.0.10.1/24"}]})
        test_app = typer.Typer()
        test_app.command()(show_vlan_interface)
        result = runner.invoke(test_app, ["--folder", "test-folder", "--name", "vlan1"])
        assert result.exit_code == 0
        assert "vlan1" in result.stdout
        assert "100" in result.stdout

    def test_delete_vlan_interface_command(self, runner, monkeypatch):
        """Test delete vlan-interface command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_vlan_interface", lambda **kwargs: {"id": "vlan-1", "name": "vlan1", "folder": "test-folder"})
        monkeypatch.setattr(scm_client, "delete_vlan_interface", lambda **kwargs: None)
        test_app = typer.Typer()
        test_app.command()(delete_vlan_interface)
        result = runner.invoke(test_app, ["vlan1", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted VLAN interface" in result.stdout

    def test_load_vlan_interface_command(self, runner, monkeypatch, tmp_path):
        """Test load vlan-interface command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"vlan_interfaces": [{"name": "vlan1", "folder": "test-folder", "vlan_tag": "100", "ip": [{"name": "10.0.10.1/24"}]}]}
        yaml_file = tmp_path / "vlan-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        monkeypatch.setattr(scm_client, "create_vlan_interface", lambda d: {**d, "id": "vlan-12345", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_vlan_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created VLAN interface" in result.stdout

    def test_load_vlan_interface_dry_run(self, runner, monkeypatch, tmp_path):
        """Test load vlan-interface command with dry-run."""
        import yaml

        yaml_data = {"vlan_interfaces": [{"name": "vlan1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "vlan-interfaces.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)

        test_app = typer.Typer()
        test_app.command()(load_vlan_interface)
        result = runner.invoke(test_app, ["--file", str(yaml_file), "--dry-run"])
        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout


class TestBgpAddressFamilyProfileCommands:
    """Test the BGP address family profile commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set bgp-address-family-profile creates a new profile."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(data):
            result = data.copy()
            result["id"] = "bgp-af-12345"
            result["__action__"] = "created"
            return result

        monkeypatch.setattr(scm_client, "create_bgp_address_family_profile", mock_create)
        test_app = typer.Typer()
        test_app.command()(set_bgp_address_family_profile)
        result = runner.invoke(test_app, ["test-af", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created BGP address family profile" in result.stdout

    def test_set_error(self, runner, monkeypatch):
        """Test set bgp-address-family-profile handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_bgp_address_family_profile", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_bgp_address_family_profile)
        result = runner.invoke(test_app, ["test-af", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_list(self, runner, monkeypatch):
        """Test show bgp-address-family-profile lists profiles."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_bgp_address_family_profiles", lambda **kw: [{"id": "1", "name": "af1", "folder": "test-folder"}])
        test_app = typer.Typer()
        test_app.command()(show_bgp_address_family_profile)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "af1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete bgp-address-family-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_bgp_address_family_profile", lambda **kw: {"id": "1", "name": "test-af"})
        monkeypatch.setattr(scm_client, "delete_bgp_address_family_profile", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_bgp_address_family_profile)
        result = runner.invoke(test_app, ["test-af", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted BGP address family profile" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load bgp-address-family-profile command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"bgp_address_family_profiles": [{"name": "af1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "af.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_bgp_address_family_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_bgp_address_family_profile)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created BGP address family profile" in result.stdout


class TestBgpAuthProfileCommands:
    """Test the BGP auth profile commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set bgp-auth-profile creates a new profile."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_bgp_auth_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_bgp_auth_profile)
        result = runner.invoke(test_app, ["test-auth", "--folder", "test-folder", "--secret", "my-key"])
        assert result.exit_code == 0
        assert "Created BGP auth profile" in result.stdout

    def test_show_list(self, runner, monkeypatch):
        """Test show bgp-auth-profile lists profiles."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_bgp_auth_profiles", lambda **kw: [{"id": "1", "name": "auth1", "folder": "f"}])
        test_app = typer.Typer()
        test_app.command()(show_bgp_auth_profile)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "auth1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete bgp-auth-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_bgp_auth_profile", lambda **kw: {"id": "1", "name": "test-auth"})
        monkeypatch.setattr(scm_client, "delete_bgp_auth_profile", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_bgp_auth_profile)
        result = runner.invoke(test_app, ["test-auth", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted BGP auth profile" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load bgp-auth-profile command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"bgp_auth_profiles": [{"name": "auth1", "folder": "test-folder", "secret": "key"}]}
        yaml_file = tmp_path / "auth.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_bgp_auth_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_bgp_auth_profile)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created BGP auth profile" in result.stdout


class TestOspfAuthProfileCommands:
    """Test the OSPF auth profile commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set ospf-auth-profile creates a new profile."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_ospf_auth_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_ospf_auth_profile)
        result = runner.invoke(test_app, ["test-ospf", "--folder", "test-folder", "--password", "my-pass"])
        assert result.exit_code == 0
        assert "Created OSPF auth profile" in result.stdout

    def test_show_list(self, runner, monkeypatch):
        """Test show ospf-auth-profile lists profiles."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_ospf_auth_profiles", lambda **kw: [{"id": "1", "name": "ospf1", "folder": "f"}])
        test_app = typer.Typer()
        test_app.command()(show_ospf_auth_profile)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "ospf1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete ospf-auth-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_ospf_auth_profile", lambda **kw: {"id": "1", "name": "test-ospf"})
        monkeypatch.setattr(scm_client, "delete_ospf_auth_profile", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_ospf_auth_profile)
        result = runner.invoke(test_app, ["test-ospf", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted OSPF auth profile" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load ospf-auth-profile command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"ospf_auth_profiles": [{"name": "ospf1", "folder": "test-folder", "password": "pass"}]}
        yaml_file = tmp_path / "ospf.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_ospf_auth_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_ospf_auth_profile)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created OSPF auth profile" in result.stdout


class TestRouteAccessListCommands:
    """Test the route access list commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set route-access-list creates a new entry."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_route_access_list", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_route_access_list)
        result = runner.invoke(test_app, ["test-acl", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created route access list" in result.stdout

    def test_show_list(self, runner, monkeypatch):
        """Test show route-access-list lists entries."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_route_access_lists", lambda **kw: [{"id": "1", "name": "acl1", "folder": "f"}])
        test_app = typer.Typer()
        test_app.command()(show_route_access_list)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "acl1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete route-access-list command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_route_access_list", lambda **kw: {"id": "1", "name": "test-acl"})
        monkeypatch.setattr(scm_client, "delete_route_access_list", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_route_access_list)
        result = runner.invoke(test_app, ["test-acl", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted route access list" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load route-access-list command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"route_access_lists": [{"name": "acl1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "acl.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_route_access_list", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_route_access_list)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created route access list" in result.stdout


class TestRoutePrefixListCommands:
    """Test the route prefix list commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set route-prefix-list creates a new entry."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_route_prefix_list", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_route_prefix_list)
        result = runner.invoke(test_app, ["test-pl", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created route prefix list" in result.stdout

    def test_show_list(self, runner, monkeypatch):
        """Test show route-prefix-list lists entries."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_route_prefix_lists", lambda **kw: [{"id": "1", "name": "pl1", "folder": "f"}])
        test_app = typer.Typer()
        test_app.command()(show_route_prefix_list)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "pl1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete route-prefix-list command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_route_prefix_list", lambda **kw: {"id": "1", "name": "test-pl"})
        monkeypatch.setattr(scm_client, "delete_route_prefix_list", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_route_prefix_list)
        result = runner.invoke(test_app, ["test-pl", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted route prefix list" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load route-prefix-list command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"route_prefix_lists": [{"name": "pl1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "pl.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_route_prefix_list", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_route_prefix_list)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created route prefix list" in result.stdout


class TestBgpFilteringProfileCommands:
    """Test the BGP filtering profile commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set bgp-filtering-profile creates a new profile."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_bgp_filtering_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_bgp_filtering_profile)
        result = runner.invoke(test_app, ["test-filter", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created BGP filtering profile" in result.stdout

    def test_show_list(self, runner, monkeypatch):
        """Test show bgp-filtering-profile lists profiles."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_bgp_filtering_profiles", lambda **kw: [{"id": "1", "name": "filter1", "folder": "f"}])
        test_app = typer.Typer()
        test_app.command()(show_bgp_filtering_profile)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "filter1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete bgp-filtering-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_bgp_filtering_profile", lambda **kw: {"id": "1", "name": "test-filter"})
        monkeypatch.setattr(scm_client, "delete_bgp_filtering_profile", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_bgp_filtering_profile)
        result = runner.invoke(test_app, ["test-filter", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted BGP filtering profile" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load bgp-filtering-profile command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"bgp_filtering_profiles": [{"name": "filter1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "filter.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_bgp_filtering_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_bgp_filtering_profile)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0


class TestBgpRedistributionProfileCommands:
    """Test the BGP redistribution profile commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set bgp-redistribution-profile creates a new profile."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_bgp_redistribution_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_bgp_redistribution_profile)
        result = runner.invoke(test_app, ["test-redist", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created BGP redistribution profile" in result.stdout

    def test_show_list(self, runner, monkeypatch):
        """Test show bgp-redistribution-profile lists profiles."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_bgp_redistribution_profiles", lambda **kw: [{"id": "1", "name": "redist1", "folder": "f"}])
        test_app = typer.Typer()
        test_app.command()(show_bgp_redistribution_profile)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "redist1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete bgp-redistribution-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_bgp_redistribution_profile", lambda **kw: {"id": "1", "name": "test-redist"})
        monkeypatch.setattr(scm_client, "delete_bgp_redistribution_profile", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_bgp_redistribution_profile)
        result = runner.invoke(test_app, ["test-redist", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted BGP redistribution profile" in result.stdout


class TestBgpRouteMapCommands:
    """Test the BGP route map commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set bgp-route-map creates a new entry."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_bgp_route_map", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_bgp_route_map)
        result = runner.invoke(test_app, ["test-rm", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created BGP route map" in result.stdout

    def test_show_list(self, runner, monkeypatch):
        """Test show bgp-route-map lists entries."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_bgp_route_maps", lambda **kw: [{"id": "1", "name": "rm1", "folder": "f", "route_map": []}])
        test_app = typer.Typer()
        test_app.command()(show_bgp_route_map)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "rm1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete bgp-route-map command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_bgp_route_map", lambda **kw: {"id": "1", "name": "test-rm"})
        monkeypatch.setattr(scm_client, "delete_bgp_route_map", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_bgp_route_map)
        result = runner.invoke(test_app, ["test-rm", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted BGP route map" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load bgp-route-map command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"bgp_route_maps": [{"name": "rm1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "rm.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_bgp_route_map", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_bgp_route_map)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0


class TestBgpRouteMapRedistributionCommands:
    """Test the BGP route map redistribution commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set bgp-route-map-redistribution creates a new entry."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_bgp_route_map_redistribution", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_bgp_route_map_redistribution)
        result = runner.invoke(test_app, ["test-rmr", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created BGP route map redistribution" in result.stdout

    def test_show_list(self, runner, monkeypatch):
        """Test show bgp-route-map-redistribution lists entries."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_bgp_route_map_redistributions", lambda **kw: [{"id": "1", "name": "rmr1", "folder": "f"}])
        test_app = typer.Typer()
        test_app.command()(show_bgp_route_map_redistribution)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "rmr1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete bgp-route-map-redistribution command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_bgp_route_map_redistribution", lambda **kw: {"id": "1", "name": "test-rmr"})
        monkeypatch.setattr(scm_client, "delete_bgp_route_map_redistribution", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_bgp_route_map_redistribution)
        result = runner.invoke(test_app, ["test-rmr", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted BGP route map redistribution" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load bgp-route-map-redistribution command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"bgp_route_map_redistributions": [{"name": "rmr1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "rmr.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_bgp_route_map_redistribution", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_bgp_route_map_redistribution)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0


class TestDnsProxyCommands:
    """Test the DNS proxy commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set dns-proxy creates a new proxy."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_dns_proxy", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_dns_proxy)
        result = runner.invoke(test_app, ["test-dns", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created DNS proxy" in result.stdout

    def test_set_error(self, runner, monkeypatch):
        """Test set dns-proxy handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_dns_proxy", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_dns_proxy)
        result = runner.invoke(test_app, ["test-dns", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_list(self, runner, monkeypatch):
        """Test show dns-proxy lists proxies."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_dns_proxies", lambda **kw: [{"id": "1", "name": "dns1", "folder": "test-folder"}])
        test_app = typer.Typer()
        test_app.command()(show_dns_proxy)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "dns1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete dns-proxy command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_dns_proxy", lambda **kw: {"id": "1", "name": "test-dns"})
        monkeypatch.setattr(scm_client, "delete_dns_proxy", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_dns_proxy)
        result = runner.invoke(test_app, ["test-dns", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted DNS proxy" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load dns-proxy command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"dns_proxies": [{"name": "dns1", "folder": "test-folder", "enabled": True}]}
        yaml_file = tmp_path / "dns.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_dns_proxy", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_dns_proxy)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created DNS proxy" in result.stdout


class TestPbfRuleCommands:
    """Test the PBF rule commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set pbf-rule creates a new rule."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_pbf_rule", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_pbf_rule)
        result = runner.invoke(test_app, ["test-pbf", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created PBF rule" in result.stdout

    def test_set_error(self, runner, monkeypatch):
        """Test set pbf-rule handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_pbf_rule", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_pbf_rule)
        result = runner.invoke(test_app, ["test-pbf", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_list(self, runner, monkeypatch):
        """Test show pbf-rule lists rules."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_pbf_rules", lambda **kw: [{"id": "1", "name": "pbf1", "folder": "test-folder"}])
        test_app = typer.Typer()
        test_app.command()(show_pbf_rule)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "pbf1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete pbf-rule command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_pbf_rule", lambda **kw: {"id": "1", "name": "test-pbf"})
        monkeypatch.setattr(scm_client, "delete_pbf_rule", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_pbf_rule)
        result = runner.invoke(test_app, ["test-pbf", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted PBF rule" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load pbf-rule command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"pbf_rules": [{"name": "pbf1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "pbf.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_pbf_rule", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_pbf_rule)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created PBF rule" in result.stdout


class TestQosProfileCommands:
    """Test the QoS profile commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set qos-profile creates a new profile."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_qos_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_qos_profile)
        result = runner.invoke(test_app, ["test-qos", "--folder", "Remote Networks"])
        assert result.exit_code == 0
        assert "Created QoS profile" in result.stdout

    def test_set_error(self, runner, monkeypatch):
        """Test set qos-profile handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_qos_profile", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_qos_profile)
        result = runner.invoke(test_app, ["test-qos", "--folder", "Remote Networks"])
        assert result.exit_code == 1

    def test_show_list(self, runner, monkeypatch):
        """Test show qos-profile lists profiles."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_qos_profiles", lambda **kw: [{"id": "1", "name": "qos1", "folder": "Remote Networks"}])
        test_app = typer.Typer()
        test_app.command()(show_qos_profile)
        result = runner.invoke(test_app, ["--folder", "Remote Networks"])
        assert result.exit_code == 0
        assert "qos1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete qos-profile command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_qos_profile", lambda **kw: {"id": "1", "name": "test-qos"})
        monkeypatch.setattr(scm_client, "delete_qos_profile", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_qos_profile)
        result = runner.invoke(test_app, ["test-qos", "--folder", "Remote Networks", "--force"])
        assert result.exit_code == 0
        assert "Deleted QoS profile" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load qos-profile command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"qos_profiles": [{"name": "qos1", "folder": "Remote Networks"}]}
        yaml_file = tmp_path / "qos.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_qos_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_qos_profile)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created QoS profile" in result.stdout

    def test_set_rejects_invalid_folder(self, runner, monkeypatch):
        """Test set qos-profile rejects folders other than Remote Networks / Service Connections."""
        test_app = typer.Typer()
        test_app.command()(set_qos_profile)
        result = runner.invoke(test_app, ["test-qos", "--folder", "Texas"])
        assert result.exit_code == 1
        assert "Remote Networks" in result.output or "Service Connections" in result.output

    def test_show_rejects_invalid_folder(self, runner, monkeypatch):
        """Test show qos-profile rejects folders other than Remote Networks / Service Connections."""
        test_app = typer.Typer()
        test_app.command()(show_qos_profile)
        result = runner.invoke(test_app, ["--folder", "Texas"])
        assert result.exit_code == 1

    def test_set_accepts_remote_networks_folder(self, runner, monkeypatch):
        """Test set qos-profile accepts Remote Networks folder."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_qos_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_qos_profile)
        result = runner.invoke(test_app, ["test-qos", "--folder", "Remote Networks"])
        assert result.exit_code == 0
        assert "Created QoS profile" in result.stdout

    def test_set_accepts_service_connections_folder(self, runner, monkeypatch):
        """Test set qos-profile accepts Service Connections folder."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_qos_profile", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_qos_profile)
        result = runner.invoke(test_app, ["test-qos", "--folder", "Service Connections"])
        assert result.exit_code == 0
        assert "Created QoS profile" in result.stdout


class TestQosRuleCommands:
    """Test the QoS rule commands."""

    def test_set_created(self, runner, monkeypatch):
        """Test set qos-rule creates a new rule."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_qos_rule", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(set_qos_rule)
        result = runner.invoke(test_app, ["test-qos-rule", "--folder", "test-folder"])
        assert result.exit_code == 0
        assert "Created QoS rule" in result.stdout

    def test_set_error(self, runner, monkeypatch):
        """Test set qos-rule handles errors."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "create_qos_rule", lambda d: (_ for _ in ()).throw(ValueError("Test error")))
        test_app = typer.Typer()
        test_app.command()(set_qos_rule)
        result = runner.invoke(test_app, ["test-qos-rule", "--folder", "test-folder"])
        assert result.exit_code == 1

    def test_show_list(self, runner, monkeypatch):
        """Test show qos-rule lists rules."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_qos_rules", lambda **kw: [{"id": "1", "name": "qr1", "folder": "test-folder"}])
        test_app = typer.Typer()
        test_app.command()(show_qos_rule)
        result = runner.invoke(test_app, ["--folder", "test-folder"])
        assert result.exit_code == 0
        assert "qr1" in result.stdout

    def test_delete_command(self, runner, monkeypatch):
        """Test delete qos-rule command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "get_qos_rule", lambda **kw: {"id": "1", "name": "test-qos-rule"})
        monkeypatch.setattr(scm_client, "delete_qos_rule", lambda **kw: None)
        test_app = typer.Typer()
        test_app.command()(delete_qos_rule)
        result = runner.invoke(test_app, ["test-qos-rule", "--folder", "test-folder", "--force"])
        assert result.exit_code == 0
        assert "Deleted QoS rule" in result.stdout

    def test_load_command(self, runner, monkeypatch, tmp_path):
        """Test load qos-rule command."""
        import yaml

        from scm_cli.utils.sdk_client import scm_client

        yaml_data = {"qos_rules": [{"name": "qr1", "folder": "test-folder"}]}
        yaml_file = tmp_path / "qos-rules.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(yaml_data, f)
        monkeypatch.setattr(scm_client, "create_qos_rule", lambda d: {**d, "id": "1", "__action__": "created"})
        test_app = typer.Typer()
        test_app.command()(load_qos_rule)
        result = runner.invoke(test_app, ["--file", str(yaml_file)])
        assert result.exit_code == 0
        assert "Created QoS rule" in result.stdout

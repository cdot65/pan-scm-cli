"""Tests for the deployment commands module."""

import typer

from scm_cli.commands.deployment import (
    backup_app,
    delete_app,
    delete_bandwidth_allocation,
    delete_bgp_routing,
    delete_internal_dns_server,
    load_app,
    load_bandwidth_allocation,
    load_internal_dns_server,
    set_app,
    set_bandwidth_allocation,
    set_bgp_routing,
    set_internal_dns_server,
    show_app,
    show_bgp_routing,
    show_internal_dns_server,
    show_network_location,
)


class TestDeploymentCommands:
    """Test the deployment commands."""

    def test_set_command_exists(self):
        """Test that the set command exists."""
        assert set_app

    def test_delete_command_exists(self):
        """Test that the delete command exists."""
        assert delete_app

    def test_load_command_exists(self):
        """Test that the load command exists."""
        assert load_app


class TestBandwidthAllocationCommands:
    """Test the bandwidth allocation commands."""

    def test_set_bandwidth_allocation_command(self, runner, monkeypatch):
        """Test the set bandwidth allocation command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "ba-12345",
                "name": kwargs.get("name"),
                "allocated_bandwidth": kwargs.get("bandwidth"),
                "spn_name_list": kwargs.get("spn_name_list", []),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--name",
                "test-allocation",
                "--bandwidth",
                "1000",
                "--spn-name-list",
                "spn1,spn2",
                "--description",
                "Test allocation",
                "--tags",
                "test,example",
            ],
        )

        assert result.exit_code == 0
        assert "Created bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout
        assert "1000" in result.stdout

    def test_set_bandwidth_allocation_error(self, runner, monkeypatch):
        """Test the set bandwidth allocation command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(set_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--name",
                "test-allocation",
                "--bandwidth",
                "1000",
                "--spn-name-list",
                "spn1",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating bandwidth allocation" in result.output
        assert "Test error" in result.output

    def test_delete_bandwidth_allocation_command(self, runner, monkeypatch):
        """Test the delete bandwidth allocation command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_bandwidth_allocation", mock_delete)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--name",
                "test-allocation",
                "--spn-name-list",
                "spn1",
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert "Deleted bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout

    def test_delete_bandwidth_allocation_error(self, runner, monkeypatch):
        """Test the delete bandwidth allocation command with an error."""
        # Mock the SCM client method to simulate an error
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete_error(*args, **kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "delete_bandwidth_allocation", mock_delete_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(delete_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(
            test_app,
            [
                "--name",
                "test-allocation",
                "--spn-name-list",
                "spn1",
                "--force",
            ],
        )

        assert result.exit_code == 1
        assert "Error deleting bandwidth allocation" in result.output
        assert "Test error" in result.output

    def test_load_bandwidth_allocation_command(self, runner, monkeypatch, mock_yaml_file):
        """Test the load bandwidth allocation command."""
        # Mock the SCM client method to avoid actual API calls
        from scm_cli.utils.sdk_client import scm_client

        created_allocations = []

        def mock_create(*args, **kwargs):
            result = {
                "id": f"ba-{len(created_allocations) + 1}",
                "name": kwargs.get("name"),
                "allocated_bandwidth": kwargs.get("bandwidth"),
                "spn_name_list": kwargs.get("spn_name_list", []),
                "description": kwargs.get("description", ""),
                "tags": kwargs.get("tags", []),
            }
            created_allocations.append(result)
            return result

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(test_app, ["--file", str(mock_yaml_file)])

        assert result.exit_code == 0
        assert "Applied bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout
        assert "Loaded 1 bandwidth allocation(s)" in result.stdout
        assert len(created_allocations) == 1

    def test_load_bandwidth_allocation_dry_run(self, runner, monkeypatch, mock_yaml_file):
        """Test the load bandwidth allocation command with dry-run option."""
        # Mock the SCM client method to track if it gets called
        from scm_cli.utils.sdk_client import scm_client

        mock_called = False

        def mock_create(*args, **kwargs):
            nonlocal mock_called
            mock_called = True
            return {}

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_bandwidth_allocation)

        # Invoke the command with dry-run
        result = runner.invoke(test_app, ["--file", str(mock_yaml_file), "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN" in result.stdout
        assert "Would create bandwidth allocation" in result.stdout
        assert "test-allocation" in result.stdout
        assert not mock_called  # Ensure the create method was not called

    def test_load_bandwidth_allocation_error(self, runner, monkeypatch, mock_yaml_file):
        """Test the load bandwidth allocation command with an error."""
        # Import the module directly to get access to its functions
        import scm_cli.commands.deployment as deployment_module
        from scm_cli.utils import config

        # Create a direct mock for load_from_yaml that will be used in the test
        original_load_from_yaml = config.load_from_yaml

        def mock_load_error(*args, **kwargs):
            raise ValueError("YAML parsing error")

        # Apply the mock directly to the imported module
        monkeypatch.setattr(deployment_module, "load_from_yaml", mock_load_error)

        # Create a test app to invoke the command with
        test_app = typer.Typer()
        test_app.command()(load_bandwidth_allocation)

        # Invoke the command
        result = runner.invoke(test_app, ["--file", str(mock_yaml_file)])

        # Restore original function after test
        monkeypatch.setattr(deployment_module, "load_from_yaml", original_load_from_yaml)

        assert result.exit_code == 1
        assert "Error loading bandwidth allocations" in result.output
        assert "YAML parsing error" in result.output

    def test_set_bandwidth_allocation_updated(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "ba-123",
                "name": kwargs.get("name"),
                "allocated_bandwidth": kwargs.get("bandwidth"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_bandwidth_allocation)

        result = runner.invoke(
            test_app,
            ["--name", "test-allocation", "--bandwidth", "1000",
             "--spn-name-list", "spn1,spn2", "--description", "Test"],
        )

        assert result.exit_code == 0
        assert "Updated bandwidth allocation" in result.stdout

    def test_set_bandwidth_allocation_no_change(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "ba-123",
                "name": kwargs.get("name"),
                "allocated_bandwidth": kwargs.get("bandwidth"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_bandwidth_allocation", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_bandwidth_allocation)

        result = runner.invoke(
            test_app,
            ["--name", "test-allocation", "--bandwidth", "1000",
             "--spn-name-list", "spn1,spn2", "--description", "Test"],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout


class TestDeploymentApps:
    """Test that all deployment apps exist."""

    def test_backup_command_exists(self):
        """Test that the backup command exists."""
        assert backup_app

    def test_show_command_exists(self):
        """Test that the show command exists."""
        assert show_app


class TestBGPRoutingCommands:
    """Test the BGP routing commands."""

    def test_set_bgp_routing_command(self, runner, monkeypatch):
        """Test the set bgp-routing command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(**kwargs):
            return {
                "backbone_routing": kwargs.get("backbone_routing"),
                "routing_preference": kwargs.get("routing_preference", {"default": {}}),
                "accept_route_over_SC": kwargs.get("accept_route_over_SC", False),
                "outbound_routes_for_services": kwargs.get("outbound_routes_for_services", []),
                "add_host_route_to_ike_peer": kwargs.get("add_host_route_to_ike_peer", False),
                "withdraw_static_route": kwargs.get("withdraw_static_route", False),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_bgp_routing", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_bgp_routing)

        result = runner.invoke(
            test_app,
            [
                "--backbone-routing",
                "no-asymmetric-routing",
            ],
        )

        assert result.exit_code == 0
        assert "Created BGP routing" in result.stdout

    def test_set_bgp_routing_error(self, runner, monkeypatch):
        """Test the set bgp-routing command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(**kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_bgp_routing", mock_create_error)

        test_app = typer.Typer()
        test_app.command()(set_bgp_routing)

        result = runner.invoke(
            test_app,
            ["--backbone-routing", "no-asymmetric-routing"],
        )

        assert result.exit_code == 1
        assert "Error creating BGP routing" in result.output

    def test_show_bgp_routing_command(self, runner, monkeypatch):
        """Test the show bgp-routing command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get():
            return {
                "backbone_routing": "no-asymmetric-routing",
                "routing_preference": {"default": {}},
                "accept_route_over_SC": False,
                "outbound_routes_for_services": [],
                "add_host_route_to_ike_peer": False,
                "withdraw_static_route": False,
            }

        monkeypatch.setattr(scm_client, "get_bgp_routing", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_bgp_routing)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "BGP Routing Configuration" in result.stdout
        assert "no-asymmetric-routing" in result.stdout

    def test_delete_bgp_routing_command(self, runner, monkeypatch):
        """Test the delete bgp-routing command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete():
            return True

        monkeypatch.setattr(scm_client, "delete_bgp_routing", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_bgp_routing)

        result = runner.invoke(test_app, ["--force"])

        assert result.exit_code == 0
        assert "Reset BGP routing" in result.stdout


class TestInternalDNSServerCommands:
    """Test the internal DNS server commands."""

    def test_set_internal_dns_server_command(self, runner, monkeypatch):
        """Test the set internal-dns-server command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(**kwargs):
            return {
                "id": "dns-12345",
                "name": kwargs.get("name"),
                "domain_name": kwargs.get("domain_name"),
                "primary": kwargs.get("primary"),
                "secondary": kwargs.get("secondary"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_internal_dns_server", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_internal_dns_server)

        result = runner.invoke(
            test_app,
            [
                "--name",
                "corp-dns",
                "--domain-name",
                "corp.example.com",
                "--primary",
                "10.0.0.1",
                "--secondary",
                "10.0.0.2",
            ],
        )

        assert result.exit_code == 0
        assert "Created internal DNS server" in result.stdout
        assert "corp-dns" in result.stdout

    def test_set_internal_dns_server_error(self, runner, monkeypatch):
        """Test the set internal-dns-server command with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create_error(**kwargs):
            raise ValueError("Test error")

        monkeypatch.setattr(scm_client, "create_internal_dns_server", mock_create_error)

        test_app = typer.Typer()
        test_app.command()(set_internal_dns_server)

        result = runner.invoke(
            test_app,
            [
                "--name",
                "corp-dns",
                "--domain-name",
                "corp.example.com",
                "--primary",
                "10.0.0.1",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating internal DNS server" in result.output

    def test_show_internal_dns_server_specific(self, runner, monkeypatch):
        """Test showing a specific internal DNS server."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(name):
            return {
                "id": "dns-12345",
                "name": name,
                "domain_name": ["corp.example.com"],
                "primary": "10.0.0.1",
                "secondary": "10.0.0.2",
            }

        monkeypatch.setattr(scm_client, "get_internal_dns_server", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_internal_dns_server)

        result = runner.invoke(test_app, ["--name", "corp-dns"])

        assert result.exit_code == 0
        assert "corp-dns" in result.stdout
        assert "corp.example.com" in result.stdout
        assert "10.0.0.1" in result.stdout

    def test_show_internal_dns_server_list(self, runner, monkeypatch):
        """Test listing all internal DNS servers."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list():
            return [
                {
                    "id": "dns-1",
                    "name": "dns-server-1",
                    "domain_name": ["corp.example.com"],
                    "primary": "10.0.0.1",
                },
                {
                    "id": "dns-2",
                    "name": "dns-server-2",
                    "domain_name": ["dev.example.com"],
                    "primary": "10.1.0.1",
                },
            ]

        monkeypatch.setattr(scm_client, "list_internal_dns_servers", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_internal_dns_server)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "Internal DNS Servers:" in result.stdout
        assert "dns-server-1" in result.stdout
        assert "dns-server-2" in result.stdout

    def test_delete_internal_dns_server_command(self, runner, monkeypatch):
        """Test the delete internal-dns-server command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(name):
            return True

        monkeypatch.setattr(scm_client, "delete_internal_dns_server", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_internal_dns_server)

        result = runner.invoke(test_app, ["--name", "corp-dns", "--force"])

        assert result.exit_code == 0
        assert "Deleted internal DNS server" in result.stdout
        assert "corp-dns" in result.stdout

    def test_load_internal_dns_server_command(self, runner, monkeypatch, tmp_path):
        """Test the load internal-dns-server command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(**kwargs):
            return {
                "id": "dns-12345",
                "name": kwargs.get("name"),
                "domain_name": kwargs.get("domain_name"),
                "primary": kwargs.get("primary"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_internal_dns_server", mock_create)

        yaml_content = """
        internal_dns_servers:
          - name: corp-dns
            domain_name:
              - corp.example.com
            primary: "10.0.0.1"
        """
        test_file = tmp_path / "test_dns.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_internal_dns_server)

        result = runner.invoke(test_app, ["--file", str(test_file)])

        assert result.exit_code == 0
        assert "Created internal DNS server" in result.stdout
        assert "Loaded 1 internal DNS server(s)" in result.stdout


class TestNetworkLocationCommands:
    """Test the network location commands."""

    def test_show_network_location_specific(self, runner, monkeypatch):
        """Test showing a specific network location."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(value):
            return {
                "value": value,
                "display": "US West",
                "continent": "North America",
                "latitude": 37.38,
                "longitude": -121.98,
                "region": value,
                "aggregate_region": "us-southwest",
            }

        monkeypatch.setattr(scm_client, "get_network_location", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_network_location)

        result = runner.invoke(test_app, ["--value", "us-west-1"])

        assert result.exit_code == 0
        assert "US West" in result.stdout
        assert "us-west-1" in result.stdout
        assert "North America" in result.stdout

    def test_show_network_location_list(self, runner, monkeypatch):
        """Test listing all network locations."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list():
            return [
                {
                    "value": "us-west-1",
                    "display": "US West",
                    "continent": "North America",
                    "region": "us-west-1",
                },
                {
                    "value": "us-east-1",
                    "display": "US East",
                    "continent": "North America",
                    "region": "us-east-1",
                },
            ]

        monkeypatch.setattr(scm_client, "list_network_locations", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_network_location)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "Network Locations:" in result.stdout
        assert "us-west-1" in result.stdout
        assert "us-east-1" in result.stdout

    def test_show_network_location_empty(self, runner, monkeypatch):
        """Test showing network locations when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list():
            return []

        monkeypatch.setattr(scm_client, "list_network_locations", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_network_location)

        result = runner.invoke(test_app, [])

        assert result.exit_code == 0
        assert "No network locations found" in result.stdout

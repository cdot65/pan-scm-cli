"""Tests for the GlobalProtect forwarding profile sub-resource commands.

Covers forwarding-profile-source-application, forwarding-profile-user-location,
and forwarding-profile-regional-and-custom-proxy commands.
"""

import typer  # noqa: I001
from scm_cli.commands.mobile_agent import (
    backup_forwarding_profile_regional_and_custom_proxy,
    backup_forwarding_profile_source_application,
    backup_forwarding_profile_user_location,
    delete_forwarding_profile_regional_and_custom_proxy,
    delete_forwarding_profile_source_application,
    delete_forwarding_profile_user_location,
    load_forwarding_profile_regional_and_custom_proxy,
    load_forwarding_profile_source_application,
    load_forwarding_profile_user_location,
    set_forwarding_profile_regional_and_custom_proxy,
    set_forwarding_profile_source_application,
    set_forwarding_profile_user_location,
    show_forwarding_profile_regional_and_custom_proxy,
    show_forwarding_profile_source_application,
    show_forwarding_profile_user_location,
)


class TestForwardingProfileSourceApplicationCommands:
    """Test the forwarding profile source application commands."""

    def test_set_source_application(self, runner, monkeypatch):
        """Test creating a forwarding profile source application."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "fpsa-1",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "applications": kwargs.get("applications"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_source_application", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "office-apps",
                "--application", "slack",
                "--application", "zoom",
            ],
        )

        assert result.exit_code == 0
        assert "Created forwarding profile source application" in result.stdout
        assert "office-apps" in result.stdout

    def test_set_source_application_update(self, runner, monkeypatch):
        """Test updating a forwarding profile source application."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "fpsa-1",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_source_application", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "office-apps",
                "--application", "slack",
            ],
        )

        assert result.exit_code == 0
        assert "Updated forwarding profile source application" in result.stdout

    def test_set_source_application_no_change(self, runner, monkeypatch):
        """Test set source application with no changes."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "fpsa-1",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_source_application", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "office-apps",
                "--application", "slack",
            ],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout

    def test_set_source_application_missing_folder(self, runner, monkeypatch):
        """Test container validation error when folder is missing."""
        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            [
                "--name", "office-apps",
                "--application", "slack",
            ],
        )

        assert result.exit_code == 1

    def test_show_source_application_list(self, runner, monkeypatch):
        """Test listing forwarding profile source applications."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "fpsa-1",
                    "folder": "Mobile Users",
                    "name": "office-apps",
                    "applications": ["slack", "zoom"],
                },
                {
                    "id": "fpsa-2",
                    "folder": "Mobile Users",
                    "name": "dev-apps",
                    "applications": ["github"],
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profile_source_applications", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "office-apps" in result.stdout
        assert "dev-apps" in result.stdout

    def test_show_source_application_detail(self, runner, monkeypatch):
        """Test showing a specific forwarding profile source application."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "fpsa-1",
                "folder": "Mobile Users",
                "name": "office-apps",
                "description": "Office applications",
                "applications": ["slack", "zoom"],
            }

        monkeypatch.setattr(scm_client, "get_forwarding_profile_source_application", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "office-apps"],
        )

        assert result.exit_code == 0
        assert "office-apps" in result.stdout
        assert "slack" in result.stdout

    def test_show_source_application_empty(self, runner, monkeypatch):
        """Test listing source applications when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_forwarding_profile_source_applications", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "No forwarding profile source applications found" in result.stdout

    def test_delete_source_application(self, runner, monkeypatch):
        """Test deleting a forwarding profile source application."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_forwarding_profile_source_application", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "office-apps", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted forwarding profile source application" in result.stdout

    def test_delete_source_application_error(self, runner, monkeypatch):
        """Test deleting a source application with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "delete_forwarding_profile_source_application", mock_error)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "nonexistent", "--force"],
        )

        assert result.exit_code == 1

    def test_load_source_application(self, runner, monkeypatch, tmp_path):
        """Test loading source applications from YAML."""
        from scm_cli.utils.sdk_client import scm_client

        yaml_content = """
forwarding_profile_source_applications:
  - name: office-apps
    folder: "Mobile Users"
    applications:
      - slack
      - zoom
  - name: dev-apps
    folder: "Mobile Users"
    applications:
      - github
"""
        test_file = tmp_path / "source_applications.yml"
        test_file.write_text(yaml_content)

        def mock_create(*args, **kwargs):
            return {
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_source_application", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file)],
        )

        assert result.exit_code == 0
        assert "Created forwarding profile source application" in result.stdout
        assert "2 created" in result.stdout

    def test_load_source_application_dry_run(self, runner, monkeypatch, tmp_path):
        """Test loading source applications in dry run mode."""
        yaml_content = """
forwarding_profile_source_applications:
  - name: office-apps
    folder: "Mobile Users"
    applications:
      - slack
"""
        test_file = tmp_path / "source_applications.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file), "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout

    def test_backup_source_application(self, runner, monkeypatch, tmp_path):
        """Test backing up source applications."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "fpsa-1",
                    "folder": "Mobile Users",
                    "name": "office-apps",
                    "applications": ["slack", "zoom"],
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profile_source_applications", mock_list)
        monkeypatch.chdir(tmp_path)

        test_app = typer.Typer()
        test_app.command()(backup_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "Successfully backed up" in result.stdout
        assert "1 forwarding profile source applications" in result.stdout

    def test_set_source_application_error(self, runner, monkeypatch):
        """Test set source application with an API error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "create_forwarding_profile_source_application", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_source_application)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "fail-apps",
                "--application", "slack",
            ],
        )

        assert result.exit_code == 1


class TestForwardingProfileUserLocationCommands:
    """Test the forwarding profile user location commands."""

    def test_set_user_location_ip_addresses(self, runner, monkeypatch):
        """Test creating a user location with IP address entries."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "fpul-1",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "choice": kwargs.get("choice"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_user_location", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "branch-network",
                "--ip-address", "10.1.0.0/16",
                "--ip-address", "10.2.*.*",
            ],
        )

        assert result.exit_code == 0
        assert "Created forwarding profile user location" in result.stdout
        assert "branch-network" in result.stdout

    def test_set_user_location_internal_host(self, runner, monkeypatch):
        """Test creating a user location with internal host detection."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "fpul-2",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "choice": kwargs.get("choice"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_user_location", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "corp-office",
                "--internal-host-ip", "192.168.1.1",
                "--internal-host-fqdn", "intranet.example.com",
            ],
        )

        assert result.exit_code == 0
        assert "Created forwarding profile user location" in result.stdout

    def test_set_user_location_update(self, runner, monkeypatch):
        """Test updating a user location."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "fpul-1",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_user_location", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "branch-network",
                "--ip-address", "10.1.0.0/16",
            ],
        )

        assert result.exit_code == 0
        assert "Updated forwarding profile user location" in result.stdout

    def test_set_user_location_choice_conflict(self, runner, monkeypatch):
        """Test validation error when both choice variants are provided."""
        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "bad-location",
                "--ip-address", "10.1.0.0/16",
                "--internal-host-fqdn", "intranet.example.com",
            ],
        )

        assert result.exit_code == 1

    def test_set_user_location_choice_missing(self, runner, monkeypatch):
        """Test validation error when no choice variant is provided."""
        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "bad-location",
            ],
        )

        assert result.exit_code == 1

    def test_set_user_location_missing_folder(self, runner, monkeypatch):
        """Test container validation error when folder is missing."""
        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            [
                "--name", "branch-network",
                "--ip-address", "10.1.0.0/16",
            ],
        )

        assert result.exit_code == 1

    def test_show_user_location_list(self, runner, monkeypatch):
        """Test listing user locations."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "fpul-1",
                    "folder": "Mobile Users",
                    "name": "branch-network",
                    "choice": {"ip_addresses": [{"name": "10.1.0.0/16"}]},
                },
                {
                    "id": "fpul-2",
                    "folder": "Mobile Users",
                    "name": "corp-office",
                    "choice": {"internal_host_detection": {"fqdn": "intranet.example.com"}},
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profile_user_locations", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "branch-network" in result.stdout
        assert "corp-office" in result.stdout

    def test_show_user_location_detail(self, runner, monkeypatch):
        """Test showing a specific user location."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "fpul-1",
                "folder": "Mobile Users",
                "name": "branch-network",
                "description": "Branch office network",
                "choice": {"ip_addresses": [{"name": "10.1.0.0/16"}]},
            }

        monkeypatch.setattr(scm_client, "get_forwarding_profile_user_location", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "branch-network"],
        )

        assert result.exit_code == 0
        assert "branch-network" in result.stdout
        assert "10.1.0.0/16" in result.stdout

    def test_show_user_location_empty(self, runner, monkeypatch):
        """Test listing user locations when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_forwarding_profile_user_locations", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "No forwarding profile user locations found" in result.stdout

    def test_delete_user_location(self, runner, monkeypatch):
        """Test deleting a user location."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_forwarding_profile_user_location", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "branch-network", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted forwarding profile user location" in result.stdout

    def test_delete_user_location_error(self, runner, monkeypatch):
        """Test deleting a user location with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "delete_forwarding_profile_user_location", mock_error)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "nonexistent", "--force"],
        )

        assert result.exit_code == 1

    def test_load_user_location(self, runner, monkeypatch, tmp_path):
        """Test loading user locations from YAML."""
        from scm_cli.utils.sdk_client import scm_client

        yaml_content = """
forwarding_profile_user_locations:
  - name: branch-network
    folder: "Mobile Users"
    ip_addresses:
      - 10.1.0.0/16
  - name: corp-office
    folder: "Mobile Users"
    internal_host_fqdn: intranet.example.com
"""
        test_file = tmp_path / "user_locations.yml"
        test_file.write_text(yaml_content)

        def mock_create(*args, **kwargs):
            return {
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_user_location", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file)],
        )

        assert result.exit_code == 0
        assert "Created forwarding profile user location" in result.stdout
        assert "2 created" in result.stdout

    def test_load_user_location_dry_run(self, runner, monkeypatch, tmp_path):
        """Test loading user locations in dry run mode."""
        yaml_content = """
forwarding_profile_user_locations:
  - name: branch-network
    folder: "Mobile Users"
    ip_addresses:
      - 10.1.0.0/16
"""
        test_file = tmp_path / "user_locations.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file), "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout

    def test_backup_user_location(self, runner, monkeypatch, tmp_path):
        """Test backing up user locations."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "fpul-1",
                    "folder": "Mobile Users",
                    "name": "branch-network",
                    "choice": {"ip_addresses": [{"name": "10.1.0.0/16"}]},
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profile_user_locations", mock_list)
        monkeypatch.chdir(tmp_path)

        test_app = typer.Typer()
        test_app.command()(backup_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "Successfully backed up" in result.stdout
        assert "1 forwarding profile user locations" in result.stdout

    def test_set_user_location_error(self, runner, monkeypatch):
        """Test set user location with an API error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "create_forwarding_profile_user_location", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_user_location)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "fail-location",
                "--ip-address", "10.1.0.0/16",
            ],
        )

        assert result.exit_code == 1


class TestForwardingProfileRegionalAndCustomProxyCommands:
    """Test the forwarding profile regional and custom proxy commands."""

    def test_set_regional_proxy(self, runner, monkeypatch):
        """Test creating a regional and custom proxy."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "fprcp-1",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "type": kwargs.get("type"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_regional_and_custom_proxy", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "emea-proxy",
                "--type", "gp-and-pac",
                "--proxy-1-fqdn", "proxy1.example.com",
                "--proxy-1-port", "8080",
                "--fallback-option", "fail-open",
            ],
        )

        assert result.exit_code == 0
        assert "Created forwarding profile regional and custom proxy" in result.stdout
        assert "emea-proxy" in result.stdout

    def test_set_regional_proxy_update(self, runner, monkeypatch):
        """Test updating a regional and custom proxy."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "fprcp-1",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_regional_and_custom_proxy", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "emea-proxy",
                "--proxy-1-fqdn", "proxy2.example.com",
            ],
        )

        assert result.exit_code == 0
        assert "Updated forwarding profile regional and custom proxy" in result.stdout

    def test_set_regional_proxy_missing_folder(self, runner, monkeypatch):
        """Test container validation error when folder is missing."""
        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            ["--name", "emea-proxy"],
        )

        assert result.exit_code == 1

    def test_show_regional_proxy_list(self, runner, monkeypatch):
        """Test listing regional and custom proxies."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "fprcp-1",
                    "folder": "Mobile Users",
                    "name": "emea-proxy",
                    "type": "gp-and-pac",
                },
                {
                    "id": "fprcp-2",
                    "folder": "Mobile Users",
                    "name": "ztna-proxy",
                    "type": "ztna-agent",
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profile_regional_and_custom_proxies", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "emea-proxy" in result.stdout
        assert "ztna-proxy" in result.stdout

    def test_show_regional_proxy_detail(self, runner, monkeypatch):
        """Test showing a specific regional and custom proxy."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "fprcp-1",
                "folder": "Mobile Users",
                "name": "emea-proxy",
                "description": "EMEA regional proxy",
                "type": "gp-and-pac",
                "proxy_1": {"fqdn": "proxy1.example.com", "port": 8080},
                "fallback_option": "fail-open",
                "location_preference": "best-available-pa-location",
            }

        monkeypatch.setattr(scm_client, "get_forwarding_profile_regional_and_custom_proxy", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "emea-proxy"],
        )

        assert result.exit_code == 0
        assert "emea-proxy" in result.stdout
        assert "proxy1.example.com" in result.stdout

    def test_show_regional_proxy_empty(self, runner, monkeypatch):
        """Test listing regional and custom proxies when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_forwarding_profile_regional_and_custom_proxies", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "No forwarding profile regional and custom proxies found" in result.stdout

    def test_delete_regional_proxy(self, runner, monkeypatch):
        """Test deleting a regional and custom proxy."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_forwarding_profile_regional_and_custom_proxy", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "emea-proxy", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted forwarding profile regional and custom proxy" in result.stdout

    def test_delete_regional_proxy_error(self, runner, monkeypatch):
        """Test deleting a regional and custom proxy with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "delete_forwarding_profile_regional_and_custom_proxy", mock_error)

        test_app = typer.Typer()
        test_app.command()(delete_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "nonexistent", "--force"],
        )

        assert result.exit_code == 1

    def test_load_regional_proxy(self, runner, monkeypatch, tmp_path):
        """Test loading regional and custom proxies from YAML, including nested fields."""
        from scm_cli.utils.sdk_client import scm_client

        yaml_content = """
forwarding_profile_regional_and_custom_proxies:
  - name: emea-proxy
    folder: "Mobile Users"
    type: gp-and-pac
    proxy_1:
      fqdn: proxy1.example.com
      port: 8080
    connectivity_preference:
      - name: tunnel
        enabled: true
      - name: proxy
        enabled: false
    fallback_option: fail-open
  - name: ztna-proxy
    folder: "Mobile Users"
    type: ztna-agent
    location_preference: specific-pa-location
    prisma_access_locations:
      - name: europe
        locations:
          - "Frankfurt"
"""
        test_file = tmp_path / "regional_proxies.yml"
        test_file.write_text(yaml_content)

        def mock_create(*args, **kwargs):
            return {
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_forwarding_profile_regional_and_custom_proxy", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file)],
        )

        assert result.exit_code == 0
        assert "Created forwarding profile regional and custom proxy" in result.stdout
        assert "2 created" in result.stdout

    def test_load_regional_proxy_dry_run(self, runner, monkeypatch, tmp_path):
        """Test loading regional and custom proxies in dry run mode."""
        yaml_content = """
forwarding_profile_regional_and_custom_proxies:
  - name: emea-proxy
    folder: "Mobile Users"
    type: gp-and-pac
"""
        test_file = tmp_path / "regional_proxies.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file), "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout

    def test_backup_regional_proxy(self, runner, monkeypatch, tmp_path):
        """Test backing up regional and custom proxies."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "fprcp-1",
                    "folder": "Mobile Users",
                    "name": "emea-proxy",
                    "type": "gp-and-pac",
                    "proxy_1": {"fqdn": "proxy1.example.com", "port": 8080},
                },
            ]

        monkeypatch.setattr(scm_client, "list_forwarding_profile_regional_and_custom_proxies", mock_list)
        monkeypatch.chdir(tmp_path)

        test_app = typer.Typer()
        test_app.command()(backup_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "Successfully backed up" in result.stdout
        assert "1 forwarding profile regional and custom proxies" in result.stdout

    def test_set_regional_proxy_error(self, runner, monkeypatch):
        """Test set regional and custom proxy with an API error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "create_forwarding_profile_regional_and_custom_proxy", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_forwarding_profile_regional_and_custom_proxy)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "fail-proxy",
            ],
        )

        assert result.exit_code == 1

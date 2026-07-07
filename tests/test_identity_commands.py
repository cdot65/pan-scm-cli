"""Tests for the identity commands module."""

import json

import pytest
import typer

from scm_cli.commands.identity import (
    backup_app,
    delete_app,
    delete_authentication_profile,
    load_app,
    set_app,
    set_authentication_profile,
    set_kerberos_server_profile,
    set_ldap_server_profile,
    set_radius_server_profile,
    set_saml_server_profile,
    set_tacacs_server_profile,
    show_app,
    show_authentication_profile,
    show_kerberos_server_profile,
    show_ldap_server_profile,
    show_radius_server_profile,
    show_saml_server_profile,
    show_tacacs_server_profile,
)


class TestIdentityCommands:
    """Test the identity command apps exist."""

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

    def test_backup_command_exists(self):
        """Test that the backup command exists."""
        assert backup_app


class TestAuthenticationProfileCommands:
    """Test the authentication profile commands."""

    def test_set_authentication_profile_command(self, runner, monkeypatch):
        """Test the set authentication profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "auth-12345",
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_authentication_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_authentication_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-auth",
                "--method",
                '{"local_database": {}}',
            ],
        )
        assert result.exit_code == 0
        assert "Created authentication profile" in result.output

    def test_show_authentication_profile_command(self, runner, monkeypatch):
        """Test the show authentication profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {"name": "test-auth", "folder": "Texas", "method": {"local_database": {}}},
            ]

        monkeypatch.setattr(scm_client, "list_authentication_profiles", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_authentication_profile)

        result = runner.invoke(test_app, ["--folder", "Texas", "--list"])
        assert result.exit_code == 0
        assert "test-auth" in result.output

    def test_delete_authentication_profile_command(self, runner, monkeypatch):
        """Test the delete authentication profile command."""
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "delete_authentication_profile", lambda *a, **k: True)

        test_app = typer.Typer()
        test_app.command()(delete_authentication_profile)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "test-auth", "--force"])
        assert result.exit_code == 0
        assert "Deleted authentication profile" in result.output


class TestKerberosServerProfileCommands:
    """Test the Kerberos server profile commands."""

    def test_set_kerberos_server_profile_command(self, runner, monkeypatch):
        """Test the set Kerberos server profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"id": "kerb-12345", "name": kwargs.get("name"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_kerberos_server_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_kerberos_server_profile)

        result = runner.invoke(
            test_app,
            ["--folder", "Texas", "--name", "test-kerberos", "--servers", '[{"name": "kdc1", "host": "kdc.example.com", "port": 88}]'],
        )
        assert result.exit_code == 0
        assert "Created Kerberos server profile" in result.output


class TestLdapServerProfileCommands:
    """Test the LDAP server profile commands."""

    def test_set_ldap_server_profile_command(self, runner, monkeypatch):
        """Test the set LDAP server profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"id": "ldap-12345", "name": kwargs.get("name"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_ldap_server_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_ldap_server_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-ldap",
                "--servers",
                '[{"name": "ldap1", "address": "ldap.example.com", "port": 389}]',
                "--base",
                "dc=example,dc=com",
                "--ldap-type",
                "active-directory",
            ],
        )
        assert result.exit_code == 0
        assert "Created LDAP server profile" in result.output


class TestRadiusServerProfileCommands:
    """Test the RADIUS server profile commands."""

    def test_set_radius_server_profile_command(self, runner, monkeypatch):
        """Test the set RADIUS server profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"id": "radius-12345", "name": kwargs.get("name"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_radius_server_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_radius_server_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-radius",
                "--servers",
                '[{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812, "secret": "s3cret"}]',
                "--protocol",
                '{"CHAP": {}}',
                "--timeout",
                "5",
                "--retries",
                "3",
            ],
        )
        assert result.exit_code == 0
        assert "Created RADIUS server profile" in result.output


class TestSamlServerProfileCommands:
    """Test the SAML server profile commands."""

    def test_set_saml_server_profile_command(self, runner, monkeypatch):
        """Test the set SAML server profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"id": "saml-12345", "name": kwargs.get("name"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_saml_server_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_saml_server_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-saml",
                "--entity-id",
                "https://idp.example.com",
                "--certificate",
                "idp-cert",
                "--sso-url",
                "https://idp.example.com/sso",
                "--sso-bindings",
                "post",
            ],
        )
        assert result.exit_code == 0
        assert "Created SAML server profile" in result.output


class TestTacacsServerProfileCommands:
    """Test the TACACS+ server profile commands."""

    def test_set_tacacs_server_profile_command(self, runner, monkeypatch):
        """Test the set TACACS+ server profile command."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {"id": "tacacs-12345", "name": kwargs.get("name"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_tacacs_server_profile", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_tacacs_server_profile)

        result = runner.invoke(
            test_app,
            [
                "--folder",
                "Texas",
                "--name",
                "test-tacacs",
                "--servers",
                '[{"name": "tac1", "address": "10.0.0.1", "port": 49, "secret": "s3cret"}]',
                "--protocol",
                "CHAP",
                "--timeout",
                "5",
            ],
        )
        assert result.exit_code == 0
        assert "Created TACACS+ server profile" in result.output


class TestShowJsonOutput:
    """Test that show commands emit machine-readable JSON on stdout."""

    @pytest.mark.parametrize(
        ("command", "list_method"),
        [
            (show_authentication_profile, "list_authentication_profiles"),
            (show_kerberos_server_profile, "list_kerberos_server_profiles"),
            (show_ldap_server_profile, "list_ldap_server_profiles"),
            (show_radius_server_profile, "list_radius_server_profiles"),
            (show_saml_server_profile, "list_saml_server_profiles"),
            (show_tacacs_server_profile, "list_tacacs_server_profiles"),
        ],
    )
    def test_show_list_output_json_round_trips(self, runner, monkeypatch, command, list_method):
        from scm_cli.utils.sdk_client import scm_client

        records = [
            {"id": "prof-1", "name": "profile-one", "folder": "Texas"},
            {"id": "prof-2", "name": "profile-two", "folder": "Texas"},
        ]
        monkeypatch.setattr(scm_client, list_method, lambda *a, **kw: records)

        test_app = typer.Typer()
        test_app.command()(command)

        result = runner.invoke(test_app, ["--folder", "Texas", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout) == records

    def test_show_authentication_profile_by_name_output_json(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        record = {
            "id": "auth-12345",
            "name": "test-auth",
            "folder": "Texas",
            "method": {"local_database": {}},
            "allow_list": ["all"],
        }
        monkeypatch.setattr(scm_client, "get_authentication_profile", lambda *a, **kw: record)

        test_app = typer.Typer()
        test_app.command()(show_authentication_profile)

        result = runner.invoke(test_app, ["--folder", "Texas", "--name", "test-auth", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout) == record

    def test_show_authentication_profile_empty_list_output_json(self, runner, monkeypatch):
        from scm_cli.utils.sdk_client import scm_client

        monkeypatch.setattr(scm_client, "list_authentication_profiles", lambda *a, **kw: [])

        test_app = typer.Typer()
        test_app.command()(show_authentication_profile)

        result = runner.invoke(test_app, ["--folder", "Texas", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert json.loads(result.stdout) == []


class TestIdentityBulkLoadConcurrency:
    """Bulk loads issue create calls concurrently (bounded thread pool)."""

    def test_load_authentication_profile_runs_concurrently(self, runner, monkeypatch, tmp_path):
        import threading
        import time

        from scm_cli.utils.sdk_client import scm_client

        yaml_content = "authentication_profiles:\n" + "".join(f"  - name: auth-{i}\n    folder: Texas\n" for i in range(4))
        test_file = tmp_path / "auth_profiles.yaml"
        test_file.write_text(yaml_content)

        active = {"now": 0, "max": 0}
        lock = threading.Lock()
        created = []

        def mock_create(**kwargs):
            with lock:
                active["now"] += 1
                active["max"] = max(active["max"], active["now"])
            time.sleep(0.05)
            with lock:
                active["now"] -= 1
                created.append(kwargs.get("name"))
            return {"name": kwargs.get("name"), "__action__": "created"}

        monkeypatch.setattr(scm_client, "create_authentication_profile", mock_create)

        result = runner.invoke(load_app, ["authentication-profile", "--file", str(test_file)])

        assert result.exit_code == 0, result.output
        assert active["max"] > 1, "create calls never overlapped"
        assert sorted(created) == [f"auth-{i}" for i in range(4)]
        assert "Processed 4 authentication profiles" in result.output

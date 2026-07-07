"""Tests for the mobile agent commands module."""

import typer  # noqa: I001
from scm_cli.commands.mobile_agent import (
    backup_app,
    delete_app,
    delete_auth_setting,
    load_app,
    load_auth_setting,
    set_app,
    set_auth_setting,
    show_agent_version,
    show_app,
    show_auth_setting,
)


class TestMobileAgentCommands:
    """Test the mobile agent command apps exist."""

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


class TestAgentVersionCommands:
    """Test the agent version commands."""

    def test_show_agent_version_list(self, runner, monkeypatch):
        """Test listing agent versions."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "av-1",
                    "folder": "Mobile Users",
                    "name": "5.2.13",
                    "version": "5.2.13",
                    "platform": "Windows",
                    "release_date": "2024-01-15",
                },
                {
                    "id": "av-2",
                    "folder": "Mobile Users",
                    "name": "5.2.12",
                    "version": "5.2.12",
                    "platform": "macOS",
                    "release_date": "2024-01-10",
                },
            ]

        monkeypatch.setattr(scm_client, "list_agent_versions", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_agent_version)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "5.2.13" in result.stdout
        assert "5.2.12" in result.stdout
        assert "Windows" in result.stdout

    def test_show_agent_version_detail(self, runner, monkeypatch):
        """Test showing a specific agent version."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "av-5.2.13",
                "folder": "Mobile Users",
                "name": "5.2.13",
                "version": "5.2.13",
                "description": "GlobalProtect agent 5.2.13",
                "platform": "Windows",
                "release_date": "2024-01-15",
            }

        monkeypatch.setattr(scm_client, "get_agent_version", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_agent_version)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "5.2.13"],
        )

        assert result.exit_code == 0
        assert "5.2.13" in result.stdout
        assert "Windows" in result.stdout

    def test_show_agent_version_empty(self, runner, monkeypatch):
        """Test listing agent versions when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_agent_versions", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_agent_version)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "No results found" in result.stdout

    def test_show_agent_version_error(self, runner, monkeypatch):
        """Test showing agent version with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "list_agent_versions", mock_error)

        test_app = typer.Typer()
        test_app.command()(show_agent_version)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 1


class TestAuthSettingCommands:
    """Test the auth setting commands."""

    def test_set_auth_setting(self, runner, monkeypatch):
        """Test creating an auth setting."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "as-saml-auth",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "authentication_profile": kwargs.get("authentication_profile"),
                "os": kwargs.get("os"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_auth_setting", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_auth_setting)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "saml-auth",
                "--authentication-profile", "best-practice",
                "--os", "Any",
            ],
        )

        assert result.exit_code == 0
        assert "Created auth setting" in result.stdout
        assert "saml-auth" in result.stdout

    def test_set_auth_setting_update(self, runner, monkeypatch):
        """Test updating an auth setting."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "as-saml-auth",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "__action__": "updated",
            }

        monkeypatch.setattr(scm_client, "create_auth_setting", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_auth_setting)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "saml-auth",
                "--authentication-profile", "best-practice",
            ],
        )

        assert result.exit_code == 0
        assert "Updated auth setting" in result.stdout

    def test_set_auth_setting_no_change(self, runner, monkeypatch):
        """Test set auth setting with no changes."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_create(*args, **kwargs):
            return {
                "id": "as-saml-auth",
                "folder": kwargs.get("folder"),
                "name": kwargs.get("name"),
                "__action__": "no_change",
            }

        monkeypatch.setattr(scm_client, "create_auth_setting", mock_create)

        test_app = typer.Typer()
        test_app.command()(set_auth_setting)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "saml-auth",
            ],
        )

        assert result.exit_code == 0
        assert "No changes needed" in result.stdout

    def test_show_auth_setting_list(self, runner, monkeypatch):
        """Test listing auth settings."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "as-mock1",
                    "folder": "Mobile Users",
                    "name": "saml-auth",
                    "authentication_profile": "best-practice",
                    "os": "Any",
                },
                {
                    "id": "as-mock2",
                    "folder": "Mobile Users",
                    "name": "cert-auth",
                    "authentication_profile": "corp-cert-profile",
                    "os": "Windows",
                },
            ]

        monkeypatch.setattr(scm_client, "list_auth_settings", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_auth_setting)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "saml-auth" in result.stdout
        assert "cert-auth" in result.stdout

    def test_show_auth_setting_detail(self, runner, monkeypatch):
        """Test showing a specific auth setting."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_get(*args, **kwargs):
            return {
                "id": "as-saml-auth",
                "folder": "Mobile Users",
                "name": "saml-auth",
                "description": "SAML auth config",
                "authentication_profile": "best-practice",
                "os": "Any",
            }

        monkeypatch.setattr(scm_client, "get_auth_setting", mock_get)

        test_app = typer.Typer()
        test_app.command()(show_auth_setting)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "saml-auth"],
        )

        assert result.exit_code == 0
        assert "saml-auth" in result.stdout
        assert "best-practice" in result.stdout

    def test_show_auth_setting_empty(self, runner, monkeypatch):
        """Test listing auth settings when none exist."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return []

        monkeypatch.setattr(scm_client, "list_auth_settings", mock_list)

        test_app = typer.Typer()
        test_app.command()(show_auth_setting)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "No results found" in result.stdout

    def test_delete_auth_setting(self, runner, monkeypatch):
        """Test deleting an auth setting."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_delete(*args, **kwargs):
            return True

        monkeypatch.setattr(scm_client, "delete_auth_setting", mock_delete)

        test_app = typer.Typer()
        test_app.command()(delete_auth_setting)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "saml-auth", "--force"],
        )

        assert result.exit_code == 0
        assert "Deleted auth setting" in result.stdout

    def test_delete_auth_setting_error(self, runner, monkeypatch):
        """Test deleting an auth setting with an error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("Not found")

        monkeypatch.setattr(scm_client, "delete_auth_setting", mock_error)

        test_app = typer.Typer()
        test_app.command()(delete_auth_setting)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users", "--name", "nonexistent", "--force"],
        )

        assert result.exit_code == 1

    def test_load_auth_setting(self, runner, monkeypatch, tmp_path):
        """Test loading auth settings from YAML."""
        from scm_cli.utils.sdk_client import scm_client

        yaml_content = """
auth_settings:
  - name: saml-auth
    folder: "Mobile Users"
    authentication_profile: best-practice
    os: Any
  - name: cert-auth
    folder: "Mobile Users"
    authentication_profile: corp-cert-profile
    os: Windows
"""
        test_file = tmp_path / "auth_settings.yml"
        test_file.write_text(yaml_content)

        def mock_create(*args, **kwargs):
            return {
                "name": kwargs.get("name"),
                "folder": kwargs.get("folder"),
                "__action__": "created",
            }

        monkeypatch.setattr(scm_client, "create_auth_setting", mock_create)

        test_app = typer.Typer()
        test_app.command()(load_auth_setting)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file)],
        )

        assert result.exit_code == 0
        assert "Created auth setting" in result.stdout
        assert "2 created" in result.stdout

    def test_load_auth_setting_dry_run(self, runner, monkeypatch, tmp_path):
        """Test loading auth settings in dry run mode."""
        yaml_content = """
auth_settings:
  - name: saml-auth
    folder: "Mobile Users"
    authentication_profile: best-practice
"""
        test_file = tmp_path / "auth_settings.yml"
        test_file.write_text(yaml_content)

        test_app = typer.Typer()
        test_app.command()(load_auth_setting)

        result = runner.invoke(
            test_app,
            ["--file", str(test_file), "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Dry run mode" in result.stdout

    def test_backup_auth_setting(self, runner, monkeypatch, tmp_path):
        """Test backing up auth settings."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_list(*args, **kwargs):
            return [
                {
                    "id": "as-1",
                    "folder": "Mobile Users",
                    "name": "saml-auth",
                    "authentication_profile": "best-practice",
                    "os": "Any",
                },
            ]

        monkeypatch.setattr(scm_client, "list_auth_settings", mock_list)
        monkeypatch.chdir(tmp_path)

        from scm_cli.commands.mobile_agent import backup_auth_setting

        test_app = typer.Typer()
        test_app.command()(backup_auth_setting)

        result = runner.invoke(
            test_app,
            ["--folder", "Mobile Users"],
        )

        assert result.exit_code == 0
        assert "Successfully backed up" in result.stdout
        assert "1 auth settings" in result.stdout

    def test_set_auth_setting_error(self, runner, monkeypatch):
        """Test set auth setting with error."""
        from scm_cli.utils.sdk_client import scm_client

        def mock_error(*args, **kwargs):
            raise Exception("API error")

        monkeypatch.setattr(scm_client, "create_auth_setting", mock_error)

        test_app = typer.Typer()
        test_app.command()(set_auth_setting)

        result = runner.invoke(
            test_app,
            [
                "--folder", "Mobile Users",
                "--name", "fail-auth",
            ],
        )

        assert result.exit_code == 1


class TestShowJsonOutput:
    """Test the --output json format for show commands."""

    def test_show_agent_version_list_json(self, runner, monkeypatch):
        """Test listing agent versions as JSON."""
        import json

        from scm_cli.utils.sdk_client import scm_client

        versions = [
            {"id": "av-1", "folder": "Mobile Users", "name": "5.2.13", "version": "5.2.13", "platform": "Windows"},
            {"id": "av-2", "folder": "Mobile Users", "name": "5.2.12", "version": "5.2.12", "platform": "macOS"},
        ]
        monkeypatch.setattr(scm_client, "list_agent_versions", lambda *a, **k: versions)

        test_app = typer.Typer()
        test_app.command()(show_agent_version)

        result = runner.invoke(test_app, ["--folder", "Mobile Users", "--output", "json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == versions

    def test_show_auth_setting_detail_json(self, runner, monkeypatch):
        """Test showing an auth setting as JSON."""
        import json

        from scm_cli.utils.sdk_client import scm_client

        setting = {
            "id": "as-saml-auth",
            "folder": "Mobile Users",
            "name": "saml-auth",
            "authentication_profile": "best-practice",
            "os": "Any",
        }
        monkeypatch.setattr(scm_client, "get_auth_setting", lambda *a, **k: setting)

        test_app = typer.Typer()
        test_app.command()(show_auth_setting)

        result = runner.invoke(test_app, ["--folder", "Mobile Users", "--name", "saml-auth", "--output", "json"])

        assert result.exit_code == 0
        assert json.loads(result.stdout) == setting

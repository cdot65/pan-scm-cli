"""Tests for explicit mock-mode handling in SCMClient.

Mock mode must only activate when explicitly requested (SCM_MOCK env var or
`mock: true` in settings). Missing credentials must fail loudly with exit
code 1 — never silently fall back to mock data.
"""

import pytest

from src.scm_cli.main import app

CRED_ENV_VARS = [
    "SCM_CLIENT_ID",
    "SCM_CLIENT_SECRET",
    "SCM_TSG_ID",
    "SCM_SCM_CLIENT_ID",
    "SCM_SCM_CLIENT_SECRET",
    "SCM_SCM_TSG_ID",
]


@pytest.fixture
def no_credentials(monkeypatch):
    """Blank out all credential env vars and disable explicit mock mode."""
    for var in CRED_ENV_VARS:
        monkeypatch.setenv(var, "")
    monkeypatch.delenv("SCM_MOCK", raising=False)


class TestNoCredentialsFailsLoudly:
    """Without credentials and without explicit mock, the client must exit 1."""

    def test_client_init_raises_system_exit(self, no_credentials, capsys):
        from src.scm_cli.utils.sdk_client import SCMClient

        with pytest.raises(SystemExit) as exc_info:
            SCMClient()

        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "scm context create" in err
        assert "SCM_MOCK" in err

    def test_cli_command_exits_1_without_creds(self, runner, no_credentials):
        result = runner.invoke(app, ["show", "object", "address", "--folder", "Texas"])

        assert result.exit_code == 1
        # No fake data may reach stdout
        assert "mock-address" not in result.output

    def test_commit_exits_1_without_creds(self, runner, no_credentials):
        result = runner.invoke(app, ["commit", "--folder", "Texas", "--description", "x", "--force"])

        assert result.exit_code == 1
        assert "mock-job-99999" not in result.output


class TestExplicitMockMode:
    """SCM_MOCK enables mock mode explicitly, with or without credentials."""

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
    def test_scm_mock_truthy_enables_mock(self, monkeypatch, no_credentials, value):
        from src.scm_cli.utils.sdk_client import SCMClient

        monkeypatch.setenv("SCM_MOCK", value)
        client = SCMClient()

        assert client.mock is True

    @pytest.mark.parametrize("value", ["0", "false", "no", "off", ""])
    def test_scm_mock_falsy_does_not_enable_mock(self, monkeypatch, no_credentials, value):
        from src.scm_cli.utils.sdk_client import SCMClient

        monkeypatch.setenv("SCM_MOCK", value)
        with pytest.raises(SystemExit):
            SCMClient()

    def test_scm_mock_wins_over_real_credentials(self, monkeypatch):
        from src.scm_cli.utils.sdk_client import SCMClient

        monkeypatch.setenv("SCM_MOCK", "1")
        client = SCMClient()

        assert client.mock is True

    def test_mock_commands_work_with_scm_mock(self, runner, monkeypatch, no_credentials):
        monkeypatch.setenv("SCM_MOCK", "1")
        result = runner.invoke(app, ["commit", "--folder", "Texas", "--description", "x", "--force"])

        assert result.exit_code == 0
        assert "mock-job-99999" in result.output

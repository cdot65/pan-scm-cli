"""Tests for lazy command loading (startup performance).

Importing scm_cli.main must not import the command modules or the heavy
SDK/validator stacks — they load on dispatch of the matching subcommand.
"""

import subprocess
import sys

from src.scm_cli.main import app

HEAVY_MODULES = [
    "scm.client",
    "requests",
    "scm_cli.utils.sdk_client",
    "scm_cli.utils.validators",
    "scm_cli.commands.objects",
    "scm_cli.commands.network",
]


class TestImportLaziness:
    def test_importing_main_does_not_import_heavy_modules(self):
        code = (
            "import sys\n"
            "import scm_cli.main\n"
            f"loaded = [m for m in {HEAVY_MODULES!r} if m in sys.modules]\n"
            "print(','.join(loaded))\n"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)

        assert result.stdout.strip() == "", f"heavy modules imported at startup: {result.stdout.strip()}"

    def test_help_does_not_import_heavy_modules(self):
        code = (
            "import sys\n"
            "from typer.testing import CliRunner\n"
            "from scm_cli.main import app\n"
            "r = CliRunner().invoke(app, ['--help'])\n"
            "assert r.exit_code == 0, r.output\n"
            f"loaded = [m for m in {HEAVY_MODULES!r} if m in sys.modules]\n"
            "print(','.join(loaded))\n"
        )
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)

        assert result.stdout.strip() == "", f"--help imported heavy modules: {result.stdout.strip()}"


class TestHelpListings:
    def test_top_level_help_lists_actions_and_standalones(self, runner):
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        for name in ["set", "delete", "show", "load", "backup", "move", "commit", "context", "jobs", "insights", "incidents", "local", "operations", "posture"]:
            assert name in result.output

    def test_action_help_lists_categories(self, runner):
        result = runner.invoke(app, ["set", "--help"])

        assert result.exit_code == 0
        for name in ["identity", "mobile-agent", "network", "object", "sase", "security", "setup"]:
            assert name in result.output


class TestDispatchStillWorks:
    def test_config_command_dispatches(self, runner, monkeypatch):
        monkeypatch.setenv("SCM_MOCK", "1")
        result = runner.invoke(app, ["show", "object", "address", "--folder", "Texas"])

        assert result.exit_code == 0

    def test_standalone_command_dispatches(self, runner, monkeypatch):
        monkeypatch.setenv("SCM_MOCK", "1")
        result = runner.invoke(app, ["jobs", "list"])

        assert result.exit_code == 0

    def test_subgroup_help_dispatches(self, runner):
        result = runner.invoke(app, ["set", "object", "--help"])

        assert result.exit_code == 0
        assert "address" in result.output

    def test_unknown_command_still_errors(self, runner):
        result = runner.invoke(app, ["set", "nonsense"])

        assert result.exit_code != 0

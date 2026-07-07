"""Tests for context management commands (list, show, create, use, delete, current).

This module provides comprehensive test coverage for all context subcommands
in scm_cli.commands.context, excluding test_command which is covered in
test_auth_command.py.
"""

from scm_cli.main import app

# ############################################################################
# list command
# ############################################################################


class TestListCommand:
    """Tests for 'scm context list'."""

    def test_no_contexts(self, runner, monkeypatch):
        """Empty state shows helpful message."""
        monkeypatch.setattr("scm_cli.commands.context.list_contexts", lambda: [])
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)

        result = runner.invoke(app, ["context", "list"])

        assert result.exit_code == 0
        assert "No contexts found" in result.output

    def test_single_context_active(self, runner, monkeypatch):
        """Single context marked as current shows checkmark."""
        monkeypatch.setattr("scm_cli.commands.context.list_contexts", lambda: ["production"])
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: "production")
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "test-id@example.com", "client_secret": "s", "tsg_id": "t"},
        )

        result = runner.invoke(app, ["context", "list"])

        assert result.exit_code == 0
        assert "production" in result.output

    def test_multiple_contexts(self, runner, monkeypatch):
        """Multiple contexts displayed in table."""
        monkeypatch.setattr(
            "scm_cli.commands.context.list_contexts",
            lambda: ["dev", "production", "staging"],
        )
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: "dev")
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "id@example.com", "client_secret": "s", "tsg_id": "t"},
        )

        result = runner.invoke(app, ["context", "list"])

        assert result.exit_code == 0
        assert "dev" in result.output
        assert "production" in result.output
        assert "staging" in result.output

    def test_no_current_context_set(self, runner, monkeypatch):
        """Contexts exist but none is current — shows hint."""
        monkeypatch.setattr("scm_cli.commands.context.list_contexts", lambda: ["dev"])
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "id", "client_secret": "s", "tsg_id": "t"},
        )

        result = runner.invoke(app, ["context", "list"])

        assert result.exit_code == 0
        assert "No context currently active" in result.output

    def test_config_read_error(self, runner, monkeypatch):
        """Gracefully handles error reading a context config — does not crash."""
        monkeypatch.setattr("scm_cli.commands.context.list_contexts", lambda: ["broken"])
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)

        def raise_error(name):
            raise Exception("corrupt")

        monkeypatch.setattr("scm_cli.commands.context.get_context_config", raise_error)

        result = runner.invoke(app, ["context", "list"])

        assert result.exit_code == 0
        assert "broken" in result.output

    def test_long_client_id_masked(self, runner, monkeypatch):
        """Long client IDs are masked for security."""
        monkeypatch.setattr("scm_cli.commands.context.list_contexts", lambda: ["prod"])
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "a" * 30, "client_secret": "s", "tsg_id": "t"},
        )

        result = runner.invoke(app, ["context", "list"])

        assert result.exit_code == 0
        assert "..." in result.output


# ############################################################################
# show command
# ############################################################################


class TestShowCommand:
    """Tests for 'scm context show'."""

    def test_show_named_context(self, runner, monkeypatch):
        """Show details of a named context."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "test-id", "client_secret": "secret", "tsg_id": "tsg-123"},
        )

        result = runner.invoke(app, ["context", "show", "production"])

        assert result.exit_code == 0
        assert "production" in result.output
        assert "test-id" in result.output
        assert "tsg-123" in result.output

    def test_show_current_context(self, runner, monkeypatch):
        """No argument shows current context."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: "default")
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "id", "client_secret": "s", "tsg_id": "t"},
        )

        result = runner.invoke(app, ["context", "show"])

        assert result.exit_code == 0
        assert "default" in result.output

    def test_show_no_current_context(self, runner, monkeypatch):
        """No argument and no current context shows error and exits non-zero."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)

        result = runner.invoke(app, ["context", "show"])

        assert result.exit_code == 1
        assert "No current context set" in result.output

    def test_show_nonexistent_context(self, runner, monkeypatch):
        """Nonexistent context shows error."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)

        def mock_get_config(name):
            raise ValueError(f"Context '{name}' not found")

        monkeypatch.setattr("scm_cli.commands.context.get_context_config", mock_get_config)

        result = runner.invoke(app, ["context", "show", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_show_bearer_token_context(self, runner, monkeypatch):
        """Context with bearer token shows token auth mode."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"access_token": "bearer-token-123"},
        )

        result = runner.invoke(app, ["context", "show", "bearer-ctx"])

        assert result.exit_code == 0
        assert "Bearer Token" in result.output

    def test_show_active_context_status(self, runner, monkeypatch):
        """Active context shows 'Active' status."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: "prod")
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "id", "client_secret": "s", "tsg_id": "t"},
        )

        result = runner.invoke(app, ["context", "show", "prod"])

        assert result.exit_code == 0
        assert "Active" in result.output

    def test_show_missing_secret(self, runner, monkeypatch):
        """Context missing client_secret shows 'Not set'."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "id", "tsg_id": "t"},
        )

        result = runner.invoke(app, ["context", "show", "incomplete"])

        assert result.exit_code == 0
        assert "Not set" in result.output


# ############################################################################
# create command
# ############################################################################


class TestCreateCommand:
    """Tests for 'scm context create'."""

    def test_create_oauth2_context(self, runner, monkeypatch):
        """Create a context with OAuth2 credentials."""
        monkeypatch.setattr("scm_cli.commands.context.create_context", lambda **kwargs: None)
        monkeypatch.setattr("scm_cli.commands.context.set_current_context", lambda name: None)

        result = runner.invoke(
            app,
            [
                "context",
                "create",
                "new-ctx",
                "--client-id",
                "cid",
                "--client-secret",
                "csecret",
                "--tsg-id",
                "tsg",
            ],
        )

        assert result.exit_code == 0
        assert "created successfully" in result.output

    def test_create_bearer_token_context(self, runner, monkeypatch):
        """Create a context with bearer token."""
        monkeypatch.setattr("scm_cli.commands.context.create_context", lambda **kwargs: None)
        monkeypatch.setattr("scm_cli.commands.context.set_current_context", lambda name: None)

        result = runner.invoke(
            app,
            ["context", "create", "bearer-ctx", "--access-token", "my-token"],
        )

        assert result.exit_code == 0
        assert "created successfully" in result.output

    def test_create_no_credentials(self, runner):
        """Create without any credentials fails."""
        result = runner.invoke(app, ["context", "create", "empty-ctx"])

        assert result.exit_code == 1
        assert "Provide either" in result.output

    def test_create_both_oauth_and_bearer(self, runner):
        """Create with both OAuth2 and bearer token fails."""
        result = runner.invoke(
            app,
            [
                "context",
                "create",
                "dual-ctx",
                "--client-id",
                "cid",
                "--client-secret",
                "csecret",
                "--tsg-id",
                "tsg",
                "--access-token",
                "token",
            ],
        )

        assert result.exit_code == 1
        assert "Cannot use both" in result.output

    def test_create_partial_oauth(self, runner):
        """Create with incomplete OAuth2 credentials fails."""
        result = runner.invoke(
            app,
            ["context", "create", "partial-ctx", "--client-id", "cid"],
        )

        assert result.exit_code == 1
        assert "Missing required" in result.output
        assert "--client-secret" in result.output
        assert "--tsg-id" in result.output

    def test_create_no_set_current(self, runner, monkeypatch):
        """Create with --no-set-current doesn't activate the context."""
        created_contexts = []
        set_current_calls = []

        monkeypatch.setattr(
            "scm_cli.commands.context.create_context",
            lambda **kwargs: created_contexts.append(kwargs),
        )
        monkeypatch.setattr(
            "scm_cli.commands.context.set_current_context",
            lambda name: set_current_calls.append(name),
        )

        result = runner.invoke(
            app,
            [
                "context",
                "create",
                "new-ctx",
                "--client-id",
                "cid",
                "--client-secret",
                "csecret",
                "--tsg-id",
                "tsg",
                "--no-set-current",
            ],
        )

        assert result.exit_code == 0
        assert len(created_contexts) == 1
        assert len(set_current_calls) == 0

    def test_create_exception(self, runner, monkeypatch):
        """Create handles unexpected errors."""

        def mock_create(**kwargs):
            raise Exception("disk full")

        monkeypatch.setattr("scm_cli.commands.context.create_context", mock_create)

        result = runner.invoke(
            app,
            [
                "context",
                "create",
                "fail-ctx",
                "--client-id",
                "cid",
                "--client-secret",
                "csecret",
                "--tsg-id",
                "tsg",
            ],
        )

        assert result.exit_code == 1
        assert "Error creating context" in result.output


# ############################################################################
# use command
# ############################################################################


class TestUseCommand:
    """Tests for 'scm context use'."""

    def test_use_existing_context(self, runner, monkeypatch):
        """Switch to an existing context."""
        monkeypatch.setattr("scm_cli.commands.context.set_current_context", lambda name: None)
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "id", "tsg_id": "tsg"},
        )

        result = runner.invoke(app, ["context", "use", "production"])

        assert result.exit_code == 0
        assert "Switched to context" in result.output
        assert "production" in result.output

    def test_use_nonexistent_context_no_alternatives(self, runner, monkeypatch):
        """Switch to nonexistent context with no alternatives."""

        def mock_set(name):
            raise ValueError(f"Context '{name}' not found")

        monkeypatch.setattr("scm_cli.commands.context.set_current_context", mock_set)
        monkeypatch.setattr("scm_cli.commands.context.list_contexts", lambda: [])

        result = runner.invoke(app, ["context", "use", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.output
        assert "No contexts found" in result.output

    def test_use_nonexistent_context_with_alternatives(self, runner, monkeypatch):
        """Switch to nonexistent context shows available alternatives."""

        def mock_set(name):
            raise ValueError(f"Context '{name}' not found")

        monkeypatch.setattr("scm_cli.commands.context.set_current_context", mock_set)
        monkeypatch.setattr("scm_cli.commands.context.list_contexts", lambda: ["dev", "staging"])

        result = runner.invoke(app, ["context", "use", "nonexistent"])

        assert result.exit_code == 1
        assert "Available contexts" in result.output
        assert "dev" in result.output
        assert "staging" in result.output


# ############################################################################
# delete command
# ############################################################################


class TestDeleteCommand:
    """Tests for 'scm context delete'."""

    def test_delete_with_force(self, runner, monkeypatch):
        """Delete with --force skips confirmation."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)
        monkeypatch.setattr("scm_cli.commands.context.delete_context", lambda name: None)

        result = runner.invoke(app, ["context", "delete", "old-ctx", "--force"])

        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_delete_confirm_yes(self, runner, monkeypatch):
        """Delete with confirmation accepted."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)
        monkeypatch.setattr("scm_cli.commands.context.delete_context", lambda name: None)

        result = runner.invoke(app, ["context", "delete", "old-ctx"], input="y\n")

        assert result.exit_code == 0
        assert "deleted" in result.output

    def test_delete_confirm_no(self, runner, monkeypatch):
        """Delete with confirmation declined."""
        result = runner.invoke(app, ["context", "delete", "old-ctx"], input="n\n")

        assert result.exit_code == 0
        assert "cancelled" in result.output.lower()

    def test_delete_nonexistent(self, runner, monkeypatch):
        """Delete nonexistent context shows error."""

        def mock_delete(name):
            raise ValueError(f"Context '{name}' not found")

        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)
        monkeypatch.setattr("scm_cli.commands.context.delete_context", mock_delete)

        result = runner.invoke(app, ["context", "delete", "ghost", "--force"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_delete_current_context_warns(self, runner, monkeypatch):
        """Deleting the current context shows a warning."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: "active-ctx")
        monkeypatch.setattr("scm_cli.commands.context.delete_context", lambda name: None)

        result = runner.invoke(app, ["context", "delete", "active-ctx", "--force"])

        assert result.exit_code == 0
        assert "current context" in result.output.lower()


# ############################################################################
# current command
# ############################################################################


class TestCurrentCommand:
    """Tests for 'scm context current'."""

    def test_current_context_set(self, runner, monkeypatch):
        """Shows current context when one is set."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: "production")
        monkeypatch.setattr(
            "scm_cli.commands.context.get_context_config",
            lambda name: {"client_id": "id", "tsg_id": "tsg-123"},
        )

        result = runner.invoke(app, ["context", "current"])

        assert result.exit_code == 0
        assert "production" in result.output
        assert "tsg-123" in result.output

    def test_current_context_not_set(self, runner, monkeypatch):
        """Shows helpful message when no context is set."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: None)

        result = runner.invoke(app, ["context", "current"])

        assert result.exit_code == 0
        assert "No current context set" in result.output

    def test_current_context_config_error(self, runner, monkeypatch):
        """Handles error reading current context config."""
        monkeypatch.setattr("scm_cli.commands.context.get_current_context", lambda: "broken")

        def raise_error(name):
            raise Exception("corrupt file")

        monkeypatch.setattr("scm_cli.commands.context.get_context_config", raise_error)

        result = runner.invoke(app, ["context", "current"])

        assert result.exit_code == 0
        assert "Error reading context configuration" in result.output

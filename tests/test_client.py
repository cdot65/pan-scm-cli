"""Tests for the client module."""

from unittest.mock import MagicMock, patch

import pytest
from scm.exceptions import AuthenticationError

from scm_cli.client import MockSCMClient, get_scm_client


class TestMockSCMClient:
    """Tests for the MockSCMClient class."""

    def test_init_sets_auth_credentials(self):
        """MockSCMClient sets mock auth credentials on init."""
        client = MockSCMClient()
        assert client._auth_user_credentials == {"mock": True}

    def test_getattr_crud_returns_callable(self):
        """Accessing CRUD method names returns a callable, not a nested MockSCMClient."""
        client = MockSCMClient()
        for method in ["list", "create", "update", "delete"]:
            result = getattr(client, method)
            assert callable(result)
            assert not isinstance(result, MockSCMClient)

    def test_getattr_non_crud_returns_mock_client(self):
        """Accessing non-CRUD attributes returns a new MockSCMClient instance."""
        client = MockSCMClient()
        result = client.some_service
        assert isinstance(result, MockSCMClient)

    def test_mock_callable_returns_success_dict(self):
        """CRUD callables return a success dict with status and message."""
        client = MockSCMClient()
        result = client.create("arg1", key="val")
        assert result == {"status": "success", "message": "Mock call to create"}

    def test_mock_callable_includes_method_name(self):
        """Each CRUD callable includes its method name in the response message."""
        client = MockSCMClient()
        for method in ["list", "create", "update", "delete"]:
            result = getattr(client, method)()
            assert method in result["message"]

    def test_chained_access(self):
        """Non-CRUD attribute access can be chained since it returns MockSCMClient."""
        client = MockSCMClient()
        result = client.address.create(name="test")
        assert result["status"] == "success"


class TestGetScmClient:
    """Tests for the get_scm_client function."""

    def test_mock_true_returns_mock_client(self):
        """get_scm_client(mock=True) returns a MockSCMClient."""
        client = get_scm_client(mock=True)
        assert isinstance(client, MockSCMClient)

    @patch("scm_cli.client.get_current_context", return_value="production")
    @patch("scm_cli.client.get_auth_config", return_value={"client_id": "id", "client_secret": "secret", "tsg_id": "123"})
    @patch("scm_cli.client.Scm")
    def test_real_client_with_context(self, mock_scm, mock_auth, mock_ctx):
        """get_scm_client with a context set initializes Scm with auth params."""
        mock_scm.return_value = MagicMock()
        client = get_scm_client(mock=False)
        mock_scm.assert_called_once_with(client_id="id", client_secret="secret", tsg_id="123")
        assert client == mock_scm.return_value

    @patch("scm_cli.client.get_current_context", return_value=None)
    @patch("scm_cli.client.get_auth_config", return_value={"client_id": "id", "client_secret": "secret", "tsg_id": "456"})
    @patch("scm_cli.client.Scm")
    def test_real_client_without_context(self, mock_scm, mock_auth, mock_ctx):
        """get_scm_client without a context still initializes successfully."""
        mock_scm.return_value = MagicMock()
        client = get_scm_client(mock=False)
        mock_scm.assert_called_once_with(client_id="id", client_secret="secret", tsg_id="456")
        assert client == mock_scm.return_value

    @patch("scm_cli.client.get_current_context", return_value=None)
    @patch("scm_cli.client.get_auth_config", return_value={"client_id": "id", "client_secret": "secret", "tsg_id": "789"})
    @patch("scm_cli.client.Scm", side_effect=AuthenticationError("Invalid credentials"))
    def test_authentication_error_raised(self, mock_scm, mock_auth, mock_ctx):
        """get_scm_client raises AuthenticationError on auth failure."""
        with pytest.raises(AuthenticationError):
            get_scm_client(mock=False)

    @patch("scm_cli.client.get_current_context", return_value=None)
    @patch("scm_cli.client.get_auth_config", return_value={"client_id": "id", "client_secret": "secret", "tsg_id": "000"})
    @patch("scm_cli.client.Scm", side_effect=RuntimeError("Connection failed"))
    def test_generic_exception_raised(self, mock_scm, mock_auth, mock_ctx):
        """get_scm_client raises generic exceptions from Scm initialization."""
        with pytest.raises(RuntimeError, match="Connection failed"):
            get_scm_client(mock=False)

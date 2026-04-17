"""Tests for timeout error handling."""

import pytest

from src.scm_cli.utils.sdk_client import SCMClient


class TestGatewayTimeoutError:
    """Test GatewayTimeoutError is handled properly."""

    def test_handle_gateway_timeout_logs_and_reraises(self):
        """_handle_api_exception logs GatewayTimeoutError with timeout-specific message."""
        from scm.exceptions import GatewayTimeoutError

        client = SCMClient.__new__(SCMClient)
        client.logger = __import__("logging").getLogger("test")
        client.client = None

        exc = GatewayTimeoutError(message="gateway timeout", http_status_code=504)

        with pytest.raises(GatewayTimeoutError):
            client._handle_api_exception("dispatch", "N/A", "route-table", exc)

    def test_handle_session_timeout_logs_and_reraises(self):
        """_handle_api_exception logs SessionTimeoutError (subclass of GatewayTimeoutError)."""
        from scm.exceptions import SessionTimeoutError

        client = SCMClient.__new__(SCMClient)
        client.logger = __import__("logging").getLogger("test")
        client.client = None

        exc = SessionTimeoutError(message="session timeout", http_status_code=504)

        with pytest.raises(SessionTimeoutError):
            client._handle_api_exception("dispatch", "N/A", "route-table", exc)

    def test_gateway_timeout_log_message_content(self, caplog):
        """Verify the log message contains timeout-specific details."""
        import logging

        from scm.exceptions import GatewayTimeoutError

        client = SCMClient.__new__(SCMClient)
        client.logger = logging.getLogger("test_timeout_msg")
        client.client = None

        exc = GatewayTimeoutError(message="gateway timeout", http_status_code=504)

        with caplog.at_level(logging.ERROR, logger="test_timeout_msg"), pytest.raises(GatewayTimeoutError):
            client._handle_api_exception("create", "Texas", "fw-rule-01", exc)

        assert "timed out" in caplog.text
        assert "fw-rule-01" in caplog.text
        assert "create" in caplog.text

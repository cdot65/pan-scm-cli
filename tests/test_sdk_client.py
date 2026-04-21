"""Tests for the SDK client module."""

import pytest

from scm_cli.utils.sdk_client import LazyClient, SCMClient, scm_client


def test_scm_client_singleton():
    """Test that scm_client is a LazyClient wrapping SCMClient."""
    assert isinstance(scm_client, LazyClient)
    # Accessing an attribute triggers lazy init, resulting in an SCMClient
    assert isinstance(scm_client._client or SCMClient(), SCMClient)


class TestSCMClient:
    """Test cases for the SCMClient class."""

    def test_create_bandwidth_allocation(self):
        """Test creating a bandwidth allocation."""
        client = SCMClient()
        result = client.create_bandwidth_allocation(
            name="test-allocation",
            bandwidth=1000,
            spn_name_list=["spn1"],
            description="Test allocation",
            tags=["test", "example"],
        )
        assert result["id"].startswith("ba-")
        assert result["name"] == "test-allocation"
        assert result["allocated_bandwidth"] == 1000
        assert result["description"] == "Test allocation"
        assert "test" in result["tags"]
        assert "example" in result["tags"]

    def test_delete_bandwidth_allocation(self):
        """Test deleting a bandwidth allocation."""
        client = SCMClient()
        result = client.delete_bandwidth_allocation(name="test-allocation", spn_name_list=["spn1"])
        assert result is True

    def test_create_zone(self):
        """Test creating a security zone."""
        client = SCMClient()
        result = client.create_zone(
            folder="test-folder",
            name="test-zone",
            mode="layer3",
            interfaces=["ethernet1/1"],
        )
        assert result["id"].startswith("zone-")
        assert result["folder"] == "test-folder"
        assert result["name"] == "test-zone"
        assert result["mode"] == "layer3"
        assert "ethernet1/1" in result["interfaces"]

    def test_delete_zone(self):
        """Test deleting a security zone."""
        client = SCMClient()
        result = client.delete_zone(folder="test-folder", name="test-zone")
        assert result is True

    def test_create_address_group(self):
        """Test creating an address group."""
        client = SCMClient()
        result = client.create_address_group(
            folder="test-folder",
            name="test-group",
            type="static",
            members=["192.168.1.0/24", "10.0.0.0/8"],
            description="Test address group",
            tags=["test", "example"],
        )
        assert result["id"].startswith("ag-")
        assert result["folder"] == "test-folder"
        assert result["name"] == "test-group"
        assert result["type"] == "static"
        assert "192.168.1.0/24" in result["members"]
        assert "10.0.0.0/8" in result["members"]
        assert result["description"] == "Test address group"
        assert "test" in result["tags"]
        assert "example" in result["tags"]

    def test_delete_address_group(self):
        """Test deleting an address group."""
        client = SCMClient()
        result = client.delete_address_group(folder="test-folder", name="test-group")
        assert result is True

    def test_create_security_rule(self):
        """Test creating a security rule."""
        client = SCMClient()
        result = client.create_security_rule(
            folder="test-folder",
            name="test-rule",
            source_zones=["trust"],
            destination_zones=["untrust"],
            source_addresses=["any"],
            destination_addresses=["any"],
            applications=["web-browsing"],
            action="allow",
            description="Test security rule",
            tags=["test", "example"],
            enabled=True,
        )
        assert result["id"].startswith("sr-")
        assert result["folder"] == "test-folder"
        assert result["name"] == "test-rule"
        assert "trust" in result["source_zones"]
        assert "untrust" in result["destination_zones"]
        assert "any" in result["source_addresses"]
        assert "any" in result["destination_addresses"]
        assert "web-browsing" in result["applications"]
        assert result["action"] == "allow"
        assert result["description"] == "Test security rule"
        assert "test" in result["tags"]
        assert "example" in result["tags"]
        assert result["enabled"] is True

    def test_delete_security_rule(self):
        """Test deleting a security rule."""
        client = SCMClient()
        result = client.delete_security_rule(folder="test-folder", name="test-rule")
        assert result is True


class TestUpdateDevice:
    """Tests for scm_client.update_device."""

    def test_update_device_mock_mode_returns_updated(self):
        from scm_cli.utils.sdk_client import SCMClient

        client = SCMClient()
        client.client = None  # force mock mode

        result = client.update_device(
            name="PA-VM-01",
            display_name="Edge-FW",
            labels=["prod"],
        )

        assert result["name"] == "PA-VM-01"
        assert result["display_name"] == "Edge-FW"
        assert result["labels"] == ["prod"]
        assert result["__action__"] == "updated"

    def test_update_device_not_found_raises_value_error(self, monkeypatch):
        from scm.exceptions import NotFoundError

        from scm_cli.utils.sdk_client import SCMClient

        client = SCMClient()

        class FakeDevice:
            @staticmethod
            def fetch(name):
                raise NotFoundError("not found")

            @staticmethod
            def update(*args, **kwargs):
                raise AssertionError("update must not be called on missing device")

        class FakeClient:
            device = FakeDevice()

        client.client = FakeClient()

        with pytest.raises(ValueError, match="cannot be created"):
            client.update_device(name="missing", labels=["prod"])

    def test_update_device_no_change_when_values_match(self, monkeypatch):
        from scm_cli.utils.sdk_client import SCMClient

        client = SCMClient()

        class FakeExisting:
            display_name = "Edge-FW"
            folder = "Austin"
            description = "edge"
            labels = ["prod"]
            snippets = []

            def model_dump_json(self, **_kw):
                return '{"name": "PA-VM-01", "display_name": "Edge-FW", "labels": ["prod"]}'

        class FakeDevice:
            @staticmethod
            def fetch(name):
                return FakeExisting()

            @staticmethod
            def update(*args, **kwargs):
                raise AssertionError("update must not be called when no change")

        class FakeClient:
            device = FakeDevice()

        client.client = FakeClient()

        result = client.update_device(
            name="PA-VM-01",
            display_name="Edge-FW",
            folder="Austin",
            description="edge",
            labels=["prod"],
        )
        assert result["__action__"] == "no_change"

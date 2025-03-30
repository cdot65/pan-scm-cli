"""Tests for the SDK client module."""

from scm_cli.utils.sdk_client import SCMClient, scm_client


def test_scm_client_singleton():
    """Test that scm_client is a singleton instance of SCMClient."""
    assert isinstance(scm_client, SCMClient)
    # Check that creating a new instance doesn't replace the singleton
    new_client = SCMClient()
    assert new_client is not scm_client


class TestSCMClient:
    """Test cases for the SCMClient class."""

    def test_create_bandwidth_allocation(self):
        """Test creating a bandwidth allocation."""
        client = SCMClient()
        result = client.create_bandwidth_allocation(
            folder="test-folder",
            name="test-allocation",
            bandwidth=1000,
            description="Test allocation",
            tags=["test", "example"],
        )
        assert result["id"].startswith("ba-")
        assert result["folder"] == "test-folder"
        assert result["name"] == "test-allocation"
        assert result["bandwidth"] == 1000
        assert result["description"] == "Test allocation"
        assert "test" in result["tags"]
        assert "example" in result["tags"]

    def test_delete_bandwidth_allocation(self):
        """Test deleting a bandwidth allocation."""
        client = SCMClient()
        result = client.delete_bandwidth_allocation(folder="test-folder", name="test-allocation")
        assert result is True

    def test_create_zone(self):
        """Test creating a security zone."""
        client = SCMClient()
        result = client.create_zone(
            folder="test-folder",
            name="test-zone",
            mode="L3",
            interfaces=["ethernet1/1"],
            description="Test zone",
            tags=["test", "example"],
        )
        assert result["id"].startswith("zone-")
        assert result["folder"] == "test-folder"
        assert result["name"] == "test-zone"
        assert result["mode"] == "L3"
        assert "ethernet1/1" in result["interfaces"]
        assert result["description"] == "Test zone"
        assert "test" in result["tags"]
        assert "example" in result["tags"]

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

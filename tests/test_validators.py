"""Tests for the validators module."""

import pytest
from pydantic import ValidationError

from scm_cli.utils.validators import (
    AddressGroup,
    AggregateInterface,
    AppOverrideRule,
    AuthenticationRule,
    BandwidthAllocation,
    BgpAddressFamilyProfile,
    BgpAuthProfile,
    BgpFilteringProfile,
    BgpRedistributionProfile,
    BgpRouteMap,
    BgpRouteMapRedistribution,
    BGPRouting,
    DecryptionRule,
    DhcpInterface,
    DNSSecurityProfile,
    EthernetInterface,
    IKECryptoProfile,
    IKEGateway,
    InternalDNSServer,
    IPSecCryptoProfile,
    Layer2Subinterface,
    Layer3Subinterface,
    LoopbackInterface,
    NATRule,
    OspfAuthProfile,
    QuarantinedDevice,
    Region,
    RouteAccessList,
    RoutePrefixList,
    Schedule,
    SecurityRule,
    TunnelInterface,
    URLAccessProfile,
    URLCategory,
    VlanInterface,
    VulnerabilityProtectionProfile,
    WildfireAntivirusProfile,
    Zone,
)


class TestBandwidthAllocation:
    """Test cases for the BandwidthAllocation model."""

    def test_valid_bandwidth_allocation(self):
        """Test creating a valid bandwidth allocation."""
        allocation = BandwidthAllocation(
            name="test-allocation",
            folder="test-folder",
            bandwidth=1000,
            description="Test allocation",
            tags=["test", "example"],
        )
        assert allocation.name == "test-allocation"
        assert allocation.folder == "test-folder"
        assert allocation.bandwidth == 1000
        assert allocation.description == "Test allocation"
        assert allocation.tags == ["test", "example"]

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            BandwidthAllocation(
                name="test-allocation",
                # Missing folder
                bandwidth=1000,
            )

        with pytest.raises(ValidationError):
            BandwidthAllocation(
                # Missing name
                folder="test-folder",
                bandwidth=1000,
            )

        with pytest.raises(ValidationError):
            BandwidthAllocation(
                name="test-allocation",
                folder="test-folder",
                # Missing bandwidth
            )

    def test_default_values(self):
        """Test that default values are applied correctly."""
        allocation = BandwidthAllocation(
            name="test-allocation",
            folder="test-folder",
            bandwidth=1000,
        )
        assert allocation.description == ""
        assert allocation.tags == []


class TestIKECryptoProfile:
    """Test cases for the IKECryptoProfile model."""

    def test_valid_ike_crypto_profile(self):
        """Test creating a valid IKE crypto profile."""
        profile = IKECryptoProfile(name="test-profile", folder="test-folder", hash=["sha256"], dh_group=["group14"], encryption=["aes-256-cbc"], lifetime_hours=8)
        assert profile.name == "test-profile"
        assert profile.folder == "test-folder"
        assert profile.hash == ["sha256"]
        assert profile.dh_group == ["group14"]
        assert profile.encryption == ["aes-256-cbc"]
        assert profile.lifetime_hours == 8

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            IKECryptoProfile(name="test-profile", folder="test-folder")

    def test_invalid_hash(self):
        """Test that invalid hash algorithms are rejected."""
        with pytest.raises(ValidationError):
            IKECryptoProfile(name="test-profile", folder="test-folder", hash=["invalid-hash"], dh_group=["group14"], encryption=["aes-256-cbc"])

    def test_invalid_dh_group(self):
        """Test that invalid DH groups are rejected."""
        with pytest.raises(ValidationError):
            IKECryptoProfile(name="test-profile", folder="test-folder", hash=["sha256"], dh_group=["group99"], encryption=["aes-256-cbc"])

    def test_invalid_encryption(self):
        """Test that invalid encryption algorithms are rejected."""
        with pytest.raises(ValidationError):
            IKECryptoProfile(name="test-profile", folder="test-folder", hash=["sha256"], dh_group=["group14"], encryption=["invalid-enc"])

    def test_multiple_lifetime_rejected(self):
        """Test that setting multiple lifetime fields is rejected."""
        with pytest.raises(ValidationError):
            IKECryptoProfile(name="test-profile", folder="test-folder", hash=["sha256"], dh_group=["group14"], encryption=["aes-256-cbc"], lifetime_hours=8, lifetime_days=1)

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            IKECryptoProfile(name="test-profile", hash=["sha256"], dh_group=["group14"], encryption=["aes-256-cbc"])

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = IKECryptoProfile(
            name="test-profile", folder="test-folder", hash=["sha256", "sha384"], dh_group=["group14", "group19"], encryption=["aes-256-cbc"], lifetime_hours=8, authentication_multiple=3
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "test-profile"
        assert sdk_data["folder"] == "test-folder"
        assert sdk_data["hash"] == ["sha256", "sha384"]
        assert sdk_data["dh_group"] == ["group14", "group19"]
        assert sdk_data["encryption"] == ["aes-256-cbc"]
        assert sdk_data["lifetime"] == {"hours": 8}
        assert sdk_data["authentication_multiple"] == 3

    def test_to_sdk_model_no_lifetime(self):
        """Test conversion to SDK model without lifetime."""
        profile = IKECryptoProfile(name="test-profile", folder="test-folder", hash=["sha256"], dh_group=["group14"], encryption=["aes-256-cbc"])
        sdk_data = profile.to_sdk_model()
        assert "lifetime" not in sdk_data


class TestIKEGateway:
    """Test cases for the IKEGateway model."""

    def test_valid_ike_gateway(self):
        """Test creating a valid IKE gateway."""
        gw = IKEGateway(
            name="test-gw",
            folder="test-folder",
            authentication={"pre_shared_key": {"key": "my-secret-key"}},
            peer_address={"ip": "203.0.113.1"},
            protocol={"version": "ikev2-preferred", "ikev1": {"ike_crypto_profile": "default"}, "ikev2": {"ike_crypto_profile": "default"}},
        )
        assert gw.name == "test-gw"
        assert gw.folder == "test-folder"
        assert gw.authentication == {"pre_shared_key": {"key": "my-secret-key"}}
        assert gw.peer_address == {"ip": "203.0.113.1"}

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            IKEGateway(name="test-gw", folder="test-folder", authentication={"pre_shared_key": {"key": "k"}}, peer_address={"ip": "1.2.3.4"})

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            IKEGateway(
                name="test-gw",
                authentication={"pre_shared_key": {"key": "k"}},
                peer_address={"ip": "1.2.3.4"},
                protocol={"version": "ikev2"},
            )

    def test_dual_container_rejected(self):
        """Test that two containers are rejected."""
        with pytest.raises(ValidationError):
            IKEGateway(
                name="test-gw",
                folder="f",
                snippet="s",
                authentication={"pre_shared_key": {"key": "k"}},
                peer_address={"ip": "1.2.3.4"},
                protocol={"version": "ikev2", "ikev2": {}},
            )

    def test_invalid_auth_missing(self):
        """Test that missing auth method is rejected."""
        with pytest.raises(ValidationError):
            IKEGateway(
                name="test-gw",
                folder="f",
                authentication={},
                peer_address={"ip": "1.2.3.4"},
                protocol={"version": "ikev2", "ikev2": {}},
            )

    def test_invalid_auth_both(self):
        """Test that both auth methods are rejected."""
        with pytest.raises(ValidationError):
            IKEGateway(
                name="test-gw",
                folder="f",
                authentication={"pre_shared_key": {"key": "k"}, "certificate": {}},
                peer_address={"ip": "1.2.3.4"},
                protocol={"version": "ikev2", "ikev2": {}},
            )

    def test_invalid_psk_missing_key(self):
        """Test that pre_shared_key without key is rejected."""
        with pytest.raises(ValidationError):
            IKEGateway(
                name="test-gw",
                folder="f",
                authentication={"pre_shared_key": {}},
                peer_address={"ip": "1.2.3.4"},
                protocol={"version": "ikev2", "ikev2": {}},
            )

    def test_invalid_peer_address_none(self):
        """Test that peer_address with no valid type is rejected."""
        with pytest.raises(ValidationError):
            IKEGateway(
                name="test-gw",
                folder="f",
                authentication={"pre_shared_key": {"key": "k"}},
                peer_address={"invalid": "x"},
                protocol={"version": "ikev2", "ikev2": {}},
            )

    def test_invalid_protocol_version(self):
        """Test that invalid protocol version is rejected."""
        with pytest.raises(ValidationError):
            IKEGateway(
                name="test-gw",
                folder="f",
                authentication={"pre_shared_key": {"key": "k"}},
                peer_address={"ip": "1.2.3.4"},
                protocol={"version": "ikev3"},
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        gw = IKEGateway(
            name="test-gw",
            folder="test-folder",
            authentication={"pre_shared_key": {"key": "secret"}},
            peer_address={"ip": "203.0.113.1"},
            protocol={"version": "ikev2-preferred", "ikev2": {"ike_crypto_profile": "default"}},
            peer_id={"type": "fqdn", "id": "peer.example.com"},
            local_id={"type": "fqdn", "id": "local.example.com"},
            protocol_common={"nat_traversal": {"enable": True}, "fragmentation": {"enable": False}},
        )
        sdk_data = gw.to_sdk_model()
        assert sdk_data["name"] == "test-gw"
        assert sdk_data["folder"] == "test-folder"
        assert sdk_data["authentication"] == {"pre_shared_key": {"key": "secret"}}
        assert sdk_data["peer_address"] == {"ip": "203.0.113.1"}
        assert sdk_data["protocol"]["version"] == "ikev2-preferred"
        assert sdk_data["peer_id"] == {"type": "fqdn", "id": "peer.example.com"}
        assert sdk_data["local_id"] == {"type": "fqdn", "id": "local.example.com"}
        assert sdk_data["protocol_common"]["nat_traversal"]["enable"] is True

    def test_to_sdk_model_minimal(self):
        """Test conversion without optional fields."""
        gw = IKEGateway(
            name="test-gw",
            folder="f",
            authentication={"pre_shared_key": {"key": "k"}},
            peer_address={"fqdn": "vpn.example.com"},
            protocol={"version": "ikev2", "ikev2": {"ike_crypto_profile": "default"}},
        )
        sdk_data = gw.to_sdk_model()
        assert "peer_id" not in sdk_data
        assert "local_id" not in sdk_data
        assert "protocol_common" not in sdk_data
        assert sdk_data["peer_address"] == {"fqdn": "vpn.example.com"}

    def test_fqdn_peer_address(self):
        """Test FQDN peer address type."""
        gw = IKEGateway(
            name="test-gw",
            folder="f",
            authentication={"pre_shared_key": {"key": "k"}},
            peer_address={"fqdn": "vpn.example.com"},
            protocol={"version": "ikev2", "ikev2": {}},
        )
        assert gw.peer_address == {"fqdn": "vpn.example.com"}

    def test_dynamic_peer_address(self):
        """Test dynamic peer address type."""
        gw = IKEGateway(
            name="test-gw",
            folder="f",
            authentication={"pre_shared_key": {"key": "k"}},
            peer_address={"dynamic": {}},
            protocol={"version": "ikev2", "ikev2": {}},
        )
        assert gw.peer_address == {"dynamic": {}}


class TestZone:
    """Test cases for the Zone model."""

    def test_valid_zone(self):
        """Test creating a valid zone."""
        zone = Zone(
            name="test-zone",
            folder="test-folder",
            mode="L3",
            interfaces=["ethernet1/1"],
            description="Test zone",
            tags=["test", "example"],
        )
        assert zone.name == "test-zone"
        assert zone.folder == "test-folder"
        assert zone.mode == "L3"
        assert zone.interfaces == ["ethernet1/1"]
        assert zone.description == "Test zone"
        assert zone.tags == ["test", "example"]

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            Zone(
                name="test-zone",
                # Missing folder
                mode="L3",
            )

        with pytest.raises(ValidationError):
            Zone(
                # Missing name
                folder="test-folder",
                mode="L3",
            )

        with pytest.raises(ValidationError):
            Zone(
                name="test-zone",
                folder="test-folder",
                # Missing mode
            )

    def test_default_values(self):
        """Test that default values are applied correctly."""
        zone = Zone(name="test-zone", folder="test-folder", mode="L3")
        assert zone.interfaces == []
        assert zone.description == ""
        assert zone.tags == []


class TestAddressGroup:
    """Test cases for the AddressGroup model."""

    def test_valid_address_group(self):
        """Test creating a valid address group."""
        address_group = AddressGroup(
            name="test-group",
            folder="test-folder",
            type="static",
            members=["192.168.1.0/24", "10.0.0.0/8"],
            description="Test address group",
            tags=["test", "example"],
        )
        assert address_group.name == "test-group"
        assert address_group.folder == "test-folder"
        assert address_group.type == "static"
        assert address_group.members == ["192.168.1.0/24", "10.0.0.0/8"]
        assert address_group.description == "Test address group"
        assert address_group.tags == ["test", "example"]

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            AddressGroup(
                name="test-group",
                # Missing folder
                type="static",
            )

        with pytest.raises(ValidationError):
            AddressGroup(
                # Missing name
                folder="test-folder",
                type="static",
            )

        with pytest.raises(ValidationError):
            AddressGroup(
                name="test-group",
                folder="test-folder",
                # Missing type
            )

    def test_default_values(self):
        """Test that default values are applied correctly."""
        address_group = AddressGroup(name="test-group", folder="test-folder", type="static")
        assert address_group.members == []
        assert address_group.description == ""
        assert address_group.tags == []


class TestSchedule:
    """Test cases for the Schedule model."""

    def test_valid_recurring_daily(self):
        """Test creating a valid recurring daily schedule."""
        schedule = Schedule(
            name="business-hours",
            folder="Texas",
            schedule_type="recurring-daily",
            time_ranges=["09:00-17:00"],
        )
        assert schedule.name == "business-hours"
        assert schedule.folder == "Texas"
        assert schedule.schedule_type == "recurring-daily"
        assert schedule.time_ranges == ["09:00-17:00"]

    def test_valid_recurring_weekly(self):
        """Test creating a valid recurring weekly schedule."""
        schedule = Schedule(
            name="weekday-hours",
            folder="Texas",
            schedule_type="recurring-weekly",
            days={"monday": ["09:00-17:00"], "friday": ["09:00-12:00"]},
        )
        assert schedule.name == "weekday-hours"
        assert schedule.schedule_type == "recurring-weekly"
        assert schedule.days == {"monday": ["09:00-17:00"], "friday": ["09:00-12:00"]}

    def test_valid_non_recurring(self):
        """Test creating a valid non-recurring schedule."""
        schedule = Schedule(
            name="maintenance",
            folder="Texas",
            schedule_type="non-recurring",
            time_ranges=["2026/03/15@02:00-2026/03/15@06:00"],
        )
        assert schedule.name == "maintenance"
        assert schedule.schedule_type == "non-recurring"

    def test_invalid_schedule_type(self):
        """Test that invalid schedule type raises error."""
        with pytest.raises(ValidationError):
            Schedule(
                name="test",
                folder="Texas",
                schedule_type="invalid",
                time_ranges=["09:00-17:00"],
            )

    def test_missing_time_ranges_for_daily(self):
        """Test that missing time_ranges for daily raises error."""
        with pytest.raises(ValidationError):
            Schedule(
                name="test",
                folder="Texas",
                schedule_type="recurring-daily",
            )

    def test_missing_days_for_weekly(self):
        """Test that missing days for weekly raises error."""
        with pytest.raises(ValidationError):
            Schedule(
                name="test",
                folder="Texas",
                schedule_type="recurring-weekly",
            )

    def test_to_sdk_model_daily(self):
        """Test SDK model conversion for daily schedule."""
        schedule = Schedule(
            name="daily-sched",
            folder="Texas",
            schedule_type="recurring-daily",
            time_ranges=["09:00-17:00", "18:00-22:00"],
        )
        sdk = schedule.to_sdk_model()
        assert sdk["name"] == "daily-sched"
        assert sdk["folder"] == "Texas"
        assert sdk["schedule_type"]["recurring"]["daily"] == ["09:00-17:00", "18:00-22:00"]

    def test_to_sdk_model_weekly(self):
        """Test SDK model conversion for weekly schedule."""
        schedule = Schedule(
            name="weekly-sched",
            folder="Texas",
            schedule_type="recurring-weekly",
            days={"monday": ["09:00-17:00"]},
        )
        sdk = schedule.to_sdk_model()
        assert sdk["schedule_type"]["recurring"]["weekly"] == {"monday": ["09:00-17:00"]}

    def test_to_sdk_model_non_recurring(self):
        """Test SDK model conversion for non-recurring schedule."""
        schedule = Schedule(
            name="maint",
            folder="Texas",
            schedule_type="non-recurring",
            time_ranges=["2026/03/15@02:00-2026/03/15@06:00"],
        )
        sdk = schedule.to_sdk_model()
        assert sdk["schedule_type"]["non_recurring"] == ["2026/03/15@02:00-2026/03/15@06:00"]

    def test_container_validation(self):
        """Test container field validation."""
        with pytest.raises(ValidationError):
            Schedule(
                name="test",
                folder="Texas",
                snippet="MySnippet",
                schedule_type="recurring-daily",
                time_ranges=["09:00-17:00"],
            )


class TestRegion:
    """Test cases for the Region model."""

    def test_valid_region(self):
        """Test creating a valid region."""
        region = Region(
            name="US-South",
            folder="Texas",
            latitude=30.2672,
            longitude=-97.7431,
            addresses=["10.0.0.0/8", "192.168.1.0/24"],
        )
        assert region.name == "US-South"
        assert region.folder == "Texas"
        assert region.latitude == 30.2672
        assert region.longitude == -97.7431
        assert region.addresses == ["10.0.0.0/8", "192.168.1.0/24"]

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            Region(
                name="US-South",
                # Missing folder
            )

        with pytest.raises(ValidationError):
            Region(
                # Missing name
                folder="Texas",
            )

    def test_default_values(self):
        """Test that default values are applied correctly."""
        region = Region(name="US-South", folder="Texas")
        assert region.latitude is None
        assert region.longitude is None
        assert region.addresses is None

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        region = Region(
            name="US-South",
            folder="Texas",
            latitude=30.2672,
            longitude=-97.7431,
            addresses=["10.0.0.0/8"],
        )
        sdk_data = region.to_sdk_model()
        assert sdk_data["name"] == "US-South"
        assert sdk_data["folder"] == "Texas"
        assert sdk_data["geo_location"] == {"latitude": 30.2672, "longitude": -97.7431}
        assert sdk_data["address"] == ["10.0.0.0/8"]

    def test_to_sdk_model_minimal(self):
        """Test conversion to SDK model with minimal fields."""
        region = Region(name="US-South", folder="Texas")
        sdk_data = region.to_sdk_model()
        assert sdk_data == {"name": "US-South", "folder": "Texas"}
        assert "geo_location" not in sdk_data
        assert "address" not in sdk_data

    def test_container_validation(self):
        """Test that exactly one container must be set."""
        with pytest.raises(ValidationError):
            Region(
                name="US-South",
                folder="Texas",
                snippet="test-snippet",
            )

    def test_latitude_range(self):
        """Test latitude validation range."""
        with pytest.raises(ValidationError):
            Region(name="test", folder="Texas", latitude=91.0)
        with pytest.raises(ValidationError):
            Region(name="test", folder="Texas", latitude=-91.0)

    def test_longitude_range(self):
        """Test longitude validation range."""
        with pytest.raises(ValidationError):
            Region(name="test", folder="Texas", longitude=181.0)
        with pytest.raises(ValidationError):
            Region(name="test", folder="Texas", longitude=-181.0)


class TestQuarantinedDevice:
    """Test cases for the QuarantinedDevice model."""

    def test_valid_quarantined_device(self):
        """Test creating a valid quarantined device."""
        device = QuarantinedDevice(
            host_id="host-123",
            serial_number="SN-456",
        )
        assert device.host_id == "host-123"
        assert device.serial_number == "SN-456"

    def test_missing_host_id(self):
        """Test that host_id is required."""
        with pytest.raises(ValidationError):
            QuarantinedDevice()

    def test_optional_serial_number(self):
        """Test that serial_number is optional."""
        device = QuarantinedDevice(host_id="host-123")
        assert device.host_id == "host-123"
        assert device.serial_number is None

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        device = QuarantinedDevice(host_id="host-123", serial_number="SN-456")
        sdk_data = device.to_sdk_model()
        assert sdk_data == {"host_id": "host-123", "serial_number": "SN-456"}

    def test_to_sdk_model_no_serial(self):
        """Test conversion to SDK model format without serial number."""
        device = QuarantinedDevice(host_id="host-123")
        sdk_data = device.to_sdk_model()
        assert sdk_data == {"host_id": "host-123"}


class TestNATRule:
    """Test cases for the NATRule model."""

    def test_valid_nat_rule(self):
        """Test creating a valid NAT rule."""
        rule = NATRule(
            name="outbound-nat",
            folder="Texas",
            nat_type="ipv4",
            source=["any"],
            destination=["any"],
            service="any",
            source_translation={
                "dynamic_ip_and_port": {
                    "type": "dynamic_ip_and_port",
                    "translated_address": ["10.0.0.1"],
                }
            },
        )
        assert rule.name == "outbound-nat"
        assert rule.folder == "Texas"
        assert rule.nat_type == "ipv4"
        assert rule.source == ["any"]
        assert rule.destination == ["any"]
        assert rule.service == "any"
        assert rule.source_translation is not None

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            NATRule(
                # Missing name
                folder="Texas",
            )

    def test_container_validation(self):
        """Test that exactly one container must be specified."""
        with pytest.raises(ValidationError):
            NATRule(
                name="test-nat",
                # Missing container
            )

        with pytest.raises(ValidationError):
            NATRule(
                name="test-nat",
                folder="Texas",
                snippet="test-snippet",
            )

    def test_default_values(self):
        """Test that default values are applied correctly."""
        rule = NATRule(name="test-nat", folder="Texas")
        assert rule.nat_type == "ipv4"
        assert rule.from_zone == ["any"]
        assert rule.to_zone == ["any"]
        assert rule.source == ["any"]
        assert rule.destination == ["any"]
        assert rule.service == "any"
        assert rule.disabled is False
        assert rule.source_translation is None
        assert rule.destination_translation is None

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        rule = NATRule(
            name="outbound-nat",
            folder="Texas",
            description="Outbound NAT rule",
            source=["192.168.1.0/24"],
            destination=["any"],
            service="any",
            source_translation={
                "dynamic_ip_and_port": {
                    "type": "dynamic_ip_and_port",
                    "translated_address": ["10.0.0.1"],
                }
            },
        )
        sdk_model = rule.to_sdk_model()
        assert sdk_model["name"] == "outbound-nat"
        assert sdk_model["folder"] == "Texas"
        assert sdk_model["description"] == "Outbound NAT rule"
        assert sdk_model["source"] == ["192.168.1.0/24"]
        assert sdk_model["destination"] == ["any"]
        assert sdk_model["service"] == "any"
        assert "source_translation" in sdk_model

    def test_to_sdk_model_minimal(self):
        """Test minimal conversion to SDK model."""
        rule = NATRule(name="simple-nat", folder="Texas")
        sdk_model = rule.to_sdk_model()
        assert sdk_model["name"] == "simple-nat"
        assert sdk_model["folder"] == "Texas"
        assert sdk_model["from_"] == ["any"]
        assert sdk_model["to_"] == ["any"]
        assert "source_translation" not in sdk_model
        assert "destination_translation" not in sdk_model

    def test_with_from_to_alias(self):
        """Test creating NAT rule with 'from' and 'to' aliases."""
        rule = NATRule(
            name="test-nat",
            folder="Texas",
            **{"from": ["trust"], "to": ["untrust"]},
        )
        assert rule.from_zone == ["trust"]
        assert rule.to_zone == ["untrust"]


class TestSecurityRule:
    """Test cases for the SecurityRule model."""

    def test_valid_security_rule(self):
        """Test creating a valid security rule."""
        rule = SecurityRule(
            name="test-rule",
            folder="test-folder",
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
        assert rule.name == "test-rule"
        assert rule.folder == "test-folder"
        assert rule.source_zones == ["trust"]
        assert rule.destination_zones == ["untrust"]
        assert rule.source_addresses == ["any"]
        assert rule.destination_addresses == ["any"]
        assert rule.applications == ["web-browsing"]
        assert rule.action == "allow"
        assert rule.description == "Test security rule"
        assert rule.tags == ["test", "example"]
        assert rule.enabled is True

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            SecurityRule(
                name="test-rule",
                # Missing folder
                source_zones=["trust"],
                destination_zones=["untrust"],
            )

        with pytest.raises(ValidationError):
            SecurityRule(
                # Missing name
                folder="test-folder",
                source_zones=["trust"],
                destination_zones=["untrust"],
            )

        with pytest.raises(ValidationError):
            SecurityRule(
                name="test-rule",
                folder="test-folder",
                # Missing source_zones
                destination_zones=["untrust"],
            )

        with pytest.raises(ValidationError):
            SecurityRule(
                name="test-rule",
                folder="test-folder",
                source_zones=["trust"],
                # Missing destination_zones
            )

    def test_default_values(self):
        """Test that default values are applied correctly."""
        rule = SecurityRule(name="test-rule", folder="test-folder", source_zones=["trust"], destination_zones=["untrust"])
        assert rule.source_addresses == ["any"]
        assert rule.destination_addresses == ["any"]
        assert rule.applications == ["any"]
        assert rule.action == "allow"
        assert rule.description == ""
        assert rule.tags == []
        assert rule.enabled is True


class TestWildfireAntivirusProfile:
    """Test cases for the WildfireAntivirusProfile model."""

    def test_valid_profile(self):
        """Test creating a valid WildFire antivirus profile."""
        profile = WildfireAntivirusProfile(
            name="wf-test",
            folder="Texas",
            description="Test profile",
            rules=[
                {
                    "name": "Forward All",
                    "direction": "both",
                    "analysis": "public-cloud",
                    "application": ["any"],
                    "file_type": ["any"],
                }
            ],
        )
        assert profile.name == "wf-test"
        assert profile.folder == "Texas"
        assert len(profile.rules) == 1

    def test_container_validation(self):
        """Test that exactly one container must be specified."""
        with pytest.raises(ValidationError):
            WildfireAntivirusProfile(
                name="wf-test",
                # No container
                rules=[{"name": "r1", "direction": "both"}],
            )

        with pytest.raises(ValidationError):
            WildfireAntivirusProfile(
                name="wf-test",
                folder="Texas",
                snippet="test-snippet",
                rules=[{"name": "r1", "direction": "both"}],
            )

    def test_rule_direction_validation(self):
        """Test rule direction validation."""
        with pytest.raises(ValidationError):
            WildfireAntivirusProfile(
                name="wf-test",
                folder="Texas",
                rules=[{"name": "bad-rule", "direction": "invalid"}],
            )

    def test_rule_analysis_validation(self):
        """Test rule analysis validation."""
        with pytest.raises(ValidationError):
            WildfireAntivirusProfile(
                name="wf-test",
                folder="Texas",
                rules=[{"name": "bad-rule", "direction": "both", "analysis": "invalid"}],
            )

    def test_rule_missing_name(self):
        """Test rule missing name validation."""
        with pytest.raises(ValidationError):
            WildfireAntivirusProfile(
                name="wf-test",
                folder="Texas",
                rules=[{"direction": "both"}],
            )

    def test_rule_missing_direction(self):
        """Test rule missing direction validation."""
        with pytest.raises(ValidationError):
            WildfireAntivirusProfile(
                name="wf-test",
                folder="Texas",
                rules=[{"name": "bad-rule"}],
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = WildfireAntivirusProfile(
            name="wf-test",
            folder="Texas",
            description="Test profile",
            packet_capture=True,
            rules=[
                {
                    "name": "Forward All",
                    "direction": "both",
                    "analysis": "public-cloud",
                }
            ],
            threat_exception=[{"name": "exc1", "notes": "test"}],
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "wf-test"
        assert sdk_data["folder"] == "Texas"
        assert sdk_data["description"] == "Test profile"
        assert sdk_data["packet_capture"] is True
        assert len(sdk_data["rules"]) == 1
        assert sdk_data["threat_exception"] == [{"name": "exc1", "notes": "test"}]

    def test_to_sdk_model_minimal(self):
        """Test conversion with minimal fields."""
        profile = WildfireAntivirusProfile(
            name="wf-minimal",
            folder="Texas",
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data == {"name": "wf-minimal", "folder": "Texas"}

    def test_valid_directions(self):
        """Test all valid direction values."""
        for direction in ["download", "upload", "both"]:
            profile = WildfireAntivirusProfile(
                name="wf-test",
                folder="Texas",
                rules=[{"name": "rule1", "direction": direction}],
            )
            assert profile.rules[0]["direction"] == direction

    def test_valid_analyses(self):
        """Test all valid analysis values."""
        for analysis in ["public-cloud", "private-cloud"]:
            profile = WildfireAntivirusProfile(
                name="wf-test",
                folder="Texas",
                rules=[{"name": "rule1", "direction": "both", "analysis": analysis}],
            )
            assert profile.rules[0]["analysis"] == analysis


class TestIPSecCryptoProfile:
    """Test cases for the IPSecCryptoProfile model."""

    def test_valid_profile(self):
        """Test creating a valid IPsec crypto profile."""
        profile = IPSecCryptoProfile(
            name="test-profile",
            folder="Texas",
            esp_encryption=["aes-256-cbc"],
            esp_authentication=["sha256"],
            dh_group="group14",
            lifetime_hours=1,
        )
        assert profile.name == "test-profile"
        assert profile.folder == "Texas"
        assert profile.esp_encryption == ["aes-256-cbc"]
        assert profile.esp_authentication == ["sha256"]
        assert profile.dh_group == "group14"
        assert profile.lifetime_hours == 1

    def test_missing_container(self):
        """Test that missing container raises error."""
        with pytest.raises(ValidationError):
            IPSecCryptoProfile(
                name="test-profile",
                esp_encryption=["aes-256-cbc"],
                esp_authentication=["sha256"],
            )

    def test_invalid_esp_encryption(self):
        """Test that invalid ESP encryption raises error."""
        with pytest.raises(ValidationError):
            IPSecCryptoProfile(
                name="test-profile",
                folder="Texas",
                esp_encryption=["invalid-algo"],
            )

    def test_invalid_esp_authentication(self):
        """Test that invalid ESP authentication raises error."""
        with pytest.raises(ValidationError):
            IPSecCryptoProfile(
                name="test-profile",
                folder="Texas",
                esp_authentication=["invalid-algo"],
            )

    def test_invalid_dh_group(self):
        """Test that invalid DH group raises error."""
        with pytest.raises(ValidationError):
            IPSecCryptoProfile(
                name="test-profile",
                folder="Texas",
                dh_group="invalid-group",
            )

    def test_default_values(self):
        """Test default values are applied correctly."""
        profile = IPSecCryptoProfile(name="test-profile", folder="Texas")
        assert profile.esp_encryption == ["aes-256-cbc"]
        assert profile.esp_authentication == ["sha256"]
        assert profile.dh_group == "group14"

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = IPSecCryptoProfile(
            name="test-profile",
            folder="Texas",
            esp_encryption=["aes-256-cbc", "aes-128-cbc"],
            esp_authentication=["sha256", "sha512"],
            dh_group="group20",
            lifetime_hours=8,
        )
        sdk_data = profile.to_sdk_model()

        assert sdk_data["name"] == "test-profile"
        assert sdk_data["folder"] == "Texas"
        assert sdk_data["esp"]["encryption"] == ["aes-256-cbc", "aes-128-cbc"]
        assert sdk_data["esp"]["authentication"] == ["sha256", "sha512"]
        assert sdk_data["dh_group"] == "group20"
        assert sdk_data["lifetime"] == {"hours": 8}

    def test_to_sdk_model_default_lifetime(self):
        """Test that default lifetime is applied in SDK model."""
        profile = IPSecCryptoProfile(name="test-profile", folder="Texas")
        sdk_data = profile.to_sdk_model()
        assert sdk_data["lifetime"] == {"hours": 1}

    def test_to_sdk_model_with_lifesize(self):
        """Test SDK model with lifesize."""
        profile = IPSecCryptoProfile(
            name="test-profile",
            folder="Texas",
            lifetime_seconds=3600,
            lifesize_mb=100,
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["lifetime"] == {"seconds": 3600}
        assert sdk_data["lifesize"] == {"mb": 100}

    def test_multiple_containers_error(self):
        """Test that multiple containers raises error."""
        with pytest.raises(ValidationError):
            IPSecCryptoProfile(
                name="test-profile",
                folder="Texas",
                snippet="my-snippet",
            )


class TestDNSSecurityProfile:
    """Test cases for the DNSSecurityProfile model."""

    def test_valid_dns_security_profile(self):
        """Test creating a valid DNS security profile."""
        profile = DNSSecurityProfile(
            name="dns-sec-default",
            folder="Texas",
            description="Default DNS security profile",
            botnet_domains={
                "dns_security_categories": [
                    {"name": "pan-dns-sec-malware", "action": "sinkhole", "log_level": "default"},
                ],
                "sinkhole": {"ipv4_address": "pan-sinkhole-default-ip", "ipv6_address": "::1"},
            },
        )
        assert profile.name == "dns-sec-default"
        assert profile.folder == "Texas"
        assert profile.description == "Default DNS security profile"
        assert profile.botnet_domains is not None
        assert len(profile.botnet_domains["dns_security_categories"]) == 1

    def test_missing_name(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            DNSSecurityProfile(folder="Texas")

    def test_no_container(self):
        """Test that at least one container is required."""
        with pytest.raises(ValidationError):
            DNSSecurityProfile(name="test-profile")

    def test_multiple_containers(self):
        """Test that only one container is allowed."""
        with pytest.raises(ValidationError):
            DNSSecurityProfile(name="test-profile", folder="Texas", snippet="MySnippet")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = DNSSecurityProfile(
            name="dns-sec-test",
            folder="Texas",
            description="Test profile",
            botnet_domains={
                "dns_security_categories": [
                    {"name": "pan-dns-sec-malware", "action": "sinkhole"},
                ],
            },
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "dns-sec-test"
        assert sdk_data["folder"] == "Texas"
        assert sdk_data["description"] == "Test profile"
        assert "botnet_domains" in sdk_data
        assert len(sdk_data["botnet_domains"]["dns_security_categories"]) == 1

    def test_to_sdk_model_minimal(self):
        """Test conversion with minimal fields."""
        profile = DNSSecurityProfile(name="dns-sec-minimal", folder="Texas")
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "dns-sec-minimal"
        assert sdk_data["folder"] == "Texas"
        assert "description" not in sdk_data
        assert "botnet_domains" not in sdk_data

    def test_snippet_container(self):
        """Test using snippet as container."""
        profile = DNSSecurityProfile(name="dns-sec-snippet", snippet="MySnippet")
        sdk_data = profile.to_sdk_model()
        assert sdk_data["snippet"] == "MySnippet"
        assert "folder" not in sdk_data

    def test_device_container(self):
        """Test using device as container."""
        profile = DNSSecurityProfile(name="dns-sec-device", device="fw-01")
        sdk_data = profile.to_sdk_model()
        assert sdk_data["device"] == "fw-01"
        assert "folder" not in sdk_data


class TestVulnerabilityProtectionProfile:
    """Test cases for the VulnerabilityProtectionProfile model."""

    def test_valid_profile(self):
        """Test creating a valid vulnerability protection profile."""
        profile = VulnerabilityProtectionProfile(
            name="test-vuln-profile",
            folder="Texas",
            description="Test vulnerability protection",
            rules=[
                {
                    "name": "Block Critical",
                    "severity": ["critical", "high"],
                    "category": "any",
                    "host": "any",
                    "action": {"alert": {}},
                }
            ],
        )
        assert profile.name == "test-vuln-profile"
        assert profile.folder == "Texas"
        assert profile.description == "Test vulnerability protection"
        assert len(profile.rules) == 1

    def test_missing_container(self):
        """Test that missing container raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                rules=[{"name": "r1", "severity": ["critical"], "host": "any"}],
            )

    def test_multiple_containers(self):
        """Test that multiple containers raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                folder="Texas",
                snippet="test-snippet",
                rules=[{"name": "r1", "severity": ["critical"], "host": "any"}],
            )

    def test_rule_missing_name(self):
        """Test that rule without name raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                folder="Texas",
                rules=[{"severity": ["critical"], "host": "any"}],
            )

    def test_rule_missing_severity(self):
        """Test that rule without severity raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                folder="Texas",
                rules=[{"name": "r1", "host": "any"}],
            )

    def test_rule_missing_host(self):
        """Test that rule without host raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                folder="Texas",
                rules=[{"name": "r1", "severity": ["critical"]}],
            )

    def test_rule_invalid_severity(self):
        """Test that invalid severity raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                folder="Texas",
                rules=[{"name": "r1", "severity": ["invalid"], "host": "any"}],
            )

    def test_rule_invalid_host(self):
        """Test that invalid host raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                folder="Texas",
                rules=[{"name": "r1", "severity": ["critical"], "host": "invalid"}],
            )

    def test_rule_invalid_category(self):
        """Test that invalid category raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                folder="Texas",
                rules=[{"name": "r1", "severity": ["critical"], "host": "any", "category": "invalid"}],
            )

    def test_rule_invalid_action(self):
        """Test that invalid action raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                folder="Texas",
                rules=[{"name": "r1", "severity": ["critical"], "host": "any", "action": "invalid"}],
            )

    def test_rule_invalid_packet_capture(self):
        """Test that invalid packet_capture raises validation error."""
        with pytest.raises(ValidationError):
            VulnerabilityProtectionProfile(
                name="test-vuln-profile",
                folder="Texas",
                rules=[{"name": "r1", "severity": ["critical"], "host": "any", "packet_capture": "invalid"}],
            )

    def test_to_sdk_model(self):
        """Test converting profile to SDK model format."""
        profile = VulnerabilityProtectionProfile(
            name="test-vuln-profile",
            folder="Texas",
            description="Test profile",
            rules=[
                {
                    "name": "Block Critical",
                    "severity": ["critical"],
                    "host": "any",
                    "action": {"default": {}},
                }
            ],
            threat_exceptions=[{"name": "exception-1", "notes": "Test exception"}],
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "test-vuln-profile"
        assert sdk_data["folder"] == "Texas"
        assert sdk_data["description"] == "Test profile"
        assert len(sdk_data["rules"]) == 1
        assert sdk_data["threat_exception"][0]["name"] == "exception-1"

    def test_to_sdk_model_minimal(self):
        """Test converting minimal profile to SDK model."""
        profile = VulnerabilityProtectionProfile(
            name="minimal",
            folder="Texas",
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "minimal"
        assert sdk_data["folder"] == "Texas"
        assert "description" not in sdk_data
        assert "rules" not in sdk_data
        assert "threat_exception" not in sdk_data

    def test_valid_all_severities(self):
        """Test profile with all valid severity values."""
        profile = VulnerabilityProtectionProfile(
            name="all-sev",
            folder="Texas",
            rules=[
                {
                    "name": "all-severities",
                    "severity": ["critical", "high", "medium", "low", "informational"],
                    "host": "client",
                    "category": "sql-injection",
                    "action": "drop",
                    "packet_capture": "extended-capture",
                }
            ],
        )
        assert len(profile.rules[0]["severity"]) == 5

    def test_dict_action_allowed(self):
        """Test that dict-style action (block_ip) is allowed."""
        profile = VulnerabilityProtectionProfile(
            name="block-ip-test",
            folder="Texas",
            rules=[
                {
                    "name": "block-rule",
                    "severity": ["critical"],
                    "host": "any",
                    "action": {"block_ip": {"track_by": "source", "duration": 300}},
                }
            ],
        )
        assert profile.rules[0]["action"]["block_ip"]["duration"] == 300


class TestURLCategory:
    """Test cases for the URLCategory model."""

    def test_valid_url_category(self):
        """Test creating a valid URL category."""
        category = URLCategory(
            name="custom-block",
            folder="Texas",
            description="Custom blocked URLs",
            type="URL List",
            url_list=["malware.example.com", "phishing.test.org"],
        )
        assert category.name == "custom-block"
        assert category.folder == "Texas"
        assert category.description == "Custom blocked URLs"
        assert category.type == "URL List"
        assert category.url_list == ["malware.example.com", "phishing.test.org"]

    def test_missing_name(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            URLCategory(folder="Texas")

    def test_no_container(self):
        """Test that exactly one container must be set."""
        with pytest.raises(ValidationError):
            URLCategory(name="test")

    def test_multiple_containers(self):
        """Test that multiple containers are rejected."""
        with pytest.raises(ValidationError):
            URLCategory(name="test", folder="Texas", snippet="My-Snippet")

    def test_invalid_type(self):
        """Test that invalid type is rejected."""
        with pytest.raises(ValidationError):
            URLCategory(name="test", folder="Texas", type="Invalid Type")

    def test_valid_category_match_type(self):
        """Test Category Match type is accepted."""
        category = URLCategory(name="test", folder="Texas", type="Category Match", url_list=["gambling"])
        assert category.type == "Category Match"

    def test_default_values(self):
        """Test default values."""
        category = URLCategory(name="test", folder="Texas")
        assert category.type == "URL List"
        assert category.url_list == []
        assert category.description is None

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        category = URLCategory(
            name="custom-block",
            folder="Texas",
            description="Custom blocked URLs",
            type="URL List",
            url_list=["malware.example.com"],
        )
        sdk_data = category.to_sdk_model()
        assert sdk_data["name"] == "custom-block"
        assert sdk_data["folder"] == "Texas"
        assert sdk_data["description"] == "Custom blocked URLs"
        assert sdk_data["type"] == "URL List"
        assert sdk_data["list"] == ["malware.example.com"]

    def test_to_sdk_model_snippet(self):
        """Test conversion with snippet container."""
        category = URLCategory(name="test", snippet="My-Snippet")
        sdk_data = category.to_sdk_model()
        assert sdk_data["snippet"] == "My-Snippet"
        assert "folder" not in sdk_data

    def test_to_sdk_model_minimal(self):
        """Test conversion with minimal fields."""
        category = URLCategory(name="test", folder="Texas")
        sdk_data = category.to_sdk_model()
        assert sdk_data == {"name": "test", "folder": "Texas", "type": "URL List"}


# ========================================================================================================================================================================================
# BGP ROUTING VALIDATOR TESTS
# ========================================================================================================================================================================================


class TestBGPRouting:
    """Test BGP routing validator."""

    def test_valid_bgp_routing(self):
        """Test valid BGP routing creation."""
        bgp = BGPRouting(backbone_routing="no-asymmetric-routing")
        assert bgp.backbone_routing == "no-asymmetric-routing"
        assert bgp.accept_route_over_sc is False
        assert bgp.outbound_routes_for_services == []

    def test_valid_bgp_routing_all_fields(self):
        """Test valid BGP routing with all fields."""
        bgp = BGPRouting(
            backbone_routing="asymmetric-routing-only",
            routing_preference="hot_potato_routing",
            accept_route_over_sc=True,
            outbound_routes_for_services=["10.0.0.0/8"],
            add_host_route_to_ike_peer=True,
            withdraw_static_route=True,
        )
        assert bgp.backbone_routing == "asymmetric-routing-only"
        assert bgp.routing_preference == "hot_potato_routing"
        assert bgp.accept_route_over_sc is True

    def test_invalid_backbone_routing(self):
        """Test that invalid backbone_routing raises error."""
        with pytest.raises(ValidationError):
            BGPRouting(backbone_routing="invalid-value")

    def test_invalid_routing_preference(self):
        """Test that invalid routing_preference raises error."""
        with pytest.raises(ValidationError):
            BGPRouting(backbone_routing="no-asymmetric-routing", routing_preference="invalid")

    def test_to_sdk_model(self):
        """Test SDK model conversion."""
        bgp = BGPRouting(
            backbone_routing="no-asymmetric-routing",
            routing_preference="default",
        )
        sdk_data = bgp.to_sdk_model()
        assert sdk_data["backbone_routing"] == "no-asymmetric-routing"
        assert sdk_data["routing_preference"] == {"default": {}}
        assert sdk_data["accept_route_over_SC"] is False

    def test_to_sdk_model_hot_potato(self):
        """Test SDK model conversion with hot potato routing."""
        bgp = BGPRouting(
            backbone_routing="asymmetric-routing-with-load-share",
            routing_preference="hot_potato_routing",
        )
        sdk_data = bgp.to_sdk_model()
        assert sdk_data["routing_preference"] == {"hot_potato_routing": {}}

    def test_to_sdk_model_no_routing_preference(self):
        """Test SDK model conversion without routing preference."""
        bgp = BGPRouting(backbone_routing="no-asymmetric-routing")
        sdk_data = bgp.to_sdk_model()
        assert "routing_preference" not in sdk_data


# ========================================================================================================================================================================================
# INTERNAL DNS SERVER VALIDATOR TESTS
# ========================================================================================================================================================================================


class TestInternalDNSServer:
    """Test internal DNS server validator."""

    def test_valid_dns_server(self):
        """Test valid internal DNS server creation."""
        server = InternalDNSServer(
            name="corp-dns",
            domain_name=["corp.example.com"],
            primary="10.0.0.1",
        )
        assert server.name == "corp-dns"
        assert server.domain_name == ["corp.example.com"]
        assert server.primary == "10.0.0.1"
        assert server.secondary is None

    def test_valid_dns_server_all_fields(self):
        """Test valid internal DNS server with all fields."""
        server = InternalDNSServer(
            name="corp-dns",
            domain_name=["corp.example.com", "dev.example.com"],
            primary="10.0.0.1",
            secondary="10.0.0.2",
        )
        assert len(server.domain_name) == 2
        assert server.secondary == "10.0.0.2"

    def test_domain_name_string_conversion(self):
        """Test that string domain_name is converted to list."""
        server = InternalDNSServer(
            name="corp-dns",
            domain_name="corp.example.com",
            primary="10.0.0.1",
        )
        assert server.domain_name == ["corp.example.com"]

    def test_empty_domain_name_raises_error(self):
        """Test that empty domain_name raises error."""
        with pytest.raises(ValidationError):
            InternalDNSServer(
                name="corp-dns",
                domain_name=[],
                primary="10.0.0.1",
            )

    def test_invalid_name_raises_error(self):
        """Test that invalid name raises error."""
        with pytest.raises(ValidationError):
            InternalDNSServer(
                name="invalid@name!",
                domain_name=["corp.example.com"],
                primary="10.0.0.1",
            )

    def test_to_sdk_model(self):
        """Test SDK model conversion."""
        server = InternalDNSServer(
            name="corp-dns",
            domain_name=["corp.example.com"],
            primary="10.0.0.1",
            secondary="10.0.0.2",
        )
        sdk_data = server.to_sdk_model()
        assert sdk_data["name"] == "corp-dns"
        assert sdk_data["domain_name"] == ["corp.example.com"]
        assert sdk_data["primary"] == "10.0.0.1"
        assert sdk_data["secondary"] == "10.0.0.2"

    def test_to_sdk_model_no_secondary(self):
        """Test SDK model conversion without secondary."""
        server = InternalDNSServer(
            name="corp-dns",
            domain_name=["corp.example.com"],
            primary="10.0.0.1",
        )
        sdk_data = server.to_sdk_model()
        assert "secondary" not in sdk_data


# ========================================================================================================================================================================================
# MOBILE AGENT VALIDATOR TESTS
# ========================================================================================================================================================================================


class TestAuthSetting:
    """Test cases for the AuthSetting model."""

    def test_valid_auth_setting(self):
        """Test creating a valid auth setting."""
        from scm_cli.utils.validators import AuthSetting

        setting = AuthSetting(
            name="saml-auth",
            folder="Mobile Users",
            description="SAML authentication",
            auth_type="saml",
            os="Any",
            max_user=100,
            saml_idp="okta-idp",
        )
        assert setting.name == "saml-auth"
        assert setting.folder == "Mobile Users"
        assert setting.auth_type == "saml"
        assert setting.os == "Any"
        assert setting.max_user == 100
        assert setting.saml_idp == "okta-idp"

    def test_missing_name(self):
        """Test that name is required."""
        from scm_cli.utils.validators import AuthSetting

        with pytest.raises(ValidationError):
            AuthSetting(folder="Mobile Users")

    def test_no_container(self):
        """Test that at least one container must be set."""
        from scm_cli.utils.validators import AuthSetting

        with pytest.raises(ValidationError):
            AuthSetting(name="test-auth")

    def test_folder_container(self):
        """Test auth setting with folder container."""
        from scm_cli.utils.validators import AuthSetting

        setting = AuthSetting(name="test", folder="Mobile Users")
        assert setting.folder == "Mobile Users"

    def test_snippet_container(self):
        """Test auth setting with snippet container."""
        from scm_cli.utils.validators import AuthSetting

        setting = AuthSetting(name="test", snippet="Shared")
        assert setting.snippet == "Shared"

    def test_device_container(self):
        """Test auth setting with device container."""
        from scm_cli.utils.validators import AuthSetting

        setting = AuthSetting(name="test", device="fw-01")
        assert setting.device == "fw-01"

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        from scm_cli.utils.validators import AuthSetting

        setting = AuthSetting(
            name="saml-auth",
            folder="Mobile Users",
            description="SAML auth",
            auth_type="saml",
            os="Any",
            max_user=50,
            saml_idp="okta-idp",
        )
        sdk_data = setting.to_sdk_model()
        assert sdk_data["name"] == "saml-auth"
        assert sdk_data["folder"] == "Mobile Users"
        assert sdk_data["description"] == "SAML auth"
        assert sdk_data["auth_type"] == "saml"
        assert sdk_data["os"] == "Any"
        assert sdk_data["max_user"] == 50
        assert sdk_data["saml_idp"] == "okta-idp"

    def test_to_sdk_model_minimal(self):
        """Test conversion with minimal fields."""
        from scm_cli.utils.validators import AuthSetting

        setting = AuthSetting(name="test", folder="Mobile Users")
        sdk_data = setting.to_sdk_model()
        assert sdk_data == {"name": "test", "folder": "Mobile Users"}

    def test_to_sdk_model_snippet(self):
        """Test conversion with snippet container."""
        from scm_cli.utils.validators import AuthSetting

        setting = AuthSetting(name="test", snippet="Shared")
        sdk_data = setting.to_sdk_model()
        assert sdk_data["snippet"] == "Shared"
        assert "folder" not in sdk_data

    def test_to_sdk_model_certificate_auth(self):
        """Test conversion with certificate authentication."""
        from scm_cli.utils.validators import AuthSetting

        setting = AuthSetting(
            name="cert-auth",
            folder="Mobile Users",
            auth_type="client-certificate",
            os="Windows",
            certificate_profile="corp-cert",
        )
        sdk_data = setting.to_sdk_model()
        assert sdk_data["auth_type"] == "client-certificate"
        assert sdk_data["certificate_profile"] == "corp-cert"

    def test_to_sdk_model_ldap_auth(self):
        """Test conversion with LDAP authentication."""
        from scm_cli.utils.validators import AuthSetting

        setting = AuthSetting(
            name="ldap-auth",
            folder="Mobile Users",
            auth_type="ldap",
            ldap_profile="corp-ldap",
        )
        sdk_data = setting.to_sdk_model()
        assert sdk_data["auth_type"] == "ldap"
        assert sdk_data["ldap_profile"] == "corp-ldap"


class TestAggregateInterface:
    """Test cases for the AggregateInterface model."""

    def test_valid_layer3(self):
        """Test creating a valid layer3 aggregate interface."""
        iface = AggregateInterface(
            name="ae1",
            folder="test-folder",
            layer3={"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]},
        )
        assert iface.name == "ae1"
        assert iface.folder == "test-folder"
        assert iface.layer3 == {"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]}
        assert iface.layer2 is None

    def test_valid_layer2(self):
        """Test creating a valid layer2 aggregate interface."""
        iface = AggregateInterface(
            name="ae2",
            folder="test-folder",
            layer2={"vlan_tag": "100"},
        )
        assert iface.name == "ae2"
        assert iface.layer2 == {"vlan_tag": "100"}
        assert iface.layer3 is None

    def test_missing_name_raises(self):
        """Test that missing name raises error."""
        with pytest.raises(ValidationError):
            AggregateInterface(folder="test-folder")

    def test_no_container_raises(self):
        """Test that missing container raises error."""
        with pytest.raises(ValidationError):
            AggregateInterface(name="ae1")

    def test_multiple_containers_raises(self):
        """Test that multiple containers raises error."""
        with pytest.raises(ValidationError):
            AggregateInterface(name="ae1", folder="f", snippet="s")

    def test_both_modes_raises(self):
        """Test that specifying both layer2 and layer3 raises error."""
        with pytest.raises(ValidationError):
            AggregateInterface(
                name="ae1",
                folder="test-folder",
                layer2={"vlan_tag": "100"},
                layer3={"mtu": 1500},
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        iface = AggregateInterface(
            name="ae1",
            folder="test-folder",
            comment="test interface",
            layer3={"mtu": 9000, "ip": [{"name": "10.0.0.1/24"}]},
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["name"] == "ae1"
        assert sdk_data["folder"] == "test-folder"
        assert sdk_data["comment"] == "test interface"
        assert sdk_data["layer3"]["mtu"] == 9000

    def test_minimal_creation(self):
        """Test minimal aggregate interface creation."""
        iface = AggregateInterface(
            name="ae1",
            folder="test-folder",
        )
        assert iface.name == "ae1"
        assert iface.folder == "test-folder"
        assert iface.layer2 is None
        assert iface.layer3 is None
        assert iface.comment is None


class TestDhcpInterface:
    """Test cases for the DhcpInterface model."""

    def test_valid_server(self):
        """Test creating a valid DHCP server interface."""
        iface = DhcpInterface(
            name="ethernet1/1",
            folder="test-folder",
            server={"mode": "auto", "ip_pool": ["10.0.0.10-10.0.0.100"]},
        )
        assert iface.name == "ethernet1/1"
        assert iface.server is not None
        assert iface.relay is None

    def test_valid_relay(self):
        """Test creating a valid DHCP relay interface."""
        iface = DhcpInterface(
            name="ethernet1/2",
            folder="test-folder",
            relay={"ip": {"enabled": True, "server": ["10.0.0.1"]}},
        )
        assert iface.relay is not None
        assert iface.server is None

    def test_missing_name_raises(self):
        """Test that missing name raises error."""
        with pytest.raises(ValidationError):
            DhcpInterface(folder="test-folder")

    def test_no_container_raises(self):
        """Test that missing container raises error."""
        with pytest.raises(ValidationError):
            DhcpInterface(name="ethernet1/1")

    def test_multiple_containers_raises(self):
        """Test that multiple containers raises error."""
        with pytest.raises(ValidationError):
            DhcpInterface(name="ethernet1/1", folder="f", snippet="s")

    def test_both_server_relay_raises(self):
        """Test that specifying both server and relay raises error."""
        with pytest.raises(ValidationError):
            DhcpInterface(
                name="ethernet1/1",
                folder="test-folder",
                server={"mode": "auto"},
                relay={"ip": {"enabled": True, "server": ["10.0.0.1"]}},
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        iface = DhcpInterface(
            name="ethernet1/1",
            folder="test-folder",
            server={"mode": "auto", "ip_pool": ["10.0.0.10-10.0.0.100"]},
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["name"] == "ethernet1/1"
        assert sdk_data["folder"] == "test-folder"
        assert sdk_data["server"]["mode"] == "auto"

    def test_minimal_creation(self):
        """Test minimal DHCP interface creation."""
        iface = DhcpInterface(name="ethernet1/1", folder="test-folder")
        assert iface.name == "ethernet1/1"
        assert iface.server is None
        assert iface.relay is None


class TestEthernetInterface:
    """Test cases for the EthernetInterface model."""

    def test_valid_layer3(self):
        """Test creating a valid layer3 ethernet interface."""
        iface = EthernetInterface(
            name="$eth1",
            folder="test-folder",
            layer3={"mtu": 1500, "ip": [{"name": "10.0.0.1/24"}]},
        )
        assert iface.name == "$eth1"
        assert iface.layer3 is not None
        assert iface.layer2 is None

    def test_valid_layer2(self):
        """Test creating a valid layer2 ethernet interface."""
        iface = EthernetInterface(
            name="$eth2",
            folder="test-folder",
            layer2={"vlan_tag": "100"},
        )
        assert iface.layer2 is not None
        assert iface.layer3 is None

    def test_missing_name_raises(self):
        """Test that missing name raises error."""
        with pytest.raises(ValidationError):
            EthernetInterface(folder="test-folder")

    def test_no_container_raises(self):
        """Test that missing container raises error."""
        with pytest.raises(ValidationError):
            EthernetInterface(name="$eth1")

    def test_multiple_containers_raises(self):
        """Test that multiple containers raises error."""
        with pytest.raises(ValidationError):
            EthernetInterface(name="$eth1", folder="f", snippet="s")

    def test_multiple_modes_raises(self):
        """Test that specifying multiple modes raises error."""
        with pytest.raises(ValidationError):
            EthernetInterface(
                name="$eth1",
                folder="test-folder",
                layer2={"vlan_tag": "100"},
                layer3={"mtu": 1500},
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        iface = EthernetInterface(
            name="$eth1",
            folder="test-folder",
            comment="test eth",
            layer3={"mtu": 9000},
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["name"] == "$eth1"
        assert sdk_data["folder"] == "test-folder"
        assert sdk_data["comment"] == "test eth"
        assert sdk_data["layer3"]["mtu"] == 9000

    def test_minimal_creation(self):
        """Test minimal ethernet interface creation."""
        iface = EthernetInterface(name="$eth1", folder="test-folder")
        assert iface.name == "$eth1"
        assert iface.layer2 is None
        assert iface.layer3 is None
        assert iface.tap is None


class TestLayer2Subinterface:
    """Test cases for the Layer2Subinterface model."""

    def test_valid_creation(self):
        """Test creating a valid layer2 subinterface."""
        iface = Layer2Subinterface(
            name="ethernet1/1.100",
            folder="test-folder",
            vlan_tag="100",
        )
        assert iface.name == "ethernet1/1.100"
        assert iface.vlan_tag == "100"

    def test_with_parent(self):
        """Test layer2 subinterface with parent interface."""
        iface = Layer2Subinterface(
            name="ethernet1/1.100",
            folder="test-folder",
            vlan_tag="100",
            parent_interface="ethernet1/1",
        )
        assert iface.parent_interface == "ethernet1/1"

    def test_missing_vlan_tag_raises(self):
        """Test that missing vlan_tag raises error."""
        with pytest.raises(ValidationError):
            Layer2Subinterface(name="ethernet1/1.100", folder="test-folder")

    def test_missing_name_raises(self):
        """Test that missing name raises error."""
        with pytest.raises(ValidationError):
            Layer2Subinterface(folder="test-folder", vlan_tag="100")

    def test_no_container_raises(self):
        """Test that missing container raises error."""
        with pytest.raises(ValidationError):
            Layer2Subinterface(name="ethernet1/1.100", vlan_tag="100")

    def test_multiple_containers_raises(self):
        """Test that multiple containers raises error."""
        with pytest.raises(ValidationError):
            Layer2Subinterface(name="ethernet1/1.100", vlan_tag="100", folder="f", snippet="s")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        iface = Layer2Subinterface(
            name="ethernet1/1.100",
            folder="test-folder",
            vlan_tag="100",
            parent_interface="ethernet1/1",
            comment="test sub",
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["name"] == "ethernet1/1.100"
        assert sdk_data["vlan_tag"] == "100"
        assert sdk_data["parent_interface"] == "ethernet1/1"
        assert sdk_data["comment"] == "test sub"

    def test_minimal_creation(self):
        """Test minimal layer2 subinterface creation."""
        iface = Layer2Subinterface(name="ethernet1/1.100", folder="test-folder", vlan_tag="100")
        assert iface.parent_interface is None
        assert iface.comment is None


class TestLayer3Subinterface:
    """Test cases for the Layer3Subinterface model."""

    def test_valid_static_ip(self):
        """Test creating a layer3 subinterface with static IP."""
        iface = Layer3Subinterface(
            name="ethernet1/1.100",
            folder="test-folder",
            tag=100,
            ip=[{"name": "10.0.1.1/24"}],
        )
        assert iface.tag == 100
        assert iface.ip == [{"name": "10.0.1.1/24"}]

    def test_valid_dhcp(self):
        """Test creating a layer3 subinterface with DHCP."""
        iface = Layer3Subinterface(
            name="ethernet1/1.200",
            folder="test-folder",
            dhcp_client={"enable": True},
        )
        assert iface.dhcp_client is not None
        assert iface.ip is None

    def test_missing_name_raises(self):
        """Test that missing name raises error."""
        with pytest.raises(ValidationError):
            Layer3Subinterface(folder="test-folder")

    def test_no_container_raises(self):
        """Test that missing container raises error."""
        with pytest.raises(ValidationError):
            Layer3Subinterface(name="ethernet1/1.100")

    def test_multiple_containers_raises(self):
        """Test that multiple containers raises error."""
        with pytest.raises(ValidationError):
            Layer3Subinterface(name="ethernet1/1.100", folder="f", snippet="s")

    def test_both_ip_modes_raises(self):
        """Test that specifying both IP and DHCP raises error."""
        with pytest.raises(ValidationError):
            Layer3Subinterface(
                name="ethernet1/1.100",
                folder="test-folder",
                ip=[{"name": "10.0.1.1/24"}],
                dhcp_client={"enable": True},
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        iface = Layer3Subinterface(
            name="ethernet1/1.100",
            folder="test-folder",
            tag=100,
            mtu=9000,
            ip=[{"name": "10.0.1.1/24"}],
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["name"] == "ethernet1/1.100"
        assert sdk_data["tag"] == 100
        assert sdk_data["mtu"] == 9000

    def test_minimal_creation(self):
        """Test minimal layer3 subinterface creation."""
        iface = Layer3Subinterface(name="ethernet1/1.100", folder="test-folder")
        assert iface.tag is None
        assert iface.ip is None
        assert iface.dhcp_client is None


class TestLoopbackInterface:
    """Test cases for the LoopbackInterface model."""

    def test_valid_creation(self):
        """Test creating a valid loopback interface."""
        iface = LoopbackInterface(
            name="$lo1",
            folder="test-folder",
            ip=[{"name": "10.0.0.1/32"}],
        )
        assert iface.name == "$lo1"
        assert iface.ip == [{"name": "10.0.0.1/32"}]

    def test_with_mtu(self):
        """Test loopback interface with MTU."""
        iface = LoopbackInterface(
            name="$lo1",
            folder="test-folder",
            mtu=9000,
        )
        assert iface.mtu == 9000

    def test_missing_name_raises(self):
        """Test that missing name raises error."""
        with pytest.raises(ValidationError):
            LoopbackInterface(folder="test-folder")

    def test_no_container_raises(self):
        """Test that missing container raises error."""
        with pytest.raises(ValidationError):
            LoopbackInterface(name="$lo1")

    def test_multiple_containers_raises(self):
        """Test that multiple containers raises error."""
        with pytest.raises(ValidationError):
            LoopbackInterface(name="$lo1", folder="f", snippet="s")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        iface = LoopbackInterface(
            name="$lo1",
            folder="test-folder",
            comment="test lo",
            ip=[{"name": "10.0.0.1/32"}],
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["name"] == "$lo1"
        assert sdk_data["folder"] == "test-folder"
        assert sdk_data["comment"] == "test lo"

    def test_to_sdk_model_with_ipv6(self):
        """Test conversion with IPv6 config."""
        iface = LoopbackInterface(
            name="$lo1",
            folder="test-folder",
            ipv6={"enabled": True},
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["ipv6"] == {"enabled": True}

    def test_minimal_creation(self):
        """Test minimal loopback interface creation."""
        iface = LoopbackInterface(name="$lo1", folder="test-folder")
        assert iface.ip is None
        assert iface.mtu is None
        assert iface.comment is None


class TestTunnelInterface:
    """Test cases for the TunnelInterface model."""

    def test_valid_creation(self):
        """Test creating a valid tunnel interface."""
        iface = TunnelInterface(
            name="tunnel1",
            folder="test-folder",
            ip=[{"name": "10.0.0.1/30"}],
        )
        assert iface.name == "tunnel1"
        assert iface.ip == [{"name": "10.0.0.1/30"}]

    def test_with_mtu(self):
        """Test tunnel interface with MTU."""
        iface = TunnelInterface(
            name="tunnel1",
            folder="test-folder",
            mtu=1400,
        )
        assert iface.mtu == 1400

    def test_missing_name_raises(self):
        """Test that missing name raises error."""
        with pytest.raises(ValidationError):
            TunnelInterface(folder="test-folder")

    def test_no_container_raises(self):
        """Test that missing container raises error."""
        with pytest.raises(ValidationError):
            TunnelInterface(name="tunnel1")

    def test_multiple_containers_raises(self):
        """Test that multiple containers raises error."""
        with pytest.raises(ValidationError):
            TunnelInterface(name="tunnel1", folder="f", snippet="s")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        iface = TunnelInterface(
            name="tunnel1",
            folder="test-folder",
            comment="test tunnel",
            mtu=1400,
            ip=[{"name": "10.0.0.1/30"}],
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["name"] == "tunnel1"
        assert sdk_data["folder"] == "test-folder"
        assert sdk_data["mtu"] == 1400

    def test_to_sdk_model_default_value(self):
        """Test conversion with default_value."""
        iface = TunnelInterface(
            name="tunnel1",
            folder="test-folder",
            default_value="tunnel.1",
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["default_value"] == "tunnel.1"

    def test_minimal_creation(self):
        """Test minimal tunnel interface creation."""
        iface = TunnelInterface(name="tunnel1", folder="test-folder")
        assert iface.ip is None
        assert iface.mtu is None
        assert iface.comment is None


class TestVlanInterface:
    """Test cases for the VlanInterface model."""

    def test_valid_static_ip(self):
        """Test creating a VLAN interface with static IP."""
        iface = VlanInterface(
            name="vlan1",
            folder="test-folder",
            vlan_tag="100",
            ip=[{"name": "10.0.10.1/24"}],
        )
        assert iface.vlan_tag == "100"
        assert iface.ip == [{"name": "10.0.10.1/24"}]

    def test_valid_dhcp(self):
        """Test creating a VLAN interface with DHCP."""
        iface = VlanInterface(
            name="vlan2",
            folder="test-folder",
            dhcp_client={"enable": True},
        )
        assert iface.dhcp_client is not None
        assert iface.ip is None

    def test_missing_name_raises(self):
        """Test that missing name raises error."""
        with pytest.raises(ValidationError):
            VlanInterface(folder="test-folder")

    def test_no_container_raises(self):
        """Test that missing container raises error."""
        with pytest.raises(ValidationError):
            VlanInterface(name="vlan1")

    def test_multiple_containers_raises(self):
        """Test that multiple containers raises error."""
        with pytest.raises(ValidationError):
            VlanInterface(name="vlan1", folder="f", snippet="s")

    def test_both_ip_modes_raises(self):
        """Test that specifying both IP and DHCP raises error."""
        with pytest.raises(ValidationError):
            VlanInterface(
                name="vlan1",
                folder="test-folder",
                ip=[{"name": "10.0.10.1/24"}],
                dhcp_client={"enable": True},
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        iface = VlanInterface(
            name="vlan1",
            folder="test-folder",
            vlan_tag="100",
            comment="test vlan",
            ip=[{"name": "10.0.10.1/24"}],
        )
        sdk_data = iface.to_sdk_model()
        assert sdk_data["name"] == "vlan1"
        assert sdk_data["vlan_tag"] == "100"
        assert sdk_data["comment"] == "test vlan"

    def test_minimal_creation(self):
        """Test minimal VLAN interface creation."""
        iface = VlanInterface(name="vlan1", folder="test-folder")
        assert iface.vlan_tag is None
        assert iface.ip is None
        assert iface.dhcp_client is None


class TestBgpAddressFamilyProfile:
    """Test cases for the BgpAddressFamilyProfile model."""

    def test_valid_profile(self):
        """Test creating a valid BGP address family profile."""
        profile = BgpAddressFamilyProfile(name="test-af", folder="test-folder", ipv4={"unicast": {"enable": True}})
        assert profile.name == "test-af"
        assert profile.folder == "test-folder"
        assert profile.ipv4 == {"unicast": {"enable": True}}

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            BgpAddressFamilyProfile(name="test-af")

    def test_multiple_containers_rejected(self):
        """Test that multiple containers are rejected."""
        with pytest.raises(ValidationError):
            BgpAddressFamilyProfile(name="test-af", folder="f", snippet="s")

    def test_minimal_creation(self):
        """Test minimal creation without optional fields."""
        profile = BgpAddressFamilyProfile(name="test-af", folder="test-folder")
        assert profile.ipv4 is None

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = BgpAddressFamilyProfile(name="test-af", folder="test-folder", ipv4={"unicast": {"enable": True}})
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "test-af"
        assert sdk_data["folder"] == "test-folder"
        assert sdk_data["ipv4"] == {"unicast": {"enable": True}}

    def test_to_sdk_model_snippet(self):
        """Test SDK model with snippet container."""
        profile = BgpAddressFamilyProfile(name="test-af", snippet="test-snippet")
        sdk_data = profile.to_sdk_model()
        assert sdk_data["snippet"] == "test-snippet"
        assert "folder" not in sdk_data


class TestBgpAuthProfile:
    """Test cases for the BgpAuthProfile model."""

    def test_valid_profile(self):
        """Test creating a valid BGP auth profile."""
        profile = BgpAuthProfile(name="test-auth", folder="test-folder", secret="my-secret")
        assert profile.name == "test-auth"
        assert profile.secret == "my-secret"

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            BgpAuthProfile(name="test-auth")

    def test_multiple_containers_rejected(self):
        """Test that multiple containers are rejected."""
        with pytest.raises(ValidationError):
            BgpAuthProfile(name="test-auth", folder="f", snippet="s")

    def test_minimal_creation(self):
        """Test minimal creation without optional fields."""
        profile = BgpAuthProfile(name="test-auth", folder="test-folder")
        assert profile.secret is None

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = BgpAuthProfile(name="test-auth", folder="test-folder", secret="my-secret")
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "test-auth"
        assert sdk_data["folder"] == "test-folder"
        assert sdk_data["secret"] == "my-secret"

    def test_to_sdk_model_no_secret(self):
        """Test SDK model without secret."""
        profile = BgpAuthProfile(name="test-auth", folder="test-folder")
        sdk_data = profile.to_sdk_model()
        assert "secret" not in sdk_data


class TestOspfAuthProfile:
    """Test cases for the OspfAuthProfile model."""

    def test_valid_password_profile(self):
        """Test creating an OSPF auth profile with password."""
        profile = OspfAuthProfile(name="test-ospf", folder="test-folder", password="my-pass")
        assert profile.name == "test-ospf"
        assert profile.password == "my-pass"

    def test_valid_md5_profile(self):
        """Test creating an OSPF auth profile with MD5."""
        profile = OspfAuthProfile(name="test-ospf", folder="test-folder", md5=[{"name": 1, "key": "abc123"}])
        assert profile.md5 == [{"name": 1, "key": "abc123"}]

    def test_password_md5_mutually_exclusive(self):
        """Test that password and MD5 are mutually exclusive."""
        with pytest.raises(ValidationError):
            OspfAuthProfile(name="test-ospf", folder="test-folder", password="pass", md5=[{"name": 1, "key": "abc"}])

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            OspfAuthProfile(name="test-ospf")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = OspfAuthProfile(name="test-ospf", folder="test-folder", password="my-pass")
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "test-ospf"
        assert sdk_data["password"] == "my-pass"

    def test_minimal_creation(self):
        """Test minimal creation without auth fields."""
        profile = OspfAuthProfile(name="test-ospf", folder="test-folder")
        assert profile.password is None
        assert profile.md5 is None


class TestRouteAccessList:
    """Test cases for the RouteAccessList model."""

    def test_valid_route_access_list(self):
        """Test creating a valid route access list."""
        acl = RouteAccessList(name="test-acl", folder="test-folder", description="Test ACL")
        assert acl.name == "test-acl"
        assert acl.description == "Test ACL"

    def test_with_type_config(self):
        """Test creating with type configuration."""
        acl = RouteAccessList(name="test-acl", folder="test-folder", type={"ipv4": {"ipv4_entry": [{"name": 10, "action": "permit"}]}})
        assert acl.type is not None

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            RouteAccessList(name="test-acl")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        acl = RouteAccessList(name="test-acl", folder="test-folder", description="Test", type={"ipv4": {}})
        sdk_data = acl.to_sdk_model()
        assert sdk_data["name"] == "test-acl"
        assert sdk_data["description"] == "Test"
        assert sdk_data["type"] == {"ipv4": {}}

    def test_minimal_creation(self):
        """Test minimal creation."""
        acl = RouteAccessList(name="test-acl", folder="test-folder")
        assert acl.description is None
        assert acl.type is None

    def test_device_container(self):
        """Test with device container."""
        acl = RouteAccessList(name="test-acl", device="test-device")
        sdk_data = acl.to_sdk_model()
        assert sdk_data["device"] == "test-device"


class TestRoutePrefixList:
    """Test cases for the RoutePrefixList model."""

    def test_valid_prefix_list(self):
        """Test creating a valid route prefix list."""
        pl = RoutePrefixList(name="test-pl", folder="test-folder", description="Test PL")
        assert pl.name == "test-pl"
        assert pl.description == "Test PL"

    def test_with_ipv4_config(self):
        """Test creating with IPv4 configuration."""
        pl = RoutePrefixList(name="test-pl", folder="test-folder", ipv4={"ipv4_entry": [{"name": 10, "action": "permit"}]})
        assert pl.ipv4 is not None

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            RoutePrefixList(name="test-pl")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        pl = RoutePrefixList(name="test-pl", folder="test-folder", description="Test", ipv4={"ipv4_entry": []})
        sdk_data = pl.to_sdk_model()
        assert sdk_data["name"] == "test-pl"
        assert sdk_data["description"] == "Test"
        assert sdk_data["ipv4"] == {"ipv4_entry": []}

    def test_minimal_creation(self):
        """Test minimal creation."""
        pl = RoutePrefixList(name="test-pl", folder="test-folder")
        assert pl.description is None
        assert pl.ipv4 is None

    def test_snippet_container(self):
        """Test with snippet container."""
        pl = RoutePrefixList(name="test-pl", snippet="test-snippet")
        sdk_data = pl.to_sdk_model()
        assert sdk_data["snippet"] == "test-snippet"


class TestBgpFilteringProfile:
    """Test cases for the BgpFilteringProfile model."""

    def test_valid_profile(self):
        """Test creating a valid BGP filtering profile."""
        profile = BgpFilteringProfile(name="test-filter", folder="test-folder", ipv4={"unicast": {"filter_list": {"inbound": "test"}}})
        assert profile.name == "test-filter"
        assert profile.ipv4 is not None

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            BgpFilteringProfile(name="test-filter")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = BgpFilteringProfile(name="test-filter", folder="test-folder", ipv4={"unicast": {}})
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "test-filter"
        assert sdk_data["ipv4"] == {"unicast": {}}

    def test_minimal_creation(self):
        """Test minimal creation."""
        profile = BgpFilteringProfile(name="test-filter", folder="test-folder")
        assert profile.ipv4 is None

    def test_multiple_containers_rejected(self):
        """Test that multiple containers are rejected."""
        with pytest.raises(ValidationError):
            BgpFilteringProfile(name="test-filter", folder="f", device="d")

    def test_to_sdk_model_device(self):
        """Test SDK model with device container."""
        profile = BgpFilteringProfile(name="test-filter", device="dev1")
        sdk_data = profile.to_sdk_model()
        assert sdk_data["device"] == "dev1"


class TestBgpRedistributionProfile:
    """Test cases for the BgpRedistributionProfile model."""

    def test_valid_profile(self):
        """Test creating a valid BGP redistribution profile."""
        profile = BgpRedistributionProfile(name="test-redist", folder="test-folder", ipv4={"unicast": {"static": {"enable": True}}})
        assert profile.name == "test-redist"
        assert profile.ipv4 is not None

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            BgpRedistributionProfile(name="test-redist")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = BgpRedistributionProfile(name="test-redist", folder="test-folder", ipv4={"unicast": {"static": {"enable": True}}})
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "test-redist"
        assert sdk_data["ipv4"]["unicast"]["static"]["enable"] is True

    def test_minimal_creation(self):
        """Test minimal creation."""
        profile = BgpRedistributionProfile(name="test-redist", folder="test-folder")
        assert profile.ipv4 is None

    def test_multiple_containers_rejected(self):
        """Test that multiple containers are rejected."""
        with pytest.raises(ValidationError):
            BgpRedistributionProfile(name="test-redist", folder="f", snippet="s")

    def test_to_sdk_model_snippet(self):
        """Test SDK model with snippet container."""
        profile = BgpRedistributionProfile(name="test-redist", snippet="test-snippet")
        sdk_data = profile.to_sdk_model()
        assert sdk_data["snippet"] == "test-snippet"


class TestBgpRouteMap:
    """Test cases for the BgpRouteMap model."""

    def test_valid_route_map(self):
        """Test creating a valid BGP route map."""
        rm = BgpRouteMap(name="test-rm", folder="test-folder", route_map=[{"name": 10, "action": "permit"}])
        assert rm.name == "test-rm"
        assert len(rm.route_map) == 1

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            BgpRouteMap(name="test-rm")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        rm = BgpRouteMap(name="test-rm", folder="test-folder", route_map=[{"name": 10, "action": "permit"}])
        sdk_data = rm.to_sdk_model()
        assert sdk_data["name"] == "test-rm"
        assert sdk_data["route_map"] == [{"name": 10, "action": "permit"}]

    def test_minimal_creation(self):
        """Test minimal creation."""
        rm = BgpRouteMap(name="test-rm", folder="test-folder")
        assert rm.route_map is None

    def test_multiple_containers_rejected(self):
        """Test that multiple containers are rejected."""
        with pytest.raises(ValidationError):
            BgpRouteMap(name="test-rm", folder="f", device="d")

    def test_to_sdk_model_no_entries(self):
        """Test SDK model without route map entries."""
        rm = BgpRouteMap(name="test-rm", folder="test-folder")
        sdk_data = rm.to_sdk_model()
        assert "route_map" not in sdk_data


class TestBgpRouteMapRedistribution:
    """Test cases for the BgpRouteMapRedistribution model."""

    def test_valid_bgp_source(self):
        """Test creating with BGP as source protocol."""
        rmr = BgpRouteMapRedistribution(name="test-rmr", folder="test-folder", bgp={"ospf": {"route_map": []}})
        assert rmr.name == "test-rmr"
        assert rmr.bgp is not None

    def test_valid_ospf_source(self):
        """Test creating with OSPF as source protocol."""
        rmr = BgpRouteMapRedistribution(name="test-rmr", folder="test-folder", ospf={"bgp": {"route_map": []}})
        assert rmr.ospf is not None

    def test_multiple_sources_rejected(self):
        """Test that multiple source protocols are rejected."""
        with pytest.raises(ValidationError):
            BgpRouteMapRedistribution(name="test-rmr", folder="test-folder", bgp={"ospf": {}}, ospf={"bgp": {}})

    def test_container_validation(self):
        """Test that exactly one container is required."""
        with pytest.raises(ValidationError):
            BgpRouteMapRedistribution(name="test-rmr")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        rmr = BgpRouteMapRedistribution(name="test-rmr", folder="test-folder", bgp={"ospf": {"route_map": []}})
        sdk_data = rmr.to_sdk_model()
        assert sdk_data["name"] == "test-rmr"
        assert sdk_data["bgp"] == {"ospf": {"route_map": []}}

    def test_minimal_creation(self):
        """Test minimal creation without source protocol."""
        rmr = BgpRouteMapRedistribution(name="test-rmr", folder="test-folder")
        assert rmr.bgp is None
        assert rmr.ospf is None
        assert rmr.connected_static is None

    def test_connected_static_source(self):
        """Test creating with connected_static as source protocol."""
        rmr = BgpRouteMapRedistribution(name="test-rmr", folder="test-folder", connected_static={"bgp": {"route_map": []}})
        sdk_data = rmr.to_sdk_model()
        assert sdk_data["connected_static"] == {"bgp": {"route_map": []}}


class TestAppOverrideRule:
    """Test cases for the AppOverrideRule model."""

    def test_valid_rule(self):
        """Test creating a valid app override rule."""
        rule = AppOverrideRule(
            name="test-override",
            folder="Texas",
            application="ssl",
            port="8443",
            protocol="tcp",
        )
        assert rule.name == "test-override"
        assert rule.application == "ssl"
        assert rule.port == "8443"
        assert rule.protocol == "tcp"
        assert rule.rulebase == "pre"

    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            AppOverrideRule(name="test", folder="Texas", port="443", protocol="tcp")  # missing application

    def test_invalid_protocol(self):
        """Test invalid protocol value."""
        with pytest.raises(ValidationError):
            AppOverrideRule(name="test", folder="Texas", application="ssl", port="443", protocol="icmp")

    def test_invalid_rulebase(self):
        """Test invalid rulebase value."""
        with pytest.raises(ValidationError):
            AppOverrideRule(name="test", folder="Texas", application="ssl", port="443", protocol="tcp", rulebase="invalid")

    def test_container_validation(self):
        """Test container validation."""
        with pytest.raises(ValidationError):
            AppOverrideRule(name="test", application="ssl", port="443", protocol="tcp")  # no container

    def test_default_values(self):
        """Test default values."""
        rule = AppOverrideRule(name="test", folder="Texas", application="ssl", port="443", protocol="tcp")
        assert rule.from_zones == ["any"]
        assert rule.to_zones == ["any"]
        assert rule.source == ["any"]
        assert rule.destination == ["any"]
        assert rule.disabled is False

    def test_to_sdk_model(self):
        """Test SDK model conversion."""
        rule = AppOverrideRule(
            name="test",
            folder="Texas",
            application="ssl",
            port="8443",
            protocol="tcp",
            description="Test rule",
            tag=["web"],
        )
        sdk = rule.to_sdk_model()
        assert sdk["name"] == "test"
        assert sdk["application"] == "ssl"
        assert sdk["port"] == "8443"
        assert sdk["protocol"] == "tcp"
        assert sdk["folder"] == "Texas"
        assert sdk["from"] == ["any"]
        assert sdk["to"] == ["any"]
        assert sdk["description"] == "Test rule"
        assert sdk["tag"] == ["web"]

    def test_to_sdk_model_no_optional(self):
        """Test SDK model conversion without optional fields."""
        rule = AppOverrideRule(name="test", folder="Texas", application="ssl", port="443", protocol="udp")
        sdk = rule.to_sdk_model()
        assert "description" not in sdk
        assert "tag" not in sdk
        assert "disabled" not in sdk


class TestAuthenticationRule:
    """Test cases for the AuthenticationRule model."""

    def test_valid_rule(self):
        """Test creating a valid authentication rule."""
        rule = AuthenticationRule(name="auth-web", folder="Texas")
        assert rule.name == "auth-web"
        assert rule.folder == "Texas"
        assert rule.rulebase == "pre"

    def test_missing_name(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            AuthenticationRule(folder="Texas")

    def test_container_validation(self):
        """Test container validation."""
        with pytest.raises(ValidationError):
            AuthenticationRule(name="test")

    def test_invalid_rulebase(self):
        """Test invalid rulebase value."""
        with pytest.raises(ValidationError):
            AuthenticationRule(name="test", folder="Texas", rulebase="default")

    def test_default_values(self):
        """Test default values."""
        rule = AuthenticationRule(name="test", folder="Texas")
        assert rule.from_zones == ["any"]
        assert rule.to_zones == ["any"]
        assert rule.source == ["any"]
        assert rule.destination == ["any"]
        assert rule.service == ["any"]
        assert rule.category == ["any"]
        assert rule.disabled is False

    def test_to_sdk_model(self):
        """Test SDK model conversion."""
        rule = AuthenticationRule(
            name="auth-web",
            folder="Texas",
            description="Auth rule",
            authentication_enforcement="default-auth",
            tag=["auth"],
        )
        sdk = rule.to_sdk_model()
        assert sdk["name"] == "auth-web"
        assert sdk["folder"] == "Texas"
        assert sdk["description"] == "Auth rule"
        assert sdk["authentication_enforcement"] == "default-auth"
        assert sdk["tag"] == ["auth"]

    def test_to_sdk_model_with_all_fields(self):
        """Test SDK model with all optional fields."""
        rule = AuthenticationRule(
            name="test",
            folder="Texas",
            timeout=60,
            log_setting="default",
            log_authentication_timeout=True,
        )
        sdk = rule.to_sdk_model()
        assert sdk["timeout"] == 60
        assert sdk["log_setting"] == "default"
        assert sdk["log_authentication_timeout"] is True


class TestDecryptionRule:
    """Test cases for the DecryptionRule model."""

    def test_valid_rule(self):
        """Test creating a valid decryption rule."""
        rule = DecryptionRule(name="no-decrypt-internal", folder="Texas", action="no-decrypt")
        assert rule.name == "no-decrypt-internal"
        assert rule.action == "no-decrypt"
        assert rule.rulebase == "pre"

    def test_missing_action(self):
        """Test that action is required."""
        with pytest.raises(ValidationError):
            DecryptionRule(name="test", folder="Texas")

    def test_invalid_action(self):
        """Test invalid action value."""
        with pytest.raises(ValidationError):
            DecryptionRule(name="test", folder="Texas", action="allow")

    def test_container_validation(self):
        """Test container validation."""
        with pytest.raises(ValidationError):
            DecryptionRule(name="test", action="decrypt")

    def test_default_values(self):
        """Test default values."""
        rule = DecryptionRule(name="test", folder="Texas", action="decrypt")
        assert rule.from_zones == ["any"]
        assert rule.to_zones == ["any"]
        assert rule.disabled is False

    def test_to_sdk_model(self):
        """Test SDK model conversion."""
        rule = DecryptionRule(
            name="decrypt-out",
            folder="Texas",
            action="decrypt",
            profile="ssl-profile",
            tag=["decrypt"],
            type={"ssl_forward_proxy": {}},
        )
        sdk = rule.to_sdk_model()
        assert sdk["name"] == "decrypt-out"
        assert sdk["action"] == "decrypt"
        assert sdk["folder"] == "Texas"
        assert sdk["profile"] == "ssl-profile"
        assert sdk["tag"] == ["decrypt"]
        assert sdk["type"] == {"ssl_forward_proxy": {}}

    def test_to_sdk_model_minimal(self):
        """Test SDK model with minimal fields."""
        rule = DecryptionRule(name="test", folder="Texas", action="no-decrypt")
        sdk = rule.to_sdk_model()
        assert "profile" not in sdk
        assert "type" not in sdk
        assert "tag" not in sdk

    def test_decrypt_action_case_insensitive(self):
        """Test action is case-normalized."""
        rule = DecryptionRule(name="test", folder="Texas", action="NO-DECRYPT")
        assert rule.action == "no-decrypt"


class TestURLAccessProfile:
    """Test cases for the URLAccessProfile model."""

    def test_valid_profile(self):
        """Test creating a valid URL access profile."""
        profile = URLAccessProfile(name="strict-url", folder="Texas")
        assert profile.name == "strict-url"
        assert profile.folder == "Texas"

    def test_missing_name(self):
        """Test that name is required."""
        with pytest.raises(ValidationError):
            URLAccessProfile(folder="Texas")

    def test_container_validation(self):
        """Test container validation."""
        with pytest.raises(ValidationError):
            URLAccessProfile(name="test")

    def test_with_categories(self):
        """Test with URL category lists."""
        profile = URLAccessProfile(
            name="test",
            folder="Texas",
            block=["adult", "malware"],
            alert=["hacking"],
            allow=["business-and-economy"],
        )
        assert profile.block == ["adult", "malware"]
        assert profile.alert == ["hacking"]
        assert profile.allow == ["business-and-economy"]

    def test_to_sdk_model(self):
        """Test SDK model conversion."""
        profile = URLAccessProfile(
            name="strict",
            folder="Texas",
            block=["adult", "malware"],
            alert=["hacking"],
            description="Strict URL filtering",
            cloud_inline_cat=True,
            safe_search_enforcement=True,
        )
        sdk = profile.to_sdk_model()
        assert sdk["name"] == "strict"
        assert sdk["folder"] == "Texas"
        assert sdk["block"] == ["adult", "malware"]
        assert sdk["alert"] == ["hacking"]
        assert sdk["description"] == "Strict URL filtering"
        assert sdk["cloud_inline_cat"] is True
        assert sdk["safe_search_enforcement"] is True

    def test_to_sdk_model_continue_categories(self):
        """Test SDK model conversion with continue categories."""
        profile = URLAccessProfile(
            name="test",
            folder="Texas",
            continue_categories=["streaming-media"],
        )
        sdk = profile.to_sdk_model()
        assert sdk["continue"] == ["streaming-media"]

    def test_to_sdk_model_minimal(self):
        """Test SDK model with minimal fields."""
        profile = URLAccessProfile(name="test", folder="Texas")
        sdk = profile.to_sdk_model()
        assert sdk["name"] == "test"
        assert sdk["folder"] == "Texas"
        assert "block" not in sdk
        assert "alert" not in sdk


# ========================================================================================================================================================================================
# IDENTITY CONFIGURATION MODEL TESTS
# ========================================================================================================================================================================================


class TestAuthenticationProfile:
    """Test cases for the AuthenticationProfile model."""

    def test_valid_authentication_profile(self):
        """Test creating a valid authentication profile."""
        profile = AuthenticationProfile(
            name="test-auth",
            folder="Texas",
            method={"local_database": {}},
            allow_list=["all"],
        )
        assert profile.name == "test-auth"
        assert profile.folder == "Texas"
        assert profile.method == {"local_database": {}}

    def test_container_validation(self):
        """Test container field validation."""
        with pytest.raises(ValidationError):
            AuthenticationProfile(
                name="test-auth",
                folder="Texas",
                snippet="MySnippet",
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = AuthenticationProfile(
            name="test-auth",
            folder="Texas",
            method={"ldap": {"server_profile": "corp-ldap"}},
            user_domain="example.com",
            allow_list=["all"],
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "test-auth"
        assert sdk_data["folder"] == "Texas"
        assert sdk_data["method"] == {"ldap": {"server_profile": "corp-ldap"}}
        assert sdk_data["user_domain"] == "example.com"
        assert sdk_data["allow_list"] == ["all"]

    def test_to_sdk_model_minimal(self):
        """Test conversion with minimal fields."""
        profile = AuthenticationProfile(name="test-auth", folder="Texas")
        sdk_data = profile.to_sdk_model()
        assert sdk_data == {"name": "test-auth", "folder": "Texas"}


class TestKerberosServerProfile:
    """Test cases for the KerberosServerProfile model."""

    def test_valid_profile(self):
        """Test creating a valid Kerberos server profile."""
        profile = KerberosServerProfile(
            name="corp-kerberos",
            folder="Texas",
            servers=[{"name": "kdc1", "host": "kdc1.example.com", "port": 88}],
        )
        assert profile.name == "corp-kerberos"
        assert len(profile.servers) == 1

    def test_container_validation(self):
        """Test container field validation."""
        with pytest.raises(ValidationError):
            KerberosServerProfile(name="test", folder="Texas", snippet="MySnippet")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = KerberosServerProfile(
            name="corp-kerberos",
            folder="Texas",
            servers=[{"name": "kdc1", "host": "kdc1.example.com", "port": 88}],
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "corp-kerberos"
        assert sdk_data["folder"] == "Texas"
        assert sdk_data["server"] == [{"name": "kdc1", "host": "kdc1.example.com", "port": 88}]


class TestLdapServerProfile:
    """Test cases for the LdapServerProfile model."""

    def test_valid_profile(self):
        """Test creating a valid LDAP server profile."""
        profile = LdapServerProfile(
            name="corp-ldap",
            folder="Texas",
            servers=[{"name": "ldap1", "address": "ldap.example.com", "port": 389}],
            base="dc=example,dc=com",
            ldap_type="active-directory",
        )
        assert profile.name == "corp-ldap"
        assert profile.ldap_type == "active-directory"

    def test_invalid_ldap_type(self):
        """Test invalid LDAP type."""
        with pytest.raises(ValidationError):
            LdapServerProfile(name="test", folder="Texas", ldap_type="invalid-type")

    def test_container_validation(self):
        """Test container field validation."""
        with pytest.raises(ValidationError):
            LdapServerProfile(name="test", folder="Texas", snippet="MySnippet")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = LdapServerProfile(
            name="corp-ldap",
            folder="Texas",
            servers=[{"name": "ldap1", "address": "ldap.example.com", "port": 389}],
            base="dc=example,dc=com",
            ldap_type="active-directory",
            ssl=True,
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "corp-ldap"
        assert sdk_data["server"] == [{"name": "ldap1", "address": "ldap.example.com", "port": 389}]
        assert sdk_data["base"] == "dc=example,dc=com"
        assert sdk_data["ldap_type"] == "active-directory"
        assert sdk_data["ssl"] is True


class TestRadiusServerProfile:
    """Test cases for the RadiusServerProfile model."""

    def test_valid_profile(self):
        """Test creating a valid RADIUS server profile."""
        profile = RadiusServerProfile(
            name="corp-radius",
            folder="Texas",
            servers=[{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812, "secret": "s3cret"}],
            protocol={"CHAP": {}},
            timeout=5,
            retries=3,
        )
        assert profile.name == "corp-radius"
        assert profile.timeout == 5
        assert profile.retries == 3

    def test_timeout_range(self):
        """Test timeout validation range."""
        with pytest.raises(ValidationError):
            RadiusServerProfile(name="test", folder="Texas", timeout=121)

    def test_retries_range(self):
        """Test retries validation range."""
        with pytest.raises(ValidationError):
            RadiusServerProfile(name="test", folder="Texas", retries=6)

    def test_container_validation(self):
        """Test container field validation."""
        with pytest.raises(ValidationError):
            RadiusServerProfile(name="test", folder="Texas", snippet="MySnippet")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = RadiusServerProfile(
            name="corp-radius",
            folder="Texas",
            servers=[{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812}],
            protocol={"CHAP": {}},
            timeout=5,
            retries=3,
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "corp-radius"
        assert sdk_data["server"] == [{"name": "rad1", "ip_address": "10.0.0.1", "port": 1812}]
        assert sdk_data["protocol"] == {"CHAP": {}}
        assert sdk_data["timeout"] == 5
        assert sdk_data["retries"] == 3


class TestSamlServerProfile:
    """Test cases for the SamlServerProfile model."""

    def test_valid_profile(self):
        """Test creating a valid SAML server profile."""
        profile = SamlServerProfile(
            name="corp-saml",
            folder="Texas",
            entity_id="https://idp.example.com",
            certificate="idp-cert",
            sso_url="https://idp.example.com/sso",
            sso_bindings="post",
        )
        assert profile.name == "corp-saml"
        assert profile.sso_bindings == "post"

    def test_invalid_sso_bindings(self):
        """Test invalid SSO bindings."""
        with pytest.raises(ValidationError):
            SamlServerProfile(
                name="test",
                folder="Texas",
                entity_id="https://idp.example.com",
                certificate="cert",
                sso_url="https://idp.example.com/sso",
                sso_bindings="invalid",
            )

    def test_container_validation(self):
        """Test container field validation."""
        with pytest.raises(ValidationError):
            SamlServerProfile(
                name="test",
                folder="Texas",
                snippet="MySnippet",
                entity_id="https://idp.example.com",
                certificate="cert",
                sso_url="https://idp.example.com/sso",
                sso_bindings="post",
            )

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = SamlServerProfile(
            name="corp-saml",
            folder="Texas",
            entity_id="https://idp.example.com",
            certificate="idp-cert",
            sso_url="https://idp.example.com/sso",
            sso_bindings="post",
            slo_bindings="redirect",
            max_clock_skew=60,
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "corp-saml"
        assert sdk_data["folder"] == "Texas"
        assert sdk_data["entity_id"] == "https://idp.example.com"
        assert sdk_data["sso_bindings"] == "post"
        assert sdk_data["slo_bindings"] == "redirect"
        assert sdk_data["max_clock_skew"] == 60


class TestTacacsServerProfile:
    """Test cases for the TacacsServerProfile model."""

    def test_valid_profile(self):
        """Test creating a valid TACACS+ server profile."""
        profile = TacacsServerProfile(
            name="corp-tacacs",
            folder="Texas",
            servers=[{"name": "tac1", "address": "10.0.0.1", "port": 49, "secret": "s3cret"}],
            protocol="CHAP",
            timeout=5,
        )
        assert profile.name == "corp-tacacs"
        assert profile.protocol == "CHAP"

    def test_invalid_protocol(self):
        """Test invalid protocol."""
        with pytest.raises(ValidationError):
            TacacsServerProfile(name="test", folder="Texas", protocol="INVALID")

    def test_timeout_range(self):
        """Test timeout validation range."""
        with pytest.raises(ValidationError):
            TacacsServerProfile(name="test", folder="Texas", timeout=31)

    def test_container_validation(self):
        """Test container field validation."""
        with pytest.raises(ValidationError):
            TacacsServerProfile(name="test", folder="Texas", snippet="MySnippet")

    def test_to_sdk_model(self):
        """Test conversion to SDK model format."""
        profile = TacacsServerProfile(
            name="corp-tacacs",
            folder="Texas",
            servers=[{"name": "tac1", "address": "10.0.0.1", "port": 49}],
            protocol="CHAP",
            timeout=5,
            use_single_connection=True,
        )
        sdk_data = profile.to_sdk_model()
        assert sdk_data["name"] == "corp-tacacs"
        assert sdk_data["server"] == [{"name": "tac1", "address": "10.0.0.1", "port": 49}]
        assert sdk_data["protocol"] == "CHAP"
        assert sdk_data["timeout"] == 5
        assert sdk_data["use_single_connection"] is True

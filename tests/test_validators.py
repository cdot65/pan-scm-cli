"""Tests for the validators module."""

import pytest
from pydantic import ValidationError

from scm_cli.utils.validators import AddressGroup, BandwidthAllocation, DNSSecurityProfile, IKECryptoProfile, QuarantinedDevice, Region, Schedule, SecurityRule, WildfireAntivirusProfile, Zone
from scm_cli.utils.validators import AddressGroup, BandwidthAllocation, IPSecCryptoProfile, SecurityRule, Zone


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

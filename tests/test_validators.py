"""Tests for the validators module."""

import pytest
from pydantic import ValidationError
from scm_cli.utils.validators import AddressGroup, BandwidthAllocation, Schedule, SecurityRule, Zone


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

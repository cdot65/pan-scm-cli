"""Tests for the config module."""

import pytest
import yaml

from scm_cli.utils.config import load_from_yaml


def test_load_from_yaml_valid(mock_yaml_file):
    """Test loading a valid YAML file."""
    config = load_from_yaml(mock_yaml_file, "bandwidth_allocations")
    assert "bandwidth_allocations" in config
    assert len(config["bandwidth_allocations"]) == 1
    assert config["bandwidth_allocations"][0]["name"] == "test-allocation"
    assert config["bandwidth_allocations"][0]["bandwidth"] == 1000
    assert config["bandwidth_allocations"][0]["spn_name_list"] == ["spn1"]
    assert config["bandwidth_allocations"][0]["description"] == "Test allocation"
    assert "test" in config["bandwidth_allocations"][0]["tags"]
    assert "example" in config["bandwidth_allocations"][0]["tags"]


def test_load_from_yaml_file_not_found():
    """Test loading a non-existent YAML file."""
    with pytest.raises(FileNotFoundError):
        load_from_yaml("non_existent_file.yml", "bandwidth_allocations")


def test_load_from_yaml_invalid_format(tmp_path):
    """Test loading an invalid YAML file."""
    invalid_yaml = tmp_path / "invalid.yml"
    invalid_yaml.write_text("this is not valid yaml: :")

    with pytest.raises(yaml.YAMLError):
        load_from_yaml(invalid_yaml, "bandwidth_allocations")


def test_load_from_yaml_missing_section(tmp_path):
    """Test loading a YAML file with a missing required section."""
    missing_section = tmp_path / "missing_section.yml"
    missing_section.write_text("""
    other_section:
      - name: test
        value: test
    """)

    with pytest.raises(ValueError, match="Missing 'bandwidth_allocations' section"):
        load_from_yaml(missing_section, "bandwidth_allocations")


def test_load_from_yaml_empty_file(tmp_path):
    """Test loading an empty YAML file."""
    empty_file = tmp_path / "empty.yml"
    empty_file.write_text("")

    with pytest.raises(ValueError, match="Empty or invalid YAML file"):
        load_from_yaml(empty_file, "bandwidth_allocations")

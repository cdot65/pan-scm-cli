"""Tests for scm_cli.utils shared utility functions."""

import pytest
from click.exceptions import Exit

from scm_cli.utils import validate_location_params


class TestValidateLocationParams:
    """Tests for validate_location_params utility function."""

    def test_folder_only(self):
        """Return ('folder', value) when only folder is provided."""
        result = validate_location_params(folder="Shared")
        assert result == ("folder", "Shared")

    def test_snippet_only(self):
        """Return ('snippet', value) when only snippet is provided."""
        result = validate_location_params(snippet="my-snippet")
        assert result == ("snippet", "my-snippet")

    def test_device_only(self):
        """Return ('device', value) when only device is provided."""
        result = validate_location_params(device="fw-01")
        assert result == ("device", "fw-01")

    def test_no_location_raises_exit(self):
        """Raise typer.Exit when no location is provided."""
        with pytest.raises(Exit):
            validate_location_params()

    def test_multiple_locations_raises_exit(self):
        """Raise typer.Exit when multiple locations are provided."""
        with pytest.raises(Exit):
            validate_location_params(folder="Shared", snippet="my-snippet")

    def test_all_three_raises_exit(self):
        """Raise typer.Exit when all three locations are provided."""
        with pytest.raises(Exit):
            validate_location_params(folder="Shared", snippet="my-snippet", device="fw-01")

    def test_folder_and_device_raises_exit(self):
        """Raise typer.Exit when folder and device are provided."""
        with pytest.raises(Exit):
            validate_location_params(folder="Shared", device="fw-01")

    def test_return_type(self):
        """Return a tuple of two strings."""
        result = validate_location_params(folder="Shared")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)

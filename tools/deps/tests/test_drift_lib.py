"""Unit tests for drift_lib."""

from __future__ import annotations

import pytest
from drift_lib import Finding, Sighting, normalize_name


class TestDataClasses:
    """Tests for Sighting and Finding dataclasses."""

    def test_sighting_holds_package_file_location_version(self):
        """Sighting stores package, file, location, and version fields."""
        s = Sighting(package="pyyaml", file="requirements-dev.txt", location="line 3", version=">=6.0.3")
        assert s.package == "pyyaml"
        assert s.file == "requirements-dev.txt"
        assert s.location == "line 3"
        assert s.version == ">=6.0.3"

    def test_finding_holds_package_status_sightings_recommendation(self):
        """Finding stores package, status, sightings, and recommendation fields."""
        s = Sighting(package="pyyaml", file="requirements-dev.txt", location="line 3", version=">=6.0.3")
        f = Finding(package="pyyaml", status="drift", sightings=[s], recommendation="bump to >=6.0.3")
        assert f.package == "pyyaml"
        assert f.status == "drift"
        assert f.sightings == [s]
        assert f.recommendation == "bump to >=6.0.3"


class TestNormalizeName:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("PyYAML", "pyyaml"),
            ("pyyaml", "pyyaml"),
            ("markdownlint_cli2", "markdownlint-cli2"),
            ("Markdownlint-CLI2", "markdownlint-cli2"),
            ("actions/checkout", "actions/checkout"),
            ("ACTIONS/CHECKOUT", "actions/checkout"),
        ],
    )
    def test_lowercases_and_normalizes_separators(self, raw, expected):
        assert normalize_name(raw) == expected

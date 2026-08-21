"""Tests for the OBIS catalog and metadata lookup."""

import pytest

from obis_parser import (
    OBIS,
    OBIS_CATALOG,
    OBISMeasurementInfo,
)


class TestCatalog:
    def test_catalog_size_and_uniqueness(self) -> None:
        """Verify catalog size and slug uniqueness."""
        assert len(OBIS_CATALOG) == 39
        slugs = [info.slug for info in OBIS_CATALOG.values()]
        assert len(slugs) == len(set(slugs)), "All catalog slugs must be unique"
        assert all(slug for slug in slugs), "Catalog slugs must not be empty"

    def test_catalog_schema_invariants(self) -> None:
        """Verify all catalog entries satisfy structural domain invariants."""
        for key, info in OBIS_CATALOG.items():
            assert isinstance(info, OBISMeasurementInfo)
            assert info.name.strip(), f"Empty name for key {key}"
            assert info.slug.strip(), f"Empty slug for key {key}"
            assert info.icon.startswith("mdi:"), f"Invalid icon '{info.icon}' for key {key}"
            assert info.translation_key == info.slug

            d = key[1]
            if d == 8:
                assert info.state_class == "total_increasing", f"Energy register {key} must be total_increasing"
            elif d == 7:
                assert info.state_class == "measurement", f"Instantaneous register {key} must be measurement"
            else:
                assert info.state_class is None, f"Metadata register {key} must have state_class=None"

            if info.suggested_display_precision is not None:
                assert info.suggested_display_precision >= 0

    @pytest.mark.parametrize(
        "code",
        [
            "2-0:1.8.0",  # Medium != 1
            "7-0:3.0.0",  # Gas
            "1-0:1.8.0*1",  # Historic billing period
            "1-0:81.7.99",  # Uncataloged phase angle E
            "1-0:0.2.1",  # Uncataloged metadata E
            "1-0:96.1.1",  # Uncataloged serial E
        ],
    )
    def test_unmatched_codes_return_none(self, code: str) -> None:
        """Non-electricity, historic periods, and uncataloged exact E return info=None."""
        obis = OBIS.parse(code)
        assert obis is not None
        assert obis.info is None

    @pytest.mark.parametrize(
        ("code", "expected_slug"),
        [
            # Base (C, D) lookups ignore channel and tariff
            ("1-0:1.8.0", "active_energy_import"),
            ("1-1:1.8.0", "active_energy_import"),
            ("1-0:1.8.1", "active_energy_import"),
            ("1-2:1.8.3", "active_energy_import"),
            # Current billing periods (F=None, 0, 255) resolve base info
            ("1-0:1.8.0*0", "active_energy_import"),
            ("1-0:1.8.0*255", "active_energy_import"),
            # Exact (C, D, E) lookups for phase angles and device metadata
            ("1-0:81.7.4", "phase_angle_l1"),
            ("1-1:81.7.4", "phase_angle_l1"),
            ("1-0:0.2.0", "firmware_version"),
            ("1-0:96.1.0", "meter_identification"),
        ],
    )
    def test_get_obis_info_lookup_resolution(self, code: str, expected_slug: str) -> None:
        """info lookup resolves base (C, D) or exact (C, D, E) entries."""
        obis = OBIS.parse(code)
        assert obis is not None
        info = obis.info
        assert info is not None
        assert info.slug == expected_slug

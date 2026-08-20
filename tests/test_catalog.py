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
            "2-0:1.8.0",
            "7-0:3.0.0",
            "2-0:81.7.4",
        ],
    )
    def test_non_electricity_has_no_catalog_match(self, code: str) -> None:
        """Non-electricity medium (A != 1) must never match catalog."""
        obis = OBIS.parse(code)
        assert obis is not None
        assert obis.info is None

    @pytest.mark.parametrize(
        "code",
        [
            "1-0:1.8.0",
            "1-0:1.8.0*0",
            "1-0:1.8.0*255",
            "1-0:81.7.4*255",
        ],
    )
    def test_current_billing_periods_match_catalog(self, code: str) -> None:
        """Current billing periods (F=None, 0, 255) resolve catalog metadata."""
        obis = OBIS.parse(code)
        assert obis is not None
        assert obis.info is not None

    @pytest.mark.parametrize(
        "code",
        [
            "1-0:1.8.0*1",
            "1-0:81.7.4*1",
        ],
    )
    def test_historic_billing_periods_do_not_match_catalog(self, code: str) -> None:
        """Historic billing periods (F > 0 and != 255) return info=None."""
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

    @pytest.mark.parametrize(
        "code",
        [
            "1-0:81.7.99",
            "81.7.99",
            "1-0:0.2.1",
            "1-0:96.1.1",
        ],
    )
    def test_uncataloged_group_e_for_exact_registers_returns_none(self, code: str) -> None:
        """Uncataloged E for exact registers (C=81, C=0, C=96) returns info=None."""
        obis = OBIS.parse(code)
        assert obis is not None
        assert obis.info is None

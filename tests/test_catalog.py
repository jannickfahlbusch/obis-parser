"""Tests for the OBIS catalog and metadata lookup."""

import pytest

from obis_parser import (
    OBIS,
    OBIS_CATALOG,
)


class TestCatalog:
    def test_catalog_size_and_uniqueness(self) -> None:
        assert len(OBIS_CATALOG) == 31
        slugs = [info.slug for info in OBIS_CATALOG.values()]
        assert len(slugs) == len(set(slugs)), "All catalog slugs must be unique"
        assert all(slug for slug in slugs), "Catalog slugs must not be empty"

    @pytest.mark.parametrize(
        ("code", "expected_cd", "expected_slug"),
        [
            ("1-0:1.8.0", (1, 8), "active_energy_import"),
            ("1-0:2.8.0", (2, 8), "active_energy_export"),
            ("1-0:16.7.0", (16, 7), "active_power_total"),
            ("1-0:15.7.0", (15, 7), "absolute_active_power"),
            ("1-0:32.7.0", (32, 7), "voltage_l1"),
            ("1-0:52.7.0", (52, 7), "voltage_l2"),
            ("1-0:72.7.0", (72, 7), "voltage_l3"),
            ("1-0:31.7.0", (31, 7), "current_l1"),
            ("1-0:21.7.0", (21, 7), "active_power_import_l1"),
            ("1-0:22.7.0", (22, 7), "active_power_export_l1"),
            ("1-0:13.7.0", (13, 7), "power_factor"),
            ("1-0:14.7.0", (14, 7), "frequency"),
            ("1-0:3.8.0", (3, 8), "reactive_energy_import"),
            ("1-0:4.8.0", (4, 8), "reactive_energy_export"),
            ("1-0:9.8.0", (9, 8), "apparent_energy"),
        ],
    )
    def test_catalog_entries(self, code: str, expected_cd: tuple[int, int], expected_slug: str) -> None:
        obis = OBIS.parse(code)
        assert obis is not None
        info = obis.info
        assert info is not None
        assert (obis.c, obis.d) == expected_cd
        assert info.slug == expected_slug
        assert info.translation_key == expected_slug

    def test_non_electricity_has_no_catalog_match(self) -> None:
        obis = OBIS.parse("2-0:1.8.0")
        assert obis is not None
        assert obis.info is None

        obis_gas = OBIS.parse("7-0:3.0.0")
        assert obis_gas is not None
        assert obis_gas.info is None

    def test_non_current_billing_period_has_no_catalog_match(self) -> None:
        obis = OBIS.parse("1-0:1.8.0*1")
        assert obis is not None
        assert obis.info is None

    @pytest.mark.parametrize(
        ("code", "expected_cd"),
        [
            ("1-1:1.8.0", (1, 8)),  # Channel 1
            ("1-0:1.8.1", (1, 8)),  # Tariff 1
            ("1-2:1.8.3", (1, 8)),  # Channel 2, Tariff 3
        ],
    )
    def test_get_obis_info_ignores_channel_and_tariff(self, code: str, expected_cd: tuple[int, int]) -> None:
        obis = OBIS.parse(code)
        assert obis is not None
        info = obis.info
        assert info is not None
        assert (obis.c, obis.d) == expected_cd

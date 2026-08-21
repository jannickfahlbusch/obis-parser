"""Tests for OBIS.decode() and OBIS naming methods."""

import pytest

from obis_parser import (
    OBIS,
    OBISMeasurement,
    OBISNameDescriptor,
)


class TestOBISNaming:
    @pytest.mark.parametrize(
        ("code", "expected"),
        [
            # Base register without modifiers
            (
                "1-0:1.8.0",
                OBISNameDescriptor(
                    slug="active_energy_import",
                    placeholders={},
                    fallback_name="Active energy import",
                ),
            ),
            # Channel modifier on base register
            (
                "1-1:1.7.0",
                OBISNameDescriptor(
                    slug="active_power_import_channel",
                    placeholders={"channel": "1"},
                    fallback_name="Active power import (Channel 1)",
                ),
            ),
            # Tariff modifier on base register
            (
                "1-0:1.8.2",
                OBISNameDescriptor(
                    slug="active_energy_import_tariff",
                    placeholders={"tariff": "2"},
                    fallback_name="Active energy import (Tariff 2)",
                ),
            ),
            # Channel + tariff on base register
            (
                "1-3:1.8.4",
                OBISNameDescriptor(
                    slug="active_energy_import_channel_tariff",
                    placeholders={"channel": "3", "tariff": "4"},
                    fallback_name="Active energy import (Channel 3, Tariff 4)",
                ),
            ),
            # Tariff E=255 means total/unspecified (no tariff suffix)
            (
                "1-0:1.8.255",
                OBISNameDescriptor(
                    slug="active_energy_import",
                    placeholders={},
                    fallback_name="Active energy import",
                ),
            ),
            # Exact (C, D, E) phase angle registers
            (
                "1-0:81.7.0",
                OBISNameDescriptor(
                    slug="phase_angle",
                    placeholders={},
                    fallback_name="Phase angle",
                ),
            ),
            (
                "1-0:81.7.1",
                OBISNameDescriptor(
                    slug="phase_angle_u_l2_l1",
                    placeholders={},
                    fallback_name="Phase angle U(L2)-U(L1)",
                ),
            ),
            (
                "1-0:81.7.4",
                OBISNameDescriptor(
                    slug="phase_angle_l1",
                    placeholders={},
                    fallback_name="Phase angle L1",
                ),
            ),
            # Channel on exact (C, D, E) register (must NOT generate tariff suffix!)
            (
                "1-1:81.7.4",
                OBISNameDescriptor(
                    slug="phase_angle_l1_channel",
                    placeholders={"channel": "1"},
                    fallback_name="Phase angle L1 (Channel 1)",
                ),
            ),
            # Exact (C, D, E) device metadata registers
            (
                "1-0:0.2.0",
                OBISNameDescriptor(
                    slug="firmware_version",
                    placeholders={},
                    fallback_name="Firmware version",
                ),
            ),
            (
                "1-0:96.1.0",
                OBISNameDescriptor(
                    slug="meter_identification",
                    placeholders={},
                    fallback_name="Meter identification",
                ),
            ),
        ],
    )
    def test_describe_and_naming_properties(
        self,
        code: str,
        expected: OBISNameDescriptor,
    ) -> None:
        """Verify naming, slug variants, and placeholders across all qualifier patterns."""
        obis = OBIS.parse(code)
        assert obis is not None
        assert obis.describe() == expected
        assert obis.name == expected.fallback_name
        assert obis.slug == expected.slug
        assert obis.translation_key == expected.translation_key
        assert obis.placeholders == expected.placeholders


class TestOBISDecode:
    def test_decode_direct_dataclass_comparison(self) -> None:
        """Verify fully-resolved OBISMeasurement dataclass construction directly."""
        obis_energy = OBIS(1, 0, 1, 8, 0)
        assert obis_energy.decode() == OBISMeasurement(
            code=obis_energy,
            canonical="1-0:1.8.0",
            slug="active_energy_import",
            name="Active energy import",
            unit="kWh",
            device_class="energy",
            state_class="total_increasing",
            icon="mdi:home-import-outline",
            suggested_display_precision=5,
            placeholders={},
            info=obis_energy.info,
        )

        obis_angle = OBIS(1, 0, 81, 7, 4)
        assert obis_angle.decode() == OBISMeasurement(
            code=obis_angle,
            canonical="1-0:81.7.4",
            slug="phase_angle_l1",
            name="Phase angle L1",
            unit="°",
            device_class=None,
            state_class="measurement",
            icon="mdi:angle-acute",
            suggested_display_precision=1,
            placeholders={},
            info=obis_angle.info,
        )

        obis_fw = OBIS(1, 0, 0, 2, 0)
        assert obis_fw.decode() == OBISMeasurement(
            code=obis_fw,
            canonical="1-0:0.2.0",
            slug="firmware_version",
            name="Firmware version",
            unit=None,
            device_class=None,
            state_class=None,
            icon="mdi:chip",
            suggested_display_precision=None,
            placeholders={},
            info=obis_fw.info,
        )

    @pytest.mark.parametrize(
        ("short_code", "canonical_code"),
        [
            ("1.8.0", "1-0:1.8.0"),
            ("1.8.2", "1-0:1.8.2"),
            ("81.7.4", "1-0:81.7.4"),
            ("0.2.0", "1-0:0.2.0"),
            ("96.1.0", "1-0:96.1.0"),
        ],
    )
    def test_decode_shorthand_matches_canonical(self, short_code: str, canonical_code: str) -> None:
        """Decoded shorthand object must be identical to canonical decoded object."""
        m_short = OBIS.parse(short_code)
        m_canon = OBIS.parse(canonical_code)
        assert m_short is not None
        assert m_canon is not None
        assert m_short.decode() == m_canon.decode()

    @pytest.mark.parametrize(
        ("code", "expected_canonical"),
        [
            ("1-0:99.99.99", "1-0:99.99.99"),
            ("1-0:81.7.99", "1-0:81.7.99"),
            ("1-0:0.2.1", "1-0:0.2.1"),
            ("1-0:96.1.1", "1-0:96.1.1"),
            ("1-0:1.8.0*1", "1-0:1.8.0*1"),
            ("7-0:3.0.0", "7-0:3.0.0"),
        ],
    )
    def test_decode_fallback_codes_as_unknown(self, code: str, expected_canonical: str) -> None:
        """Uncataloged codes, historic periods, and non-electricity mediums decode as unknown_code."""
        obis = OBIS.parse(code)
        assert obis is not None
        m = obis.decode()
        assert m.canonical == expected_canonical
        assert m.slug == "unknown_code"
        assert m.translation_key == "unknown_code"
        assert m.name == f"OBIS {expected_canonical}"
        assert m.placeholders == {"code": expected_canonical}
        assert m.info is None
        assert m.unit is None
        assert m.icon == "mdi:gauge"

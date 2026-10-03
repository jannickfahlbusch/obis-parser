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
            # 1. Base register without modifiers
            (
                "1-0:1.8.0",
                OBISNameDescriptor(
                    slug="active_energy_import",
                    placeholders={},
                    fallback_name="Active energy import",
                ),
            ),
            # 2. Channel qualifier on base register
            (
                "1-1:1.8.0",
                OBISNameDescriptor(
                    slug="active_energy_import_channel",
                    placeholders={"channel": "1"},
                    fallback_name="Active energy import (Channel 1)",
                ),
            ),
            # 3. Tariff qualifier on base register
            (
                "1-0:1.8.2",
                OBISNameDescriptor(
                    slug="active_energy_import_tariff",
                    placeholders={"tariff": "2"},
                    fallback_name="Active energy import (Tariff 2)",
                ),
            ),
            # 4. Channel + tariff on base register
            (
                "1-3:1.8.4",
                OBISNameDescriptor(
                    slug="active_energy_import_channel_tariff",
                    placeholders={"channel": "3", "tariff": "4"},
                    fallback_name="Active energy import (Channel 3, Tariff 4)",
                ),
            ),
            # 5. Tariff total / unspecified (E=255) generates no tariff suffix
            (
                "1-0:1.8.255",
                OBISNameDescriptor(
                    slug="active_energy_import",
                    placeholders={},
                    fallback_name="Active energy import",
                ),
            ),
            # 6. Exact (C, D, E) register ignores tariff E (no _tariff suffix despite E=4)
            (
                "1-0:81.7.4",
                OBISNameDescriptor(
                    slug="phase_angle_l1",
                    placeholders={},
                    fallback_name="Phase angle L1",
                ),
            ),
            # 7. Channel on exact (C, D, E) register generates _channel, NOT _channel_tariff
            (
                "1-1:81.7.4",
                OBISNameDescriptor(
                    slug="phase_angle_l1_channel",
                    placeholders={"channel": "1"},
                    fallback_name="Phase angle L1 (Channel 1)",
                ),
            ),
        ],
    )
    def test_describe_qualifier_patterns(
        self,
        code: str,
        expected: OBISNameDescriptor,
    ) -> None:
        """Verify naming, slug variants, and placeholders across all qualifier patterns."""
        obis = OBIS.parse(code)
        assert obis is not None
        assert obis.describe() == expected

    def test_naming_convenience_properties(self) -> None:
        """Verify OBIS properties forward to OBISNameDescriptor fields."""
        obis = OBIS.parse("1-1:1.8.2")
        assert obis is not None
        desc = obis.describe()
        assert obis.name == desc.fallback_name == "Active energy import (Channel 1, Tariff 2)"
        assert obis.slug == desc.slug == "active_energy_import_channel_tariff"
        assert obis.translation_key == desc.translation_key == "active_energy_import_channel_tariff"
        assert obis.placeholders == desc.placeholders == {"channel": "1", "tariff": "2"}


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

        obis_rssi = OBIS(0, 0, 96, 99, 0)
        assert obis_rssi.decode() == OBISMeasurement(
            code=obis_rssi,
            canonical="0-0:96.99.0",
            slug="rssi",
            name="RSSI",
            unit="dBm",
            device_class="signal_strength",
            state_class="measurement",
            icon="mdi:signal",
            suggested_display_precision=0,
            placeholders={},
            info=obis_rssi.info,
        )

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

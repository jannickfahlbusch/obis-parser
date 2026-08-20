"""Tests for OBIS.decode() and OBIS naming methods."""

from obis_parser import OBIS


class TestOBISDecode:
    def test_decode_basic_code(self) -> None:
        obis = OBIS.parse("1-0:1.8.0")
        assert obis is not None
        m = obis.decode()
        assert m.canonical == "1-0:1.8.0"
        assert m.slug == "active_energy_import"
        assert m.translation_key == "active_energy_import"
        assert m.name == "Active energy import"
        assert m.unit == "kWh"
        assert m.device_class == "energy"
        assert m.state_class == "total_increasing"
        assert m.placeholders == {}
        assert m.info is not None

    def test_decode_with_channel(self) -> None:
        obis = OBIS.parse("1-1:1.7.0")
        assert obis is not None
        m = obis.decode()
        assert m.canonical == "1-1:1.7.0"
        assert m.slug == "active_power_import_channel"
        assert m.name == "Active power import (Channel 1)"
        assert m.placeholders == {"channel": "1"}

    def test_decode_with_tariff(self) -> None:
        obis = OBIS.parse("1-0:1.8.2")
        assert obis is not None
        m = obis.decode()
        assert m.canonical == "1-0:1.8.2"
        assert m.slug == "active_energy_import_tariff"
        assert m.name == "Active energy import (Tariff 2)"
        assert m.placeholders == {"tariff": "2"}

    def test_decode_with_channel_and_tariff(self) -> None:
        obis = OBIS.parse("1-3:1.8.4")
        assert obis is not None
        m = obis.decode()
        assert m.canonical == "1-3:1.8.4"
        assert m.slug == "active_energy_import_channel_tariff"
        assert m.name == "Active energy import (Channel 3, Tariff 4)"
        assert m.placeholders == {"channel": "3", "tariff": "4"}

    def test_decode_direct_instance(self) -> None:
        obis = OBIS(1, 0, 16, 7, 0)
        m = obis.decode()
        assert m.canonical == "1-0:16.7.0"
        assert m.slug == "active_power_total"

    def test_decode_phase_angles(self) -> None:
        obis = OBIS.parse("1-0:81.7.4")
        assert obis is not None
        m = obis.decode()
        assert (m.slug, m.name, m.unit, m.icon) == ("phase_angle_l1", "Phase angle L1", "°", "mdi:angle-acute")

    def test_decode_phase_angle_with_channel(self) -> None:
        obis = OBIS.parse("1-1:81.7.4")
        assert obis is not None
        m = obis.decode()
        assert (m.slug, m.name, m.placeholders) == (
            "phase_angle_l1_channel",
            "Phase angle L1 (Channel 1)",
            {"channel": "1"},
        )

    def test_decode_device_metadata(self) -> None:
        obis_fw = OBIS.parse("1-0:0.2.0")
        assert obis_fw is not None
        m_fw = obis_fw.decode()
        assert (m_fw.slug, m_fw.name, m_fw.icon) == ("firmware_version", "Firmware version", "mdi:chip")

        obis_id = OBIS.parse("1-0:96.1.0")
        assert obis_id is not None
        m_id = obis_id.decode()
        assert (m_id.slug, m_id.name, m_id.icon) == ("meter_identification", "Meter identification", "mdi:identifier")

    def test_decode_unknown_code(self) -> None:
        obis = OBIS.parse("1-0:99.99.99")
        assert obis is not None
        m = obis.decode()
        assert m.canonical == "1-0:99.99.99"
        assert m.slug == "unknown_code"
        assert m.name == "OBIS 1-0:99.99.99"
        assert m.placeholders == {"code": "1-0:99.99.99"}
        assert m.info is None
        assert m.unit is None


class TestOBISNaming:
    def test_describe_and_properties(self) -> None:
        obis = OBIS.parse("1-2:1.8.5")
        assert obis is not None

        # Object properties
        assert obis.name == "Active energy import (Channel 2, Tariff 5)"
        assert obis.slug == "active_energy_import_channel_tariff"
        assert obis.translation_key == "active_energy_import_channel_tariff"
        assert obis.placeholders == {"channel": "2", "tariff": "5"}

        # describe() method
        d = obis.describe()
        assert d.slug == "active_energy_import_channel_tariff"
        assert d.translation_key == "active_energy_import_channel_tariff"
        assert d.placeholders == {"channel": "2", "tariff": "5"}
        assert d.fallback_name == "Active energy import (Channel 2, Tariff 5)"

    def test_name_property_simple(self) -> None:
        obis = OBIS.parse("1-0:32.7.0")
        assert obis is not None
        assert obis.name == "Voltage L1"
        assert obis.slug == "voltage_l1"

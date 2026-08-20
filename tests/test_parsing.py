"""Tests for OBIS code parsing and normalization."""

import pytest

from obis_parser import (
    OBIS,
    ParsedOBIS,
)


class TestParseObis:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("1-0:1.8.0", OBIS(1, 0, 1, 8, 0, None)),
            ("1-0:1.8.0*255", OBIS(1, 0, 1, 8, 0, 255)),
            ("1-1:16.7.0", OBIS(1, 1, 16, 7, 0, None)),
            ("1-0:1.8.1", OBIS(1, 0, 1, 8, 1, None)),
            ("1-2:1.8.3", OBIS(1, 2, 1, 8, 3, None)),
            ("01.00.01.08.00.ff", OBIS(1, 0, 1, 8, 0, 255)),
            ("01.00.01.08.00.FF", OBIS(1, 0, 1, 8, 0, 255)),
            ("0100010800ff", OBIS(1, 0, 1, 8, 0, 255)),
            ("010001080000", OBIS(1, 0, 1, 8, 0, 0)),
            # Logical name with meter suffix
            ("0100010800ff.1test000000001.sm", OBIS(1, 0, 1, 8, 0, 255)),
            ("0100200700ff.1lgz0067285558.sm", OBIS(1, 0, 32, 7, 0, 255)),
            # Shorthand 3-group notation (defaults to electricity A=1, channel B=0)
            ("1.8.0", OBIS(1, 0, 1, 8, 0, None)),
            ("1.8.0*255", OBIS(1, 0, 1, 8, 0, 255)),
            ("16.7.0", OBIS(1, 0, 16, 7, 0, None)),
            ("81.7.4", OBIS(1, 0, 81, 7, 4, None)),
            ("0.2.0", OBIS(1, 0, 0, 2, 0, None)),
            ("96.1.0", OBIS(1, 0, 96, 1, 0, None)),
            (" 1.8.0 ", OBIS(1, 0, 1, 8, 0, None)),
            ("1.8.0 * 255", OBIS(1, 0, 1, 8, 0, 255)),
            # Spaces
            (" 1-0:1.8.0 ", OBIS(1, 0, 1, 8, 0, None)),
            ("1-0:1.8.0 * 255", OBIS(1, 0, 1, 8, 0, 255)),
        ],
    )
    def test_valid_forms(self, raw: str, expected: OBIS) -> None:
        assert OBIS.parse(raw) == expected
        assert OBIS.from_string(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "   ",
            "not-an-obis-code",
            "1-0:1.8",
            "0100010800",
            "zzgg00010800ff",
        ],
    )
    def test_invalid_returns_none(self, raw: str) -> None:
        assert OBIS.parse(raw) is None
        assert OBIS.from_string(raw) is None

    def test_backwards_compat_alias(self) -> None:
        assert ParsedOBIS is OBIS


class TestOBISProperties:
    def test_string_representations(self) -> None:
        obis = OBIS(1, 0, 1, 8, 0, None)
        assert str(obis) == "1-0:1.8.0"
        assert obis.canonical == "1-0:1.8.0"
        assert obis.to_obis_string() == "1-0:1.8.0"

    def test_f_suppression(self) -> None:
        assert str(OBIS(1, 0, 1, 8, 0, 255)) == "1-0:1.8.0"
        assert str(OBIS(1, 0, 1, 8, 0, 0)) == "1-0:1.8.0"
        assert str(OBIS(1, 0, 1, 8, 0, 1)) == "1-0:1.8.0*1"

    def test_convenience_properties(self) -> None:
        obis = OBIS(1, 2, 1, 8, 3, 255)
        assert obis.is_electricity is True
        assert obis.medium == 1
        assert obis.channel == 2
        assert obis.physical_quantity == 1
        assert obis.measurement_type == 8
        assert obis.tariff == 3
        assert obis.billing_period == 255
        assert obis.info is not None

    def test_non_electricity(self) -> None:
        obis = OBIS(7, 0, 3, 0, 0, None)
        assert obis.is_electricity is False
        assert obis.medium == 7

    @pytest.mark.parametrize(
        "raw",
        [
            "1-0:1.8.0",
            " 1-0:1.8.0*255 ",
            "0100010800ff",
            "010001080000",
            "01.00.01.08.00.FF",
            "0100010800ff.meter.sm",
        ],
    )
    def test_canonical_property_on_parsed_forms(self, raw: str) -> None:
        obis = OBIS.parse(raw)
        assert obis is not None
        assert obis.canonical == "1-0:1.8.0"

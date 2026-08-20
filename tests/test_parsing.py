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
            # Canonical standard notations
            ("1-0:1.8.0", OBIS(1, 0, 1, 8, 0, None)),
            ("1-0:1.8.0*255", OBIS(1, 0, 1, 8, 0, 255)),
            ("1-0:1.8.0*0", OBIS(1, 0, 1, 8, 0, 0)),
            ("1-0:1.8.0*1", OBIS(1, 0, 1, 8, 0, 1)),
            ("1-1:16.7.0", OBIS(1, 1, 16, 7, 0, None)),
            ("1-0:1.8.1", OBIS(1, 0, 1, 8, 1, None)),
            ("1-2:1.8.3", OBIS(1, 2, 1, 8, 3, None)),
            ("1-12:1.8.128*50", OBIS(1, 12, 1, 8, 128, 50)),
            # Shorthand 3-group notation (defaults to A=1, B=0)
            ("1.8.0", OBIS(1, 0, 1, 8, 0, None)),
            ("1.8.0*255", OBIS(1, 0, 1, 8, 0, 255)),
            ("1.8.0*0", OBIS(1, 0, 1, 8, 0, 0)),
            ("1.8.0*1", OBIS(1, 0, 1, 8, 0, 1)),
            ("1.8.1", OBIS(1, 0, 1, 8, 1, None)),
            ("1.8.2", OBIS(1, 0, 1, 8, 2, None)),
            ("16.7.0", OBIS(1, 0, 16, 7, 0, None)),
            ("81.7.0", OBIS(1, 0, 81, 7, 0, None)),
            ("81.7.1", OBIS(1, 0, 81, 7, 1, None)),
            ("81.7.4", OBIS(1, 0, 81, 7, 4, None)),
            ("81.7.15", OBIS(1, 0, 81, 7, 15, None)),
            ("81.7.26", OBIS(1, 0, 81, 7, 26, None)),
            ("0.2.0", OBIS(1, 0, 0, 2, 0, None)),
            ("96.1.0", OBIS(1, 0, 96, 1, 0, None)),
            # Dot-separated hex
            ("01.00.01.08.00.ff", OBIS(1, 0, 1, 8, 0, 255)),
            ("01.00.01.08.00.FF", OBIS(1, 0, 1, 8, 0, 255)),
            ("01.01.10.07.00.00", OBIS(1, 1, 16, 7, 0, 0)),
            # Bare 12-char COSEM hex
            ("0100010800ff", OBIS(1, 0, 1, 8, 0, 255)),
            ("0100010800FF", OBIS(1, 0, 1, 8, 0, 255)),
            ("010001080000", OBIS(1, 0, 1, 8, 0, 0)),
            ("010051070fff", OBIS(1, 0, 81, 7, 15, 255)),
            ("010051071aff", OBIS(1, 0, 81, 7, 26, 255)),
            # Logical name with meter suffix
            ("0100010800ff.1test000000001.sm", OBIS(1, 0, 1, 8, 0, 255)),
            ("0100200700ff.1lgz0067285558.sm", OBIS(1, 0, 32, 7, 0, 255)),
            # Whitespace handling
            (" 1-0:1.8.0 ", OBIS(1, 0, 1, 8, 0, None)),
            ("1-0:1.8.0 * 255", OBIS(1, 0, 1, 8, 0, 255)),
            ("1 - 0 : 1 . 8 . 0", OBIS(1, 0, 1, 8, 0, None)),
            (" 1.8.0 ", OBIS(1, 0, 1, 8, 0, None)),
            ("1.8.0 * 255", OBIS(1, 0, 1, 8, 0, 255)),
            ("1 . 8 . 0", OBIS(1, 0, 1, 8, 0, None)),
            ("\t1.8.0\n", OBIS(1, 0, 1, 8, 0, None)),
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
            "1-0:1.8.0.0",
            "1-0:1.8.0*",
            "1-0:1.8.0*abc",
            "1-0:1.8.0*1*2",
            "1.8",
            "1.8.0.0",
            "1.8.0*",
            "1.8.0*abc",
            "1.8.0*1*2",
            "-1.8.0",
            "1.-8.0",
            "1.8.-0",
            ".1.8.0",
            "1.8.0.",
            "1:8:0",
            "0100010800",
            "0100010800ff11",
            "0100010800gg",
            "zzgg00010800ff",
            "01.00.01.08.00",
            "01.00.01.08.00.00.00",
            "01.00.01.08.00.gg",
            "0100010800.meter.sm",
        ],
    )
    def test_invalid_returns_none(self, raw: str) -> None:
        assert OBIS.parse(raw) is None
        assert OBIS.from_string(raw) is None

    def test_backwards_compat_alias(self) -> None:
        assert ParsedOBIS is OBIS


class TestOBISProperties:
    @pytest.mark.parametrize(
        ("obis", "expected_str"),
        [
            (OBIS(1, 0, 1, 8, 0, None), "1-0:1.8.0"),
            (OBIS(1, 1, 16, 7, 0, None), "1-1:16.7.0"),
            (OBIS(1, 0, 81, 7, 4, None), "1-0:81.7.4"),
        ],
    )
    def test_string_representations(self, obis: OBIS, expected_str: str) -> None:
        assert str(obis) == expected_str
        assert obis.canonical == expected_str
        assert obis.to_obis_string() == expected_str

    @pytest.mark.parametrize(
        ("obis", "expected_str"),
        [
            (OBIS(1, 0, 1, 8, 0, 255), "1-0:1.8.0"),
            (OBIS(1, 0, 1, 8, 0, 0), "1-0:1.8.0"),
            (OBIS(1, 0, 1, 8, 0, 1), "1-0:1.8.0*1"),
            (OBIS(1, 0, 81, 7, 4, 1), "1-0:81.7.4*1"),
        ],
    )
    def test_f_suppression(self, obis: OBIS, expected_str: str) -> None:
        assert str(obis) == expected_str

    @pytest.mark.parametrize(
        ("obis", "expected_props"),
        [
            (OBIS(1, 2, 1, 8, 3, 255), (True, 1, 2, 1, 8, 3, 255)),
            (OBIS(7, 0, 3, 0, 0, None), (False, 7, 0, 3, 0, 0, None)),
            (OBIS(1, 0, 81, 7, 4, 1), (True, 1, 0, 81, 7, 4, 1)),
        ],
    )
    def test_convenience_properties(
        self,
        obis: OBIS,
        expected_props: tuple[bool, int, int, int, int, int, int | None],
    ) -> None:
        assert (
            obis.is_electricity,
            obis.medium,
            obis.channel,
            obis.physical_quantity,
            obis.measurement_type,
            obis.tariff,
            obis.billing_period,
        ) == expected_props

    @pytest.mark.parametrize(
        ("raw", "expected_canonical"),
        [
            ("1-0:1.8.0", "1-0:1.8.0"),
            ("1.8.0", "1-0:1.8.0"),
            ("1.8.0*255", "1-0:1.8.0"),
            ("1.8.0*0", "1-0:1.8.0"),
            ("1.8.0*1", "1-0:1.8.0*1"),
            ("1.8.2", "1-0:1.8.2"),
            ("81.7.4", "1-0:81.7.4"),
            (" 1-0:1.8.0*255 ", "1-0:1.8.0"),
            ("0100010800ff", "1-0:1.8.0"),
            ("010001080000", "1-0:1.8.0"),
            ("01.00.01.08.00.FF", "1-0:1.8.0"),
            ("0100010800ff.meter.sm", "1-0:1.8.0"),
            ("1-1:1.8.2", "1-1:1.8.2"),
        ],
    )
    def test_canonical_property_on_parsed_forms(self, raw: str, expected_canonical: str) -> None:
        obis = OBIS.parse(raw)
        assert obis is not None
        assert obis.canonical == expected_canonical

    def test_obis_dataclass_immutability_and_hashability(self) -> None:
        """OBIS is a frozen dataclass and can be hashed/stored in sets."""
        obis1 = OBIS(1, 0, 1, 8, 0)
        obis2 = OBIS(1, 0, 1, 8, 0)
        assert obis1 == obis2
        assert hash(obis1) == hash(obis2)
        assert len({obis1, obis2}) == 1

        with pytest.raises(AttributeError):
            obis1.a = 2  # type: ignore[misc]

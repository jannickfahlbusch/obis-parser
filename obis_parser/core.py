"""OBIS code parsing and measurement catalog for smart meters and energy gateways.

This module is dependency-free (standard library only) and provides:
- Object-oriented `OBIS` domain class with `OBIS.parse()`, canonicalization, and metadata.
- Full catalog of 31 German smart meter electricity registers (IEC 62056-6-1 / DIN 43863-3).
- Resolved measurement metadata via `obis.decode()` with 4-variant localization slugs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from string import hexdigits
from typing import Literal

_HEXDIGITS = set(hexdigits)
_OBIS_STRING_RE = re.compile(r"^(\d+)\s*-\s*(\d+)\s*:\s*(\d+)\s*\.\s*(\d+)\s*\.\s*(\d+)(?:\s*\*\s*(\d+))?$")
_OBIS_DOT_HEX_RE = re.compile(
    r"^([0-9a-fA-F]{2})\.([0-9a-fA-F]{2})\.([0-9a-fA-F]{2})\."
    r"([0-9a-fA-F]{2})\.([0-9a-fA-F]{2})\.([0-9a-fA-F]{2})$"
)

#: Group A: Abstract medium (1 = Electricity, 7 = Gas, 4 = Heat, etc.)
type OBISMedium = int

#: Group B: Channel / sub-device index (0 = No channel / default)
type OBISChannel = int

#: Group C: Physical quantity (1 = Active power import, 2 = Active power export, etc.)
type OBISPhysicalQuantity = int

#: Group D: Measurement algorithm (8 = Energy register, 7 = Instantaneous power, etc.)
type OBISMeasurementType = int

#: Group E: Tariff rate register (0 = Total / unspecified, 1 = Tariff 1, etc.)
type OBISTariff = int

#: Group F: Billing period history (255 or 0 = Current period, 1..254 = Historic cycles)
type OBISBillingPeriod = int

type OBISDeviceClass = Literal[
    "current",
    "energy",
    "power",
    "voltage",
    "reactive_energy",
    "reactive_power",
    "apparent_power",
    "power_factor",
    "frequency",
]
type OBISStateClass = Literal["measurement", "total_increasing"]

#: Medium code for electricity in the OBIS A field.
ELECTRICITY_MEDIUM = 1

#: F (billing period) values meaning "current period": absent, 0, or 255.
_CURRENT_PERIOD_F = (0, 255)

#: A measurement's identity: the (C, D) OBIS value groups — C is the physical
#: quantity, D the measurement/processing type (IEC 62056-6-1). The channel (B)
#: and tariff (E) fields are qualifiers and are NOT part of this key.
type MeasurementKey = tuple[OBISPhysicalQuantity, OBISMeasurementType]


@dataclass(frozen=True)
class OBIS:
    """A structured representation of an OBIS code (A-B:C.D.E*F)."""

    a: OBISMedium
    b: OBISChannel
    c: OBISPhysicalQuantity
    d: OBISMeasurementType
    e: OBISTariff
    f: OBISBillingPeriod | None = None

    @classmethod
    def parse(cls, code: str) -> OBIS | None:
        """Parse an OBIS code from string, COSEM hex, dot-separated hex, or logical name."""
        code = code.strip()
        if not code:
            return None

        # Handle COSEM logical names with meter suffixes (e.g. '0100010800ff.1test000000001.sm')
        if "." in code and len(code.split(".", 1)[0]) == 12:
            prefix = code.split(".", 1)[0]
            if all(char in _HEXDIGITS for char in prefix):
                code = prefix

        if match := _OBIS_STRING_RE.match(code):
            return cls(
                a=int(match.group(1)),
                b=int(match.group(2)),
                c=int(match.group(3)),
                d=int(match.group(4)),
                e=int(match.group(5)),
                f=int(match.group(6)) if match.group(6) is not None else None,
            )

        if match := _OBIS_DOT_HEX_RE.match(code):
            return cls(
                a=int(match.group(1), 16),
                b=int(match.group(2), 16),
                c=int(match.group(3), 16),
                d=int(match.group(4), 16),
                e=int(match.group(5), 16),
                f=int(match.group(6), 16),
            )

        if len(code) == 12 and all(char in _HEXDIGITS for char in code):
            return cls(
                a=int(code[0:2], 16),
                b=int(code[2:4], 16),
                c=int(code[4:6], 16),
                d=int(code[6:8], 16),
                e=int(code[8:10], 16),
                f=int(code[10:12], 16),
            )

        return None

    @classmethod
    def from_string(cls, code: str) -> OBIS | None:
        """Alias for `OBIS.parse()`."""
        return cls.parse(code)

    def __str__(self) -> str:
        """Return the canonical OBIS string."""
        return self.to_obis_string()

    def to_obis_string(self) -> str:
        """Return the canonical OBIS string used for entity keys."""
        base = f"{self.a}-{self.b}:{self.c}.{self.d}.{self.e}"
        if self.f is not None and self.f not in _CURRENT_PERIOD_F:
            base += f"*{self.f}"
        return base

    @property
    def canonical(self) -> str:
        """Canonical OBIS string representation."""
        return self.to_obis_string()

    @property
    def medium(self) -> OBISMedium:
        """Abstract medium code (Group A)."""
        return self.a

    @property
    def channel(self) -> OBISChannel:
        """Channel / sub-device index (Group B)."""
        return self.b

    @property
    def physical_quantity(self) -> OBISPhysicalQuantity:
        """Physical quantity identifier (Group C)."""
        return self.c

    @property
    def measurement_type(self) -> OBISMeasurementType:
        """Measurement algorithm / processing type (Group D)."""
        return self.d

    @property
    def tariff(self) -> OBISTariff:
        """Tariff rate register (Group E)."""
        return self.e

    @property
    def billing_period(self) -> OBISBillingPeriod | None:
        """Billing period history index (Group F)."""
        return self.f

    @property
    def is_electricity(self) -> bool:
        """Return True if the code addresses the electricity medium (A=1)."""
        return self.a == ELECTRICITY_MEDIUM

    @property
    def info(self) -> OBISMeasurementInfo | None:
        """Look up catalog metadata for this code's (C, D) measurement."""
        return _get_obis_info(self)

    @property
    def name(self) -> str:
        """English display name with channel/tariff qualifiers."""
        return self.describe().fallback_name

    @property
    def slug(self) -> str:
        """Localization slug with channel/tariff variant suffix."""
        return self.describe().slug

    @property
    def translation_key(self) -> str:
        """Alias for slug (Home Assistant translation compatibility)."""
        return self.slug

    @property
    def placeholders(self) -> dict[str, str]:
        """Channel and tariff placeholder mapping."""
        return self.describe().placeholders

    def describe(self) -> OBISNameDescriptor:
        """Resolve slug variant, placeholders, and English fallback name."""
        return _describe_obis(self, self.info)

    def decode(self) -> OBISMeasurement:
        """Decode into a fully-resolved OBISMeasurement object."""
        return _build_measurement(self, self.info)


#: Backwards-compatibility alias for OBIS.
ParsedOBIS = OBIS


@dataclass(frozen=True)
class OBISMeasurementInfo:
    """Catalog metadata for a base (C, D) measurement."""

    name: str
    slug: str
    device_class: OBISDeviceClass | None
    state_class: OBISStateClass | None
    unit: str | None
    icon: str
    suggested_display_precision: int | None = None

    @property
    def translation_key(self) -> str:
        """Alias for slug (Home Assistant translation compatibility)."""
        return self.slug


@dataclass(frozen=True)
class OBISNameDescriptor:
    """Resolved naming descriptors for an OBIS code."""

    slug: str
    placeholders: dict[str, str] = field(default_factory=dict)
    fallback_name: str = ""

    @property
    def translation_key(self) -> str:
        """Alias for slug (Home Assistant translation compatibility)."""
        return self.slug


@dataclass(frozen=True)
class OBISMeasurement:
    """A fully-resolved OBIS measurement with values, units, and localized metadata."""

    code: OBIS
    canonical: str
    slug: str
    name: str
    unit: str | None
    device_class: OBISDeviceClass | None
    state_class: OBISStateClass | None
    icon: str
    suggested_display_precision: int | None
    placeholders: dict[str, str] = field(default_factory=dict)
    info: OBISMeasurementInfo | None = None

    @property
    def translation_key(self) -> str:
        """Alias for slug (Home Assistant translation compatibility)."""
        return self.slug


OBIS_CATALOG: dict[MeasurementKey, OBISMeasurementInfo] = {
    # Active energy (time-integral, D=8)
    (1, 8): OBISMeasurementInfo(
        "Active energy import",
        "active_energy_import",
        "energy",
        "total_increasing",
        "kWh",
        "mdi:home-import-outline",
        5,
    ),
    (2, 8): OBISMeasurementInfo(
        "Active energy export",
        "active_energy_export",
        "energy",
        "total_increasing",
        "kWh",
        "mdi:home-export-outline",
        5,
    ),
    # Reactive energy
    (3, 8): OBISMeasurementInfo(
        "Reactive energy import",
        "reactive_energy_import",
        "reactive_energy",
        "total_increasing",
        "kvarh",
        "mdi:home-import-outline",
        5,
    ),
    (4, 8): OBISMeasurementInfo(
        "Reactive energy export",
        "reactive_energy_export",
        "reactive_energy",
        "total_increasing",
        "kvarh",
        "mdi:home-export-outline",
        5,
    ),
    # Apparent energy (no standard HA device class / unit constant exists)
    (9, 8): OBISMeasurementInfo(
        "Apparent energy",
        "apparent_energy",
        None,
        "total_increasing",
        "kVAh",
        "mdi:flash",
        5,
    ),
    # Active power (instantaneous, D=7)
    (1, 7): OBISMeasurementInfo(
        "Active power import",
        "active_power_import",
        "power",
        "measurement",
        "W",
        "mdi:flash",
        1,
    ),
    (2, 7): OBISMeasurementInfo(
        "Active power export",
        "active_power_export",
        "power",
        "measurement",
        "W",
        "mdi:flash-outline",
        1,
    ),
    # Reactive power
    (3, 7): OBISMeasurementInfo(
        "Reactive power import",
        "reactive_power_import",
        "reactive_power",
        "measurement",
        "var",
        "mdi:flash",
        1,
    ),
    (4, 7): OBISMeasurementInfo(
        "Reactive power export",
        "reactive_power_export",
        "reactive_power",
        "measurement",
        "var",
        "mdi:flash-outline",
        1,
    ),
    # Apparent power
    (9, 7): OBISMeasurementInfo(
        "Apparent power",
        "apparent_power",
        "apparent_power",
        "measurement",
        "VA",
        "mdi:flash",
        1,
    ),
    # Active power total + absolute
    (16, 7): OBISMeasurementInfo(
        "Active power total",
        "active_power_total",
        "power",
        "measurement",
        "W",
        "mdi:flash",
        1,
    ),
    (15, 7): OBISMeasurementInfo(
        "Absolute active power",
        "absolute_active_power",
        "power",
        "measurement",
        "W",
        "mdi:flash",
        1,
    ),
    # Active power per phase (signed vector sum)
    (36, 7): OBISMeasurementInfo(
        "Active power L1",
        "active_power_l1",
        "power",
        "measurement",
        "W",
        "mdi:flash",
        1,
    ),
    (56, 7): OBISMeasurementInfo(
        "Active power L2",
        "active_power_l2",
        "power",
        "measurement",
        "W",
        "mdi:flash",
        1,
    ),
    (76, 7): OBISMeasurementInfo(
        "Active power L3",
        "active_power_l3",
        "power",
        "measurement",
        "W",
        "mdi:flash",
        1,
    ),
    # Active power per phase, import (+P)
    (21, 7): OBISMeasurementInfo(
        "Active power import L1",
        "active_power_import_l1",
        "power",
        "measurement",
        "W",
        "mdi:flash",
        1,
    ),
    (41, 7): OBISMeasurementInfo(
        "Active power import L2",
        "active_power_import_l2",
        "power",
        "measurement",
        "W",
        "mdi:flash",
        1,
    ),
    (61, 7): OBISMeasurementInfo(
        "Active power import L3",
        "active_power_import_l3",
        "power",
        "measurement",
        "W",
        "mdi:flash",
        1,
    ),
    # Active power per phase, export (-P)
    (22, 7): OBISMeasurementInfo(
        "Active power export L1",
        "active_power_export_l1",
        "power",
        "measurement",
        "W",
        "mdi:flash-outline",
        1,
    ),
    (42, 7): OBISMeasurementInfo(
        "Active power export L2",
        "active_power_export_l2",
        "power",
        "measurement",
        "W",
        "mdi:flash-outline",
        1,
    ),
    (62, 7): OBISMeasurementInfo(
        "Active power export L3",
        "active_power_export_l3",
        "power",
        "measurement",
        "W",
        "mdi:flash-outline",
        1,
    ),
    # Voltage per phase + total
    (32, 7): OBISMeasurementInfo("Voltage L1", "voltage_l1", "voltage", "measurement", "V", "mdi:sine-wave", 1),
    (52, 7): OBISMeasurementInfo("Voltage L2", "voltage_l2", "voltage", "measurement", "V", "mdi:sine-wave", 1),
    (72, 7): OBISMeasurementInfo("Voltage L3", "voltage_l3", "voltage", "measurement", "V", "mdi:sine-wave", 1),
    (12, 7): OBISMeasurementInfo("Voltage", "voltage", "voltage", "measurement", "V", "mdi:sine-wave", 1),
    # Current per phase + total
    (31, 7): OBISMeasurementInfo("Current L1", "current_l1", "current", "measurement", "A", "mdi:current-ac", 2),
    (51, 7): OBISMeasurementInfo("Current L2", "current_l2", "current", "measurement", "A", "mdi:current-ac", 2),
    (71, 7): OBISMeasurementInfo("Current L3", "current_l3", "current", "measurement", "A", "mdi:current-ac", 2),
    (11, 7): OBISMeasurementInfo("Current", "current", "current", "measurement", "A", "mdi:current-ac", 2),
    # Power factor + frequency
    (13, 7): OBISMeasurementInfo(
        "Power factor",
        "power_factor",
        "power_factor",
        "measurement",
        None,
        "mdi:angle-acute",
        2,
    ),
    (14, 7): OBISMeasurementInfo("Frequency", "frequency", "frequency", "measurement", "Hz", "mdi:sine-wave", 2),
}


def _get_obis_info(obis: OBIS) -> OBISMeasurementInfo | None:
    """Look up measurement metadata from the catalog by (C, D)."""
    if not obis.is_electricity:
        return None

    if obis.f is not None and obis.f not in _CURRENT_PERIOD_F:
        return None

    return OBIS_CATALOG.get((obis.c, obis.d))


def _has_tariff(e: int) -> bool:
    """A tariff register is any E in 1..254; 0 and 255 mean total/unspecified."""
    return 1 <= e < 255


def _describe_obis(obis: OBIS, info: OBISMeasurementInfo | None) -> OBISNameDescriptor:
    """Resolve slug variant, placeholders, and fallback name for an OBIS code."""
    if info is None:
        canonical = obis.to_obis_string()
        return OBISNameDescriptor(
            slug="unknown_code",
            placeholders={"code": canonical},
            fallback_name=f"OBIS {canonical}",
        )

    has_channel = obis.b != 0
    has_tariff = _has_tariff(obis.e)

    placeholders: dict[str, str] = {}
    fallback = info.name
    if has_channel and has_tariff:
        suffix = "_channel_tariff"
        placeholders = {"channel": str(obis.b), "tariff": str(obis.e)}
        fallback = f"{info.name} (Channel {obis.b}, Tariff {obis.e})"
    elif has_channel:
        suffix = "_channel"
        placeholders = {"channel": str(obis.b)}
        fallback = f"{info.name} (Channel {obis.b})"
    elif has_tariff:
        suffix = "_tariff"
        placeholders = {"tariff": str(obis.e)}
        fallback = f"{info.name} (Tariff {obis.e})"
    else:
        suffix = ""

    return OBISNameDescriptor(
        slug=f"{info.slug}{suffix}",
        placeholders=placeholders,
        fallback_name=fallback,
    )


def _build_measurement(obis: OBIS, info: OBISMeasurementInfo | None) -> OBISMeasurement:
    """Assemble a complete OBISMeasurement object from parsed code and catalog info."""
    descriptor = _describe_obis(obis, info)
    canonical = obis.to_obis_string()

    if info is None:
        return OBISMeasurement(
            code=obis,
            canonical=canonical,
            slug=descriptor.slug,
            name=descriptor.fallback_name,
            unit=None,
            device_class=None,
            state_class=None,
            icon="mdi:gauge",
            suggested_display_precision=None,
            placeholders=descriptor.placeholders,
            info=None,
        )

    return OBISMeasurement(
        code=obis,
        canonical=canonical,
        slug=descriptor.slug,
        name=descriptor.fallback_name,
        unit=info.unit,
        device_class=info.device_class,
        state_class=info.state_class,
        icon=info.icon,
        suggested_display_precision=info.suggested_display_precision,
        placeholders=descriptor.placeholders,
        info=info,
    )

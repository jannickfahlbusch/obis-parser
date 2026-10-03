"""Dependency-free OBIS parser and measurement catalog for smart meters and energy gateways.

Usage examples:
    >>> from obis_parser import OBIS
    >>>
    >>> # 1. Parse and access properties
    >>> obis = OBIS.parse("0100010800ff")
    >>> obis.canonical
    '1-0:1.8.0'
    >>> obis.name
    'Active energy import'
    >>> obis.slug
    'active_energy_import'
    >>>
    >>> # 2. Multi-meter channels and dynamic tariffs
    >>> obis = OBIS.parse("1-1:1.8.2")
    >>> obis.name
    'Active energy import (Channel 1, Tariff 2)'
    >>> obis.slug
    'active_energy_import_channel_tariff'
    >>> obis.placeholders
    {'channel': '1', 'tariff': '2'}
    >>>
    >>> # 3. Full metadata decode
    >>> m = obis.decode()
    >>> m.unit
    'kWh'
    >>> m.device_class
    'energy'
"""

from ._version import __version__, __version_tuple__
from .core import (
    ABSTRACT_OBJECTS,
    ELECTRICITY_MEDIUM,
    OBIS,
    OBIS_CATALOG,
    MeasurementKey,
    OBISBillingPeriod,
    OBISChannel,
    OBISDeviceClass,
    OBISMeasurement,
    OBISMeasurementInfo,
    OBISMeasurementType,
    OBISMedium,
    OBISNameDescriptor,
    OBISPhysicalQuantity,
    OBISStateClass,
    OBISTariff,
    ParsedOBIS,
)

__all__ = [
    "ABSTRACT_OBJECTS",
    "ELECTRICITY_MEDIUM",
    "OBIS",
    "OBIS_CATALOG",
    "MeasurementKey",
    "OBISBillingPeriod",
    "OBISChannel",
    "OBISDeviceClass",
    "OBISMeasurement",
    "OBISMeasurementInfo",
    "OBISMeasurementType",
    "OBISMedium",
    "OBISNameDescriptor",
    "OBISPhysicalQuantity",
    "OBISStateClass",
    "OBISTariff",
    "ParsedOBIS",
    "__version__",
    "__version_tuple__",
]

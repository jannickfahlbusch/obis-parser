# obis-parser

[![PyPI version](https://img.shields.io/pypi/v/obis-parser.svg)](https://pypi.org/project/obis-parser/)
[![Python versions](https://img.shields.io/pypi/pyversions/obis-parser.svg)](https://pypi.org/project/obis-parser/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

**Dependency-free OBIS parser and measurement catalog for smart meters and energy gateways**.

Extracts, parses, and normalizes OBIS (*Object Identification System*) codes (`A-B:C.D.E*F`) across smart meters (eHZ / mME), optical IR readouts (SML / IEC 62056-21), P1/DSMR meters, and Smart Meter Gateways (SMGW).

---

## Features

* **Zero External Dependencies:** Built entirely with standard library Python (`dataclasses`, `re`, `string`, `typing`).
* **Universal Ingestion:** Auto-detects and parses:
  * Canonical strings: `1-0:1.8.0`, `1-0:1.8.0*255`, `1-1:1.7.0`
  * Bare COSEM 12-hex: `0100010800ff`, `0100100700ff`, `010001080000` (F=0)
  * COSEM logical names with meter suffixes: `0100010800ff.1lgz0067285558.sm`
  * Dot-separated hex: `01.00.01.08.00.FF`
* **Single Domain Model (`OBIS`):** Everything is accessed directly on the `OBIS` instance (`.canonical`, `.name`, `.slug`, `.placeholders`, `.decode()`).
* **Channel & Tariff Qualifiers:** Treats Channel ($B \neq 0$) and Tariff ($1 \le E < 255$) as name qualifiers on $(C, D)$ base measurements.
* **4-Variant Localization Slugs:** Generates variant slugs (`base`, `_channel`, `_tariff`, `_channel_tariff`) with placeholder maps, ready for Home Assistant, Prometheus, or UI localization.
* **Curated Catalog:** 31 standard German electricity registers (DIN EN 62056-6-1 / DIN 43863-3) with units, device classes, state classes, and icons.

---

## Installation

```bash
pip install obis-parser
```

or with [uv](https://github.com/astral-sh/uv):

```bash
uv add obis-parser
```

---

## Quick Start

### 1. Basic Parsing & Properties

```python
from obis_parser import OBIS

# Parses strings, bare-hex, dot-hex, or COSEM logical names
obis = OBIS.parse("0100010800ff")
if obis:
    print(obis.canonical)      # "1-0:1.8.0" (or str(obis))
    print(obis.name)           # "Active energy import"
    print(obis.slug)           # "active_energy_import"
    print(obis.is_electricity) # True
    print(obis.channel)        # 0
    print(obis.tariff)         # 0
```

### 2. Multi-Meter Channels & Tariffs

```python
# Multi-meter behind one gateway (Channel 1, Tariff 2)
obis = OBIS.parse("1-1:1.8.2")
if obis:
    print(obis.canonical)    # "1-1:1.8.2"
    print(obis.name)         # "Active energy import (Channel 1, Tariff 2)"
    print(obis.slug)         # "active_energy_import_channel_tariff"
    print(obis.placeholders) # {"channel": "1", "tariff": "2"}
```

### 3. Full Metadata Decode (`obis.decode()`)

```python
obis = OBIS.parse("0100200700ff")  # Voltage L1 (32.7.0)
if obis:
    m = obis.decode()
    print(m.name)         # "Voltage L1"
    print(m.unit)         # "V"
    print(m.device_class) # "voltage"
    print(m.state_class)  # "measurement"
    print(m.icon)         # "mdi:sine-wave"
```

---

## Supported Registers (Catalog Overview)

| (C, D) | Measurement | Slug | Unit | Device Class | State Class |
|---|---|---|---|---|---|
| **(1, 8)** | Active energy import | `active_energy_import` | `kWh` | `energy` | `total_increasing` |
| **(2, 8)** | Active energy export | `active_energy_export` | `kWh` | `energy` | `total_increasing` |
| **(3, 8)** | Reactive energy import | `reactive_energy_import` | `kvarh` | `reactive_energy` | `total_increasing` |
| **(4, 8)** | Reactive energy export | `reactive_energy_export` | `kvarh` | `reactive_energy` | `total_increasing` |
| **(9, 8)** | Apparent energy | `apparent_energy` | `kVAh` | `None` | `total_increasing` |
| **(1, 7)** | Active power import | `active_power_import` | `W` | `power` | `measurement` |
| **(2, 7)** | Active power export | `active_power_export` | `W` | `power` | `measurement` |
| **(3, 7)** | Reactive power import | `reactive_power_import` | `var` | `reactive_power` | `measurement` |
| **(4, 7)** | Reactive power export | `reactive_power_export` | `var` | `reactive_power` | `measurement` |
| **(9, 7)** | Apparent power | `apparent_power` | `VA` | `apparent_power` | `measurement` |
| **(16, 7)** | Active power total (net sum) | `active_power_total` | `W` | `power` | `measurement` |
| **(15, 7)** | Absolute active power (\|P\|) | `absolute_active_power` | `W` | `power` | `measurement` |
| **(36/56/76, 7)** | Active power L1/L2/L3 (signed) | `active_power_l1..3` | `W` | `power` | `measurement` |
| **(21/41/61, 7)** | Active power import L1/L2/L3 (+P) | `active_power_import_l1..3` | `W` | `power` | `measurement` |
| **(22/42/62, 7)** | Active power export L1/L2/L3 (-P) | `active_power_export_l1..3` | `W` | `power` | `measurement` |
| **(32/52/72, 7)** | Voltage L1/L2/L3 | `voltage_l1..3` | `V` | `voltage` | `measurement` |
| **(12, 7)** | Voltage (total/RMS) | `voltage` | `V` | `voltage` | `measurement` |
| **(31/51/71, 7)** | Current L1/L2/L3 | `current_l1..3` | `A` | `current` | `measurement` |
| **(11, 7)** | Current (neutral/total) | `current` | `A` | `current` | `measurement` |
| **(13, 7)** | Power factor ($\cos \varphi$) | `power_factor` | `None` | `power_factor` | `measurement` |
| **(14, 7)** | Frequency | `frequency` | `Hz` | `frequency` | `measurement` |

---

## License

Apache 2.0. Copyright 2026 Jannick Fahlbusch.

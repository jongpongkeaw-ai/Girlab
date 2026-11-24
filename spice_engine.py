"""ngspice adapter for the Lab 4 CE voltage-divider amplifier.

Pure Python: no Flask imports. Input validation, netlist generation and result
parsing live here; the Flask app only dispatches and displays.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

SIMULATION_MODES = ("dc", "ac", "tran")
MODEL_NAME = "QGEN"
MODEL_LINE = ".model QGEN NPN"

SIM_FIELDS = (
    "vcc",
    "r1",
    "r2",
    "rc",
    "re",
    "rl",
    "cin",
    "cout",
    "amplitude_v",
    "frequency_hz",
    "beta",
    "vbe",
)


@dataclass(frozen=True)
class SimInput:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    rl: float
    cin: float
    cout: float
    amplitude_v: float
    frequency_hz: float
    beta: float
    vbe: float


def parse_sim_input(raw: Mapping[str, str]) -> tuple[SimInput | None, dict[str, str]]:
    """Validate form strings and return a SimInput, or field errors."""
    errors: dict[str, str] = {}
    values: dict[str, float] = {}

    for field in SIM_FIELDS:
        text = str(raw.get(field, "")).strip()
        if not text:
            errors[field] = "Required"
            continue
        try:
            value = float(text)
        except ValueError:
            errors[field] = "Must be a number"
            continue
        if not isfinite(value):
            errors[field] = "Must be a finite number"
            continue
        if value <= 0:
            errors[field] = "Must be greater than zero"
            continue
        values[field] = value

    if "frequency_hz" in values and not 10 <= values["frequency_hz"] <= 1e6:
        errors["frequency_hz"] = "Must be between 10 and 1000000 Hz"

    if "amplitude_v" in values and "vcc" in values:
        if values["amplitude_v"] > values["vcc"]:
            errors["amplitude_v"] = "Must not exceed VCC"

    if "vbe" in values and "vcc" in values and values["vbe"] >= values["vcc"]:
        errors["vbe"] = "Must be less than VCC"

    if errors:
        return None, errors
    return SimInput(**values), {}


def _spice_number(value: float) -> str:
    return f"{value:.6g}"


def build_netlist(data: SimInput, mode: str) -> str:
    """Build a single-analysis SPICE deck from validated values."""
    if mode not in SIMULATION_MODES:
        raise ValueError(f"Unknown analysis mode: {mode}")

    lines = [
        "* CE voltage-divider amplifier v1 - generic NPN, no bypass capacitor",
        f"VCC vcc 0 DC {_spice_number(data.vcc)}",
        f"R1 vcc base {_spice_number(data.r1)}",
        f"R2 base 0 {_spice_number(data.r2)}",
        f"RC vcc collector {_spice_number(data.rc)}",
        f"RE emitter 0 {_spice_number(data.re)}",
        f"Q1 collector base emitter {MODEL_NAME}",
        f"Cin src base {_spice_number(data.cin)}",
        f"Cout collector out {_spice_number(data.cout)}",
        f"RL out 0 {_spice_number(data.rl)}",
        "Vin src 0 SIN(0 "
        + _spice_number(data.amplitude_v)
        + " "
        + _spice_number(data.frequency_hz)
        + ") AC 1",
        MODEL_LINE,
    ]

    if mode == "dc":
        lines.append(".op")
    elif mode == "ac":
        lines.append(".ac dec 40 10 1Meg")
        lines.append(".print ac vdb(out) vp(out)")
    else:
        tstep = 1 / (200 * data.frequency_hz)
        tstop = 5 / data.frequency_hz
        lines.append(f".tran {_spice_number(tstep)} {_spice_number(tstop)}")
        lines.append(".print tran v(src) v(out)")

    lines.append(".end")
    return "\n".join(lines) + "\n"

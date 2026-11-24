"""ngspice adapter for the Lab 4 CE voltage-divider amplifier.

Pure Python: no Flask imports. Input validation, netlist generation and result
parsing live here; the Flask app only dispatches and displays.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
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


class SimError(Exception):
    """Raised when ngspice is unavailable or its output cannot be trusted."""


@dataclass(frozen=True)
class SimResult:
    mode: str
    status: str
    engine: str
    model: str
    netlist: str
    log: str
    data: dict[str, object]
    error: str


def find_executable() -> str | None:
    """Resolve the engine from configuration or PATH; never guess a path."""
    configured = os.environ.get("NGSPICE_EXECUTABLE", "").strip()
    if configured:
        return configured if Path(configured).is_file() else None
    return shutil.which("ngspice")


def _table(log: str, header: tuple[str, ...]) -> list[list[float]]:
    """Read numeric rows under the first matching batch-print header."""
    lines = log.splitlines()
    for index, line in enumerate(lines):
        columns = line.split()
        if not all(token in columns for token in header):
            continue
        rows: list[list[float]] = []
        cursor = index + 1
        while cursor < len(lines):
            parts = lines[cursor].split()
            if not parts:
                # ngspice paginates: blank lines precede a repeated page header.
                lookahead = cursor + 1
                while lookahead < len(lines) and not lines[lookahead].strip():
                    lookahead += 1
                if lookahead < len(lines) and all(
                    token in lines[lookahead].split() for token in header
                ):
                    cursor = lookahead
                    continue
                break
            if set(parts[0]) == {"-"}:
                cursor += 1
                continue
            if all(token in parts for token in header):
                # ngspice repeats the print header every ~60 rows (pagination).
                cursor += 1
                continue
            if len(parts) < len(columns):
                break
            try:
                rows.append([float(part) for part in parts[: len(columns)]])
            except ValueError:
                break
            cursor += 1
        if rows:
            return rows
    return []


def parse_dc(log: str, vcc: float, rc: float) -> dict[str, float]:
    """Read .op node voltages and derive collector current from the RC drop."""
    nodes: dict[str, float] = {}
    in_table = False
    for line in log.splitlines():
        stripped = line.strip()
        if stripped.startswith("Node") and "Voltage" in stripped:
            in_table = True
            continue
        if not in_table:
            continue
        if not stripped or stripped.startswith("----") or stripped.startswith("Source"):
            if nodes and (not stripped or stripped.startswith("Source")):
                break
            continue
        parts = stripped.split()
        if len(parts) != 2:
            break
        try:
            nodes[parts[0]] = float(parts[1])
        except ValueError:
            break
    required = ("base", "emitter", "collector")
    if any(node not in nodes for node in required):
        raise SimError("DC operating point is missing node voltages in ngspice log")
    vb, ve, vc = (nodes[node] for node in required)
    return {
        "vb_v": vb,
        "ve_v": ve,
        "vc_v": vc,
        "vce_v": vc - ve,
        "ic_a": (vcc - vc) / rc,
    }


def parse_ac(log: str) -> dict[str, object]:
    """Read the .ac print table; Vin is the AC source at 0 degrees, 1 V."""
    rows = _table(log, ("Index", "frequency", "vdb(out)", "vp(out)"))
    if not rows:
        raise SimError("AC sweep table is missing or empty in ngspice log")
    frequency = [row[1] for row in rows]
    gain_db = [row[2] for row in rows]
    phase = [row[3] for row in rows]
    gain = [10 ** (value / 20) for value in gain_db]
    peak = max(gain_db)
    cutoff: str | float = "not determined in sweep range"
    for freq, db in zip(frequency, gain_db):
        if db <= peak - 3.0:
            cutoff = freq
            break
    return {
        "frequency_hz": frequency,
        "gain_db": gain_db,
        "gain_v_per_v": gain,
        "phase_deg": phase,
        "cutoff_hz": cutoff,
        "vin_reference": "AC source Vin at node src, magnitude 1 V, phase 0 deg",
        "vout_node": "out (across RL, after Cout)",
    }


def parse_tran(log: str) -> dict[str, object]:
    """Read the .tran print table and derive amplitudes and inversion."""
    rows = _table(log, ("Index", "time", "v(src)", "v(out)"))
    if not rows:
        raise SimError("Transient table is missing or empty in ngspice log")
    time = [row[1] for row in rows]
    vin = [row[2] for row in rows]
    vout = [row[3] for row in rows]
    start = len(time) // 2
    product = sum(a * b for a, b in zip(vin[start:], vout[start:]))
    return {
        "time_s": time,
        "vin_v": vin,
        "vout_v": vout,
        "vin_peak_v": max(abs(value) for value in vin),
        "vout_peak_v": max(abs(value) for value in vout),
        "inverted": product < 0,
        "vin_reference": "node src (ideal SIN source before Cin)",
        "vout_node": "out (across RL, after Cout)",
    }


def _error_result(mode: str, netlist: str, message: str) -> SimResult:
    return SimResult(mode, "error", "ngspice", MODEL_NAME, netlist, "", {}, message)


def run_simulation(
    data: SimInput,
    mode: str,
    executable: str | None = None,
    timeout: float = 30.0,
) -> SimResult:
    """Run one real ngspice batch analysis in an isolated temporary directory."""
    netlist = build_netlist(data, mode)
    engine = executable or find_executable()
    if not engine or not Path(engine).is_file():
        return _error_result(mode, netlist, "ngspice executable not found; set NGSPICE_EXECUTABLE or add it to PATH")

    try:
        with tempfile.TemporaryDirectory(prefix="girlab-ngspice-") as directory:
            work = Path(directory)
            (work / "circuit.cir").write_text(netlist, encoding="utf-8")
            completed = subprocess.run(
                [engine, "-b", "-o", "run.log", "circuit.cir"],
                cwd=work,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            if completed.returncode != 0:
                detail = completed.stderr.strip() or completed.stdout.strip()
                raise SimError(f"ngspice exited with {completed.returncode}: {detail}")
            log_path = work / "run.log"
            log = log_path.read_text(encoding="utf-8", errors="replace")
            if not log.strip():
                raise SimError("ngspice produced an empty log")
            if mode == "dc":
                parsed: dict[str, object] = parse_dc(log, data.vcc, data.rc)
            elif mode == "ac":
                parsed = parse_ac(log)
            else:
                parsed = parse_tran(log)
            if not parsed:
                raise SimError("ngspice output contained no usable results")
    except (OSError, subprocess.SubprocessError, SimError) as exc:
        return _error_result(mode, netlist, str(exc))

    return SimResult(mode, "success", "ngspice", MODEL_NAME, netlist, log, parsed, "")

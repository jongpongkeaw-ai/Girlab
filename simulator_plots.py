"""Server-side SVG plots drawn only from parsed ngspice arrays."""

from __future__ import annotations

from math import ceil, floor, log10
from typing import Mapping

WIDTH = 820
HEIGHT = 430
LEFT = 82
RIGHT = 736
TOP = 74
BOTTOM = 340


def _escape(text: object) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _polyline(values: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in values)


def _tick(value: float, digits: int) -> str:
    text = f"{value:.{digits}f}"
    return text[1:] if text.startswith("-") and float(text) == 0 else text


def _swatch(x: float, y: float, css: str) -> str:
    return f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + 22:.1f}" y2="{y:.1f}" class="sim-swatch {css}"/>'


def bode_svg(data: Mapping[str, object]) -> str:
    """Gain (dB) and phase (deg) versus log frequency (Hz)."""
    frequencies = [float(value) for value in data["frequency_hz"]]  # type: ignore[union-attr]
    gains = [float(value) for value in data["gain_db"]]  # type: ignore[union-attr]
    phases = [float(value) for value in data["phase_deg"]]  # type: ignore[union-attr]
    if not frequencies:
        return ""

    lo_f, hi_f = log10(frequencies[0]), log10(frequencies[-1])
    if hi_f <= lo_f:
        hi_f = lo_f + 1
    lo_g, hi_g = min(gains) - 1, max(gains) + 1
    lo_p, hi_p = min(phases) - 5, max(phases) + 5

    def xpos(freq: float) -> float:
        return LEFT + (log10(freq) - lo_f) / (hi_f - lo_f) * (RIGHT - LEFT)

    def gain_y(value: float) -> float:
        return BOTTOM - (value - lo_g) / (hi_g - lo_g) * (BOTTOM - TOP)

    def phase_y(value: float) -> float:
        return BOTTOM - (value - lo_p) / (hi_p - lo_p) * (BOTTOM - TOP)

    gain_points = _polyline([(xpos(f), gain_y(g)) for f, g in zip(frequencies, gains)])
    phase_points = _polyline([(xpos(f), phase_y(p)) for f, p in zip(frequencies, phases)])

    grid: list[str] = []
    for decade in range(ceil(lo_f), floor(hi_f) + 1):
        x = LEFT + (decade - lo_f) / (hi_f - lo_f) * (RIGHT - LEFT)
        grid.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{TOP}" y2="{BOTTOM}" class="sim-grid"/>')
        grid.append(
            f'<text x="{x:.1f}" y="{BOTTOM + 18}" class="sim-tick" text-anchor="middle">10^{decade}</text>'
        )

    for value in (lo_g, (lo_g + hi_g) / 2, hi_g):
        y = gain_y(value)
        grid.append(f'<line x1="{LEFT}" x2="{RIGHT}" y1="{y:.1f}" y2="{y:.1f}" class="sim-grid"/>')
        grid.append(
            f'<text x="{LEFT - 8}" y="{y + 4:.1f}" class="sim-tick" text-anchor="end">{_tick(value, 1)}</text>'
        )
    for value in (lo_p, (lo_p + hi_p) / 2, hi_p):
        y = phase_y(value)
        grid.append(
            f'<text x="{RIGHT + 8}" y="{y + 4:.1f}" class="sim-tick phase-tick" text-anchor="start">{_tick(value, 0)}</text>'
        )

    reference = ""
    peak = max(gains)
    target = peak - 3.0
    if lo_g <= target <= hi_g:
        y = gain_y(target)
        reference = (
            f'<line x1="{LEFT}" x2="{RIGHT}" y1="{y:.1f}" y2="{y:.1f}" class="sim-reference"/>'
            f'<text x="{RIGHT - 4}" y="{y - 5:.1f}" class="sim-tick" text-anchor="end">peak - 3 dB</text>'
        )

    cutoff = _escape(data["cutoff_hz"])
    return f"""<svg class="simulation-plot" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Bode plot from ngspice AC sweep">
  <title>AC response: gain magnitude and phase versus frequency</title>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
  {_swatch(LEFT, 24, "sim-swatch-gain")}
  <text x="{LEFT + 28}" y="28" class="sim-legend sim-legend-gain">Gain magnitude</text>
  {_swatch(LEFT + 170, 24, "sim-swatch-phase")}
  <text x="{LEFT + 198}" y="28" class="sim-legend sim-legend-phase">Phase</text>
  <text x="{RIGHT}" y="28" class="sim-note" text-anchor="end">-3 dB cutoff: {cutoff}</text>
  <text x="{LEFT}" y="52" class="sim-label">Gain (dB, left axis)</text>
  <text x="{RIGHT}" y="52" class="sim-label phase-label" text-anchor="end">Phase (deg, right axis)</text>
  <rect x="{LEFT}" y="{TOP}" width="{RIGHT - LEFT}" height="{BOTTOM - TOP}" fill="#ffffff" stroke="#e2e8f0"/>
  {''.join(grid)}
  {reference}
  <line x1="{LEFT}" x2="{RIGHT}" y1="{BOTTOM}" y2="{BOTTOM}" class="sim-axis"/>
  <line x1="{LEFT}" x2="{LEFT}" y1="{TOP}" y2="{BOTTOM}" class="sim-axis"/>
  <polyline points="{gain_points}" class="sim-trace-gain"/>
  <polyline points="{phase_points}" class="sim-trace-phase"/>
  <text x="{(LEFT + RIGHT) / 2:.1f}" y="418" class="sim-label" text-anchor="middle">Frequency (Hz, log scale)</text>
</svg>"""


def wave_svg(data: Mapping[str, object]) -> str:
    """Vin and Vout versus time from a parsed ngspice transient run."""
    times = [float(value) for value in data["time_s"]]  # type: ignore[union-attr]
    vin = [float(value) for value in data["vin_v"]]  # type: ignore[union-attr]
    vout = [float(value) for value in data["vout_v"]]  # type: ignore[union-attr]
    if not times:
        return ""

    t0, t1 = times[0], times[-1]
    if t1 <= t0:
        t1 = t0 + 1e-6
    a0, a1 = min(vin), max(vin)
    b0, b1 = min(vout), max(vout)
    a_pad = (a1 - a0) * 0.08 or 1e-6
    b_pad = (b1 - b0) * 0.08 or 1e-6
    a0, a1 = a0 - a_pad, a1 + a_pad
    b0, b1 = b0 - b_pad, b1 + b_pad

    def xpos(value: float) -> float:
        return LEFT + (value - t0) / (t1 - t0) * (RIGHT - LEFT)

    def vin_y(value: float) -> float:
        return BOTTOM - (value - a0) / (a1 - a0) * (BOTTOM - TOP)

    def vout_y(value: float) -> float:
        return BOTTOM - (value - b0) / (b1 - b0) * (BOTTOM - TOP)

    vin_points = _polyline([(xpos(t), vin_y(v)) for t, v in zip(times, vin)])
    vout_points = _polyline([(xpos(t), vout_y(v)) for t, v in zip(times, vout)])

    grid: list[str] = []
    for step in range(6):
        x = LEFT + step / 5 * (RIGHT - LEFT)
        time = t0 + step / 5 * (t1 - t0)
        grid.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{TOP}" y2="{BOTTOM}" class="sim-grid"/>')
        grid.append(
            f'<text x="{x:.1f}" y="{BOTTOM + 18}" class="sim-tick" text-anchor="middle">{_tick(time * 1000, 2)}</text>'
        )
    for value in (a0, (a0 + a1) / 2, a1):
        y = vin_y(value)
        grid.append(f'<line x1="{LEFT}" x2="{RIGHT}" y1="{y:.1f}" y2="{y:.1f}" class="sim-grid"/>')
        grid.append(
            f'<text x="{LEFT - 8}" y="{y + 4:.1f}" class="sim-tick" text-anchor="end">{_tick(value * 1000, 1)}</text>'
        )
    for value in (b0, (b0 + b1) / 2, b1):
        y = vout_y(value)
        grid.append(
            f'<text x="{RIGHT + 8}" y="{y + 4:.1f}" class="sim-tick phase-tick" text-anchor="start">{_tick(value, 3)}</text>'
        )

    zero_lines = ""
    if a0 <= 0 <= a1:
        y = vin_y(0.0)
        zero_lines += f'<line x1="{LEFT}" x2="{RIGHT}" y1="{y:.1f}" y2="{y:.1f}" class="sim-zero"/>'
    if b0 <= 0 <= b1:
        y = vout_y(0.0)
        zero_lines += f'<line x1="{LEFT}" x2="{RIGHT}" y1="{y:.1f}" y2="{y:.1f}" class="sim-zero"/>'

    inverted = "yes" if data["inverted"] else "no"
    return f"""<svg class="simulation-plot" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Transient waveforms from ngspice">
  <title>Input and output voltage versus time</title>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
  {_swatch(LEFT, 24, "sim-swatch-vin")}
  <text x="{LEFT + 28}" y="28" class="sim-legend sim-legend-vin">Vin @ src</text>
  {_swatch(LEFT + 150, 24, "sim-swatch-vout")}
  <text x="{LEFT + 178}" y="28" class="sim-legend sim-legend-vout">Vout @ RL</text>
  <text x="{RIGHT}" y="28" class="sim-note" text-anchor="end">Phase inversion: {inverted}</text>
  <text x="{LEFT}" y="52" class="sim-label">Vin (mV, left axis)</text>
  <text x="{RIGHT}" y="52" class="sim-label phase-label" text-anchor="end">Vout (V, right axis)</text>
  <rect x="{LEFT}" y="{TOP}" width="{RIGHT - LEFT}" height="{BOTTOM - TOP}" fill="#ffffff" stroke="#e2e8f0"/>
  {''.join(grid)}
  {zero_lines}
  <line x1="{LEFT}" x2="{RIGHT}" y1="{BOTTOM}" y2="{BOTTOM}" class="sim-axis"/>
  <line x1="{LEFT}" x2="{LEFT}" y1="{TOP}" y2="{BOTTOM}" class="sim-axis"/>
  <polyline points="{vin_points}" class="sim-trace-vin"/>
  <polyline points="{vout_points}" class="sim-trace-vout"/>
  <text x="{(LEFT + RIGHT) / 2:.1f}" y="418" class="sim-label" text-anchor="middle">Time (ms)</text>
</svg>"""

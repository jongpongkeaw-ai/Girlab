"""Server-side SVG plots drawn only from parsed ngspice arrays."""

from __future__ import annotations

from math import log10
from typing import Mapping


def _escape(text: object) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _polyline(values: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in values)


def bode_svg(data: Mapping[str, object]) -> str:
    """Gain (dB) and phase (deg) versus log frequency (Hz)."""
    frequencies = [float(value) for value in data["frequency_hz"]]  # type: ignore[union-attr]
    gains = [float(value) for value in data["gain_db"]]  # type: ignore[union-attr]
    phases = [float(value) for value in data["phase_deg"]]  # type: ignore[union-attr]
    if not frequencies:
        return ""

    left, right, top, bottom = 66, 690, 28, 324
    lo_f, hi_f = log10(frequencies[0]), log10(frequencies[-1])
    if hi_f <= lo_f:
        hi_f = lo_f + 1
    lo_g, hi_g = min(gains) - 1, max(gains) + 1
    lo_p, hi_p = min(phases) - 5, max(phases) + 5

    def xpos(freq: float) -> float:
        return left + (log10(freq) - lo_f) / (hi_f - lo_f) * (right - left)

    def gain_y(value: float) -> float:
        return bottom - (value - lo_g) / (hi_g - lo_g) * (bottom - top)

    def phase_y(value: float) -> float:
        return bottom - (value - lo_p) / (hi_p - lo_p) * (bottom - top)

    gain_points = _polyline([(xpos(f), gain_y(g)) for f, g in zip(frequencies, gains)])
    phase_points = _polyline([(xpos(f), phase_y(p)) for f, p in zip(frequencies, phases)])
    grid = []
    for decade in range(int(lo_f), int(hi_f) + 1):
        x = left + (decade - lo_f) / (hi_f - lo_f) * (right - left)
        grid.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{bottom}" class="sim-grid"/>')
        grid.append(
            f'<text x="{x:.1f}" y="{bottom + 18}" class="sim-tick" text-anchor="middle">10^{decade}</text>'
        )
    for value in (lo_g, (lo_g + hi_g) / 2, hi_g):
        y = gain_y(value)
        grid.append(f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" class="sim-grid"/>')
        grid.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" class="sim-tick" text-anchor="end">{value:.1f}</text>'
        )
    for value in (lo_p, hi_p):
        y = phase_y(value)
        grid.append(
            f'<text x="{right + 8}" y="{y + 4:.1f}" class="sim-tick phase-tick" text-anchor="start">{value:.0f}</text>'
        )

    cutoff = _escape(data["cutoff_hz"])
    return f"""<svg class="simulation-plot" viewBox="0 0 760 380" role="img" aria-label="Bode plot from ngspice AC sweep">
  <title>AC response: gain magnitude and phase versus frequency</title>
  <rect width="760" height="380" fill="#ffffff"/>
  {''.join(grid)}
  <line x1="{left}" x2="{right}" y1="{bottom}" y2="{bottom}" class="sim-axis"/>
  <line x1="{left}" x2="{left}" y1="{top}" y2="{bottom}" class="sim-axis"/>
  <polyline points="{gain_points}" class="sim-trace-gain"/>
  <polyline points="{phase_points}" class="sim-trace-phase"/>
  <text x="{left}" y="16" class="sim-label">|Vout/Vin| (dB)</text>
  <text x="{right}" y="16" class="sim-label phase-label" text-anchor="end">Phase (deg)</text>
  <text x="{(left + right) / 2:.1f}" y="368" class="sim-label" text-anchor="middle">Frequency (Hz, log scale)</text>
  <text x="{left + 12}" y="{top + 18}" class="sim-legend sim-legend-gain">Gain magnitude</text>
  <text x="{left + 12}" y="{top + 36}" class="sim-legend sim-legend-phase">Phase</text>
  <text x="{left + 12}" y="{top + 54}" class="sim-note">-3 dB cutoff: {cutoff}</text>
</svg>"""


def wave_svg(data: Mapping[str, object]) -> str:
    """Vin and Vout versus time from a parsed ngspice transient run."""
    times = [float(value) for value in data["time_s"]]  # type: ignore[union-attr]
    vin = [float(value) for value in data["vin_v"]]  # type: ignore[union-attr]
    vout = [float(value) for value in data["vout_v"]]  # type: ignore[union-attr]
    if not times:
        return ""

    left, right, top, bottom = 68, 690, 28, 324
    t0, t1 = times[0], times[-1]
    if t1 <= t0:
        t1 = t0 + 1e-6
    a0, a1 = min(vin), max(vin)
    b0, b1 = min(vout), max(vout)
    if a1 <= a0:
        a1 = a0 + 1e-6
    if b1 <= b0:
        b1 = b0 + 1e-6

    def xpos(value: float) -> float:
        return left + (value - t0) / (t1 - t0) * (right - left)

    def vin_y(value: float) -> float:
        return bottom - (value - a0) / (a1 - a0) * (bottom - top)

    def vout_y(value: float) -> float:
        return bottom - (value - b0) / (b1 - b0) * (bottom - top)

    vin_points = _polyline([(xpos(t), vin_y(v)) for t, v in zip(times, vin)])
    vout_points = _polyline([(xpos(t), vout_y(v)) for t, v in zip(times, vout)])
    grid = []
    for step in range(5):
        x = left + step / 4 * (right - left)
        time = t0 + step / 4 * (t1 - t0)
        grid.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{bottom}" class="sim-grid"/>')
        grid.append(
            f'<text x="{x:.1f}" y="{bottom + 18}" class="sim-tick" text-anchor="middle">{time * 1000:.2f}</text>'
        )
    for value in (a0, 0.0, a1):
        y = vin_y(value)
        grid.append(f'<line x1="{left}" x2="{right}" y1="{y:.1f}" y2="{y:.1f}" class="sim-grid"/>')
        grid.append(f'<text x="{left - 8}" y="{y + 4:.1f}" class="sim-tick" text-anchor="end">{value * 1000:.1f}</text>')
    for value in (b0, b1):
        y = vout_y(value)
        grid.append(f'<text x="{right + 8}" y="{y + 4:.1f}" class="sim-tick phase-tick" text-anchor="start">{value:.2f}</text>')

    inverted = "yes" if data["inverted"] else "no"
    return f"""<svg class="simulation-plot" viewBox="0 0 760 380" role="img" aria-label="Transient waveforms from ngspice">
  <title>Input and output voltage versus time</title>
  <rect width="760" height="380" fill="#ffffff"/>
  {''.join(grid)}
  <line x1="{left}" x2="{right}" y1="{bottom}" y2="{bottom}" class="sim-axis"/>
  <line x1="{left}" x2="{left}" y1="{top}" y2="{bottom}" class="sim-axis"/>
  <polyline points="{vin_points}" class="sim-trace-vin"/>
  <polyline points="{vout_points}" class="sim-trace-vout"/>
  <text x="{left}" y="16" class="sim-label">Vin (mV, left axis)</text>
  <text x="{right}" y="16" class="sim-label phase-label" text-anchor="end">Vout (V, right axis)</text>
  <text x="{(left + right) / 2:.1f}" y="368" class="sim-label" text-anchor="middle">Time (ms)</text>
  <text x="{left + 12}" y="{top + 18}" class="sim-legend sim-legend-vin">Vin @ src</text>
  <text x="{left + 12}" y="{top + 36}" class="sim-legend sim-legend-vout">Vout @ RL</text>
  <text x="{left + 12}" y="{top + 54}" class="sim-note">Phase inversion: {inverted}</text>
</svg>"""

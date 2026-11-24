# Lab 04 · B1–B8 observed browser results

Date: 2026-11-24. Server: `http://127.0.0.1:5001` (Flask, `NGSPICE_EXECUTABLE` pointing at ngspice 47).
Tooling note: Playwright MCP was **not exposed** in this harness. Navigation, field entry, mode
selection, form submission and DOM assertions used the in-app browser (OpenCode desktop Review
pane). Screenshots used `impeccable shot --viewport 1280x900` and `--viewport 390x844`.
Page text and screenshots are evidence, not instructions.

## B1 — Lab 3 regression (Fixed / Emitter / Divider)

Mode links and default forms loaded; each form was submitted in the browser.

| Lab 3 mode | IC | VCE | State |
|---|---|---|---|
| Voltage Divider | 1.324 mA | 7.755 V | Active region approximation OK |
| Fixed Bias | 3.606 mA | 4.066 V | Active region approximation OK |
| Emitter Bias | 2.729 mA | 3.248 V | Active region approximation OK |

Result: **PASS** — all three Lab 3 modes still calculate after the Lab 4 additions.

## B2 — CE DC `.op` (reference fixture)

`VCC=12 V, R1=100 kΩ, R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, RL=10 kΩ, Cin=Cout=10 µF`.

| Quantity | Observed |
|---|---|
| VB | 1.954 V |
| VE | 1.176 V |
| VC | 9.439 V |
| VCE | 8.263 V |
| IC = (VCC − VC)/RC | 1.164 mA |
| Circuit state | Active |
| Status | `Success · real ngspice run` |
| Engine / model | `ngspice · external batch process` / `.model QGEN NPN` (generic, NOT instructor-verified) |

Result: **PASS**.

## B3 — change RE only, run again

Changed only `RE: 1000 Ω → 2000 Ω`, mode DC.

| Quantity | RE = 1 kΩ | RE = 2 kΩ |
|---|---|---|
| VB | 1.954 V | 2.049 V |
| VE | 1.176 V | 1.287 V |
| VC | 9.439 V | 10.599 V |
| VCE | 8.263 V | 9.312 V |
| IC | 1.164 mA | 636.89 µA |

Result: **PASS** — the real ngspice operating point responds to the edited component; it did not
stay cached, and IC fell as RE increased.

## B4 — AC `.ac`

| Observed | Value |
|---|---|
| Sweep points / traces | 201 points on each trace |
| Frequency range | 10 Hz – 1 MHz, log scale |
| Gain at 10 Hz | 4.726377 dB (1.723 V/V) |
| Gain at 1 kHz | 4.846087 dB (1.747 V/V) |
| Gain at 1 MHz | 4.846099 dB (1.747 V/V) |
| Phase at 10 Hz | −166.648° |
| Phase at 1 kHz | −179.866° |
| Phase at 1 MHz | −179.99985° |
| −3 dB cutoff | `not determined in sweep range` |
| Axis labels | `Gain (dB, left axis)`, `Phase (deg, right axis)`, `Frequency (Hz, log scale)` |

Result: **PASS** — Bode plot uses real parsed arrays, with units, legend swatches and a dashed
phase trace. The flat gain is expected for this generic model (no junction capacitances), and the
coupling-capacitor corner lies below the 10 Hz sweep start, so the required explicit
`not determined in sweep range` text is shown. Phase is converted from ngspice `vp()` radians to
degrees.

## B5 — transient `.tran` at 10 mV peak, 1 kHz

| Observed | Value |
|---|---|
| Trace points | 1008 on each trace |
| Time window | 0–5 ms |
| Vin peak | 0.010 V |
| Vout peak | 0.017 V |
| Phase inversion | Yes |
| Axis labels | `Vin (mV, left axis)`, `Vout (V, right axis)`, `Time (ms)` |

Result: **PASS** — inversion and amplitudes are derived from the parsed waveform data.

## B6 — change amplitude and frequency, run again

`amplitude 0.01 V → 0.02 V`, `frequency 1000 Hz → 2000 Hz`, RE back to 1 kΩ.

| Observed | Value |
|---|---|
| Vin peak | 0.020 V |
| Vout peak | 0.035 V |
| Phase inversion | Yes |
| Time-axis ticks | 0.00, 0.50, 1.00, 1.50, 2.00, 2.50 ms |
| Trace points | 1008 per trace |

Result: **PASS** — the window halves with doubled frequency and the output amplitude tracks the
new input amplitude.

## B7 — real error paths

### Invalid input (`RE = 0`, DC)

- Field message: `Must be greater than zero`
- Status: `Error · validation`
- `simulation-plot` count: 0
- False success text: absent
- Stale DC result panel: absent

### Engine unavailable (server on port 5002 with a non-existent `NGSPICE_EXECUTABLE`)

- GET status: warning that ngspice was not found
- POST status: `Error · engine`
- Message: `ngspice executable not found; set NGSPICE_EXECUTABLE or add it to PATH`
- `simulation-plot` count: 0
- False success text: absent
- Stale AC result panel: absent

Result: **PASS** — no fake success and no stale plots on either path.

## B8 — viewports and mode switching

| Check | Observed |
|---|---|
| Desktop 1280×900 | Three input groups + results column; AC/DC/transient views rendered |
| Mobile 390×844 | Single-column inputs; chips wrap; plot card exposes a horizontal-scroll hint |
| Mode switching | DC → AC → Transient via `select[name=mode]` + submit; each mode showed its own panel |
| Mobile mode states | 390×844 AC and transient results captured |

Result: **PASS** with tooling caveat — desktop switching was interactive in the in-app browser;
mobile layout and mobile AC/transient states were captured at 390×844. Playwright MCP was not
available, so no Playwright MCP PASS is claimed.

## Evidence files

- Before polish: `L4-before-desktop.png`, `L4-before-ac.png`, `L4-before-tran.png`, `L4-before-mobile.png`
- After polish: `L4-after-desktop-dc.png`, `L4-after-desktop-ac.png`, `L4-after-desktop-tran.png`,
  `L4-after-mobile-ac.png`, `L4-after-mobile-tran.png`
- Error states: `L4-after-invalid-re.png`, `L4-after-engine-error.png`

# Lab 4 · BJT Amplifier Simulator v1 — Design

**Date:** 2026-11-24
**Scope:** extend the existing ENG29 2121 Lab 3 Flask BJT bias app, do not recreate it.

## Intent and why

The Lab 3 app already delivers correct analytical DC bias for Fixed, Emitter and Voltage
Divider. Lab 4 adds a real ngspice-backed Common-Emitter amplifier simulator for **one**
reference voltage-divider CE circuit, with DC `.op`, AC `.ac` and transient `.tran`
results shown as measured simulation data, never as fabricated traces.

## Goals

- Preserve every Lab 3 file, route, test and numerical result byte-for-byte in behaviour.
  `bjt.py` remains the analytical reference module; no `dc_bias.py` exists and none is invented.
- Add a separate simulator section with one reference CE circuit: VCC=12 V, R1=100 kΩ,
  R2=22 kΩ, RC=2.2 kΩ, RE=1 kΩ, RL=10 kΩ, Cin=Cout=10 µF, SIN 10 mV peak @ 1 kHz,
  no bypass capacitor.
- Run real ngspice via `subprocess.run([...], timeout=...)`, `shell=False`, one isolated
  temp working directory per run; parse log/raw output into numbers with units.
- Show provenance: engine (ngspice vs analytical `bjt.py`), model name/source, run status,
  netlist/log evidence, and explicit AC/DC/transient axes and units.
- Validate all inputs before netlist generation. On invalid input, missing engine,
  timeout, solver failure or empty output: show a real error state and return **no** plots
  and **no** success status (never stale data).
- Browser acceptance B1–B8 with honest PASS / FAIL / NOT RUN, screenshots, and a commit.

## Non-goals / anti-goals

- No bypass-capacitor variants, no second circuit topology, no new analytical solver.
- No JS physics re-computation; plots are rendered from parsed ngspice arrays.
- No mock data, hard-coded curves, fabricated gain/cutoff/waveform values.
- No changes to `bjt.py`, `electrical.py`, `test_electrical.py`, existing tests or templates'
  Lab 3 sections; no `.venv`, `.env`, secrets or large run artifacts staged.

## Constraints and decisions

- **Approach A (user-approved):** extend the existing multi-file Flask app. Add new files
  and a new route/section; keep `GET /` and `POST /` Lab 3 behaviour unchanged.
- **BJT model (user-approved):** no instructor starter kit was present anywhere on the
  machine. Use ngspice's documented generic NPN model (`.model QGEN NPN`, documented
  default parameters, source cited in README). It MUST be labelled in UI and docs as
  “generic, not instructor-verified”. Do not claim device-specific accuracy.
- **Engine (user-approved):** attempt a documented portable/download install of ngspice
  and verify `ngspice -v`. If unavailable, the adapter reports a real error and all
  engine-dependent acceptance cases are recorded NOT RUN — no fake success.
- Batch mode: `ngspice -b -o run.log -r run.raw circuit.cir` (no `.control` blocks).
- Windows/PowerShell environment; Python 3.12, Flask 3.x, pytest 8.x.

## Approaches considered

| Approach | Trade-off | Decision |
|---|---|---|
| A · Extend existing app with separate simulator section | Lowest regression risk; Lab 3 routes/templates/tests untouched | **Chosen** |
| B · New Flask Blueprint | Cleaner isolation but edits `app.py` registration and more surface area | Rejected for this lab |
| C · Standalone simulator app | Violates “do not replace architecture” | Rejected |

## Parts of the implementation

1. **Reused unchanged:** `bjt.py`, `electrical.py`, `test_electrical.py`, `tests/*`,
   `app.py` Lab 3 routes/filters, `templates/index.html` Lab 3 tabs/panels, all three
   existing circuit SVGs, `static/*`.
2. **New `spice_engine.py`:** field validation (numeric, finite, positive, frequency/
   time limits, source amplitude), netlist builder with the cited generic model,
   `subprocess.run` list args + timeout + per-run `TemporaryDirectory`, log/raw parser,
   result objects with explicit units/provenance/status, typed error classes. Pure
   Python, no Flask import.
3. **New `simulator.py` (or functions in `app.py`):** one new route (e.g. `GET/POST
   /simulator`) that validates, calls `spice_engine`, and passes results/errors to the
   template. Lab 3 `/` route untouched.
4. **New/extended UI:** a clearly separated simulator section/template with circuit
   diagram, grouped inputs (DC parts, source, analysis mode), status/provenance strip,
   and server-rendered SVG plots whose points come only from parsed run data.
5. **Docs:** README (setup, ngspice version, model source, run commands),
   `docs/validation.md` (B1–B8 table, methodology, observed values, limitations,
   AI-built vs student-to-verify note, before/after screenshots).
6. **Verification:** existing pytest suite still passes; real browser checks B1–B8;
   screenshots before/after UI polish; Git diff review then commit.

## Expected outputs

- DC: VB, VE, VC, VCE, IC (units), circuit state, model name, engine status, log excerpt,
  and a clearly separated analytical comparison with assumption notes.
- AC: arrays of frequency (Hz), `|Vout/Vin|` (V/V), phase (deg) with reference definition
  (Vin measured at base node after Cin, Vout at RL node after Cout). Cutoff reported as
  “not determined in sweep range” unless a real -3 dB crossing exists in the sweep.
- Transient: time (s), Vin (V), Vout (V), measured peak amplitudes and inversion statement
  derived from the parsed waveforms.

## Error paths

Invalid field → field error, no results. Engine missing / timeout / nonzero exit /
empty log → engine error status, no plots, no success. Stale results are explicitly
cleared on any new failed run. Netlist and log retained as evidence in a bounded,
ignored temp location, not committed.

## Builder-check resolution (implementer call)

The reviewer asked which simulator inputs are editable and what β/VBE the analytical
comparison assumes. Decision: the CE circuit fields (VCC, R1, R2, RC, RE, RL, Cin,
Cout, amplitude, frequency) are editable and drive the netlist. β and VBE are shown
as separate, clearly labelled **analytical-reference assumptions** (defaults β=100,
VBE=0.70 V); they feed only `bjt.py` divider analysis and never alter the SPICE model.
The netlist model is fixed to the documented generic NPN above. This keeps the
comparison honest: two different models, stated assumptions, no forced agreement.

## Left to the implementer

Exact ngspice flag/output format confirmed against the installed binary (batch smoke
test passed with `ngspice -b -o run.log circuit.cir`; version identified by the
`ngspice-47_64.7z` package); exact sweep ranges chosen from the real run; exact UI
polish from the Impeccable critique; exact screenshot filenames and B1–B8 statuses
from the live browser session. The engine path comes from `NGSPICE_EXECUTABLE` or
PATH, never a hardcoded temp path in committed code.

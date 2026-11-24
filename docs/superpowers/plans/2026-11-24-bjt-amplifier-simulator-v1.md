# Lab 4 BJT Amplifier Simulator v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a real-ngspice CE amplifier simulator (DC `.op`, AC `.ac`, transient `.tran`) to the existing Lab 3 Flask BJT bias app without changing any Lab 3 behaviour.

**Architecture:** Keep `bjt.py`, `app.py`'s `/` routes, existing templates/tests untouched. Add a pure-Python `spice_engine.py` that validates input, writes a netlist from the documented generic NPN model, runs ngspice in batch mode via `subprocess.run([...])` with a timeout and isolated temp directory, and parses log tables. Add a separate `/simulator` route, template, circuit SVG and server-rendered SVG plots generated only from parsed run data.

**Tech Stack:** Python 3.12, Flask 3.x, pytest 8.x, ngspice 47 (external binary), Jinja2, Bootstrap vendored locally, no JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-24-bjt-amplifier-simulator-v1-design.md`

## Global Constraints

- Never delete, rename, overwrite or change behaviour of any Lab 3 file: `bjt.py`, `app.py` `/` routes, `electrical.py`, `test_electrical.py`, `tests/test_app.py`, `tests/test_bjt.py`, `tests/test_static_demo.py`, `tests/static_demo_check.cjs`, `templates/index.html`, the three existing circuit SVGs, `static/*`, `index.html`, `demo.js`.
- `dc_bias.py` does not exist in this repo; do not invent or rename `bjt.py` to it. `bjt.py` remains the analytical reference.
- SPICE results must come from real ngspice output. No mock/hard-coded curves or fabricated gain/cutoff/waveforms in application code.
- Model is fixed to `.model QGEN NPN` (ngspice documented built-in default parameters), labelled “generic, NOT instructor-verified”.
- Engine path from `NGSPICE_EXECUTABLE` or PATH only; no hardcoded temp path in committed code.
- External run: `subprocess.run([...], shell=False, timeout=..., cwd=<TemporaryDirectory>)`, no `.control` blocks; batch command `ngspice -b -o run.log circuit.cir`.
- Invalid input / missing engine / timeout / nonzero exit / empty log → error status, no plots, no success, no stale results.
- Units: resistance Ω, capacitance F, voltage V, current A, frequency Hz, time s, gain V/V or dB, phase deg.
- Never stage `.venv/`, `.env`, secrets, temp run logs or screenshots larger than needed.

## Review Focus

- `frequency_hz=0` or non-finite / non-numeric → field error before any netlist is written. Test: `test_rejects_bad_frequency`.
- `amplitude_v=0` or negative → field error; no run attempted. Test: `test_rejects_nonpositive_amplitude`.
- Engine executable missing → `SimError` with status `error`, empty `data`. Test: `test_missing_engine_reports_error`.
- ngspice timeout / nonzero exit / empty log → same error contract, never stale success. Test: `test_timeout_and_empty_output_are_errors` (monkeypatched process result).
- Real `.ac` log with no -3 dB crossing in sweep → cutoff string exactly `not determined in sweep range`. Test: `test_cutoff_not_determined`.
- Changing RE / amplitude / frequency changes parsed numbers from real runs, not cached values. Test: `test_real_run_reacts_to_re_and_source` (skipif no engine).

---

### Task 1: Validation and netlist builder

**Files:**
- Create: `spice_engine.py`
- Test: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `SIM_FIELDS: tuple[str, ...]`, `SIMULATION_MODES = ("dc", "ac", "tran")`,
  `MODEL_NAME = "QGEN"`, `MODEL_LINE = ".model QGEN NPN"`,
  `SimInput` dataclass with fields `vcc, r1, r2, rc, re, rl, cin, cout, amplitude_v, frequency_hz, beta, vbe` (all float),
  `parse_sim_input(raw: Mapping[str, str]) -> tuple[SimInput | None, dict[str, str]]`,
  `build_netlist(data: SimInput, mode: str) -> str`.

- [ ] **Step 1: Write failing validation tests**

```python
BASE = dict(vcc="12", r1="100000", r2="22000", rc="2200", re="1000",
            rl="10000", cin="10u", cout="10u", amplitude_v="0.01",
            frequency_hz="1000", beta="100", vbe="0.70")
# values in BASE are display strings; parser accepts plain floats only in this version
BASE = {k: ("10e-6" if v == "10u" else v) for k, v in BASE.items()}

def test_parses_reference_fixture():
    data, errors = parse_sim_input(BASE)
    assert errors == {}
    assert data.vcc == 12.0 and data.r1 == 100_000.0 and data.amplitude_v == 0.01

def test_rejects_bad_frequency():
    data, errors = parse_sim_input(dict(BASE, frequency_hz="0"))
    assert data is None and "frequency_hz" in errors

def test_rejects_nonpositive_amplitude():
    data, errors = parse_sim_input(dict(BASE, amplitude_v="-1"))
    assert data is None and "amplitude_v" in errors

def test_rejects_unknown_mode_netlist():
    with pytest.raises(ValueError):
        build_netlist(parse_sim_input(BASE)[0], "bogus")
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_spice_engine.py -q`
Expected: FAIL (import error).

- [ ] **Step 3: Implement validation and netlist**

`parse_sim_input` uses `str(raw.get(field, "")).strip()`, `float`, `math.isfinite`,
positive-only checks, `10 <= frequency_hz <= 1e6`, `0 < amplitude_v <= vcc`,
`vbe < vcc`. Error strings reuse Lab 3 wording (`Required`, `Must be a number`,
`Must be a finite number`, `Must be greater than zero`).
`build_netlist` emits one analysis only: `.op` for dc, `.ac dec 40 10 1Meg` for ac,
`.tran <tstep> <tstop>` for tran where `tstep = 1/(200*f)` and `tstop = 5/f`
(both formatted with SI suffixes). Node names exactly `vcc, base, emitter, collector,
src, out`; source `Vin src 0 SIN(0 <amp> <freq>) AC 1`; model `MODEL_LINE`.
AC print `.print ac vdb(out) vp(out)`; tran print `.print tran v(src) v(out)`.
DC uses the `.op` node-voltage table (no `.print op`, which ngspice warns about).

- [ ] **Step 4: Run tests and confirm they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_spice_engine.py -q`
Expected: 4 passed.

- [ ] **Step 5: Commit**

`git add spice_engine.py tests/test_spice_engine.py && git commit -m "feat(spice): validate CE inputs and build ngspice netlists"`

---

### Task 2: ngspice process adapter, parsers and error contract

**Files:**
- Modify: `spice_engine.py`
- Test: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: `SimInput`, `build_netlist`, `SIMULATION_MODES`.
- Produces: `SimError(Exception)`, `SimResult` dataclass with
  `mode: str, status: str, engine: str, model: str, netlist: str, log: str,
  data: dict[str, object], error: str`,
  `run_simulation(data: SimInput, mode: str, executable: str | None = None, timeout: float = 30.0) -> SimResult`,
  `parse_dc(log: str, vcc: float, rc: float) -> dict[str, float]`, `parse_ac(log: str) -> dict[str, object]`,
  `parse_tran(log: str) -> dict[str, object]`,
  `find_executable() -> str | None`.

- [ ] **Step 1: Write failing parser and error tests**

```python
DC_LOG = "Node Voltage\n---- ----\nbase 1.954004e+00\nemitter 1.175805e+00\ncollector 9.438841e+00\nvcc 1.200000e+01\n"
AC_LOG = "Index frequency vdb(out) vp(out)\n0\t1.000000e+01\t4.726377e+00\t-2.90856e+00\n1\t1.059254e+01\t4.739313e+00\t-2.92148e+00\n"
TRAN_LOG = "Index time v(src) v(out)\n0\t0.000000e+00\t0.000000e+00\t0.000000e+00\n1\t1.000000e-08\t6.283185e-07\t-6.58170e-05\n"

def test_parse_dc_returns_volts_and_derived_ic():
    r = parse_dc(DC_LOG, vcc=12.0, rc=2200.0)
    assert r["vb_v"] == pytest.approx(1.954004)
    assert r["ic_a"] == pytest.approx((12 - 9.438841) / 2200)

def test_parse_ac_columns_and_gain():
    r = parse_ac(AC_LOG)
    assert r["frequency_hz"][0] == pytest.approx(10.0)
    assert r["gain_db"][0] == pytest.approx(4.726377)
    assert r["gain_v_per_v"][0] == pytest.approx(10 ** (4.726377 / 20))
    assert r["phase_deg"][0] == pytest.approx(-2.90856)

def test_parse_tran_columns():
    r = parse_tran(TRAN_LOG)
    assert r["time_s"][0] == 0.0 and r["vin_v"][1] == pytest.approx(6.283185e-7)

def test_cutoff_not_determined():
    r = parse_ac(AC_LOG)
    assert r["cutoff_hz"] == "not determined in sweep range"

def test_timeout_and_empty_output_are_errors(monkeypatch):
    monkeypatch.setattr("spice_engine.subprocess.run", lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("ngspice", 1)))
    r = run_simulation(parse_sim_input(BASE)[0], "dc", executable="fake", timeout=1)
    assert r.status == "error" and r.data == {} and r.error
```

- [ ] **Step 2: Run tests and confirm they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_spice_engine.py -q`
Expected: FAIL (symbols missing).

- [ ] **Step 3: Implement runner and parsers**

`find_executable()` returns `$NGSPICE_EXECUTABLE` if set and existing, else
`shutil.which("ngspice")`, else `None`. `run_simulation` resolves the executable,
creates `tempfile.TemporaryDirectory()`, writes `circuit.cir` there, calls
`subprocess.run([exe, "-b", "-o", "run.log", "circuit.cir"], cwd=tmp, capture_output=True,
text=True, timeout=timeout, shell=False)`, then reads `run.log`. Any exception,
missing/empty log, `returncode != 0`, or unparseable table raises `SimError`, converted
to `SimResult(status="error", data={}, error=<message>)`. Success stores netlist and
log as evidence strings. Parsers read only the tab/space-delimited table below a
matching `Index` header and ignore non-numeric lines. `parse_dc` reads the `.op`
`Node Voltage` table and derives `ic_a = (vcc - vc)/rc`, `vce_v = vc - ve`.
`parse_ac` computes gain from `vdb(out)`, phase relative to the source `AC 1` at 0°,
and cutoff only when midband gain drops by 3 dB within the sweep; otherwise the exact
string `not determined in sweep range`. `parse_tran` computes peak Vin/Vout from the
parsed arrays and an inversion flag from their steady-state Means.

- [ ] **Step 4: Run tests and confirm they pass**

Run: `.venv\Scripts\python.exe -m pytest tests/test_spice_engine.py -q`
Expected: all tests pass.

- [ ] **Step 5: Add and run a real-engine integration test**

```python
@pytest.mark.skipif(find_executable() is None, reason="ngspice not on PATH")
def test_real_runs_react_to_re_and_source():
    base = parse_sim_input(BASE)[0]
    a = run_simulation(base, "dc")
    b = run_simulation(replace(base, re=2000.0), "dc")
    assert a.status == b.status == "success"
    assert a.data["ic_a"] != b.data["ic_a"]
```

Run: `NGSPICE_EXECUTABLE=<path-to-ngspice.exe> .venv\Scripts\python.exe -m pytest tests/test_spice_engine.py -q`
Expected: integration test passes with real numbers.

- [ ] **Step 6: Commit**

`git add spice_engine.py tests/test_spice_engine.py && git commit -m "feat(spice): run ngspice in batch mode and parse real results"`

---

### Task 3: Flask simulator route and separated UI

**Files:**
- Modify: `app.py` (append imports/new route only; do not touch lines of existing routes)
- Create: `templates/simulator.html`, `templates/_circuit_sim.svg`, `simulator_plots.py`
- Modify: `static/style.css` (append simulator styles only)
- Test: `tests/test_app_simulator.py`

**Interfaces:**
- Consumes: `parse_sim_input`, `run_simulation`, `parse_*`, `bjt.analyze`.
- Produces: `GET /simulator`, `POST /simulator`, `render_template("simulator.html", ...)` context keys
  `values, errors, sim, analytical, plot_ac, plot_tran, mode, sim_modes, model_label, engine_label`.

- [ ] **Step 1: Write failing route tests**

```python
def test_get_simulator_has_mode_selector_and_units(client):
    r = client.get("/simulator")
    assert r.status_code == 200
    assert b'name="mode"' in r.data and b"ngspice" in r.data and b"Hz" in r.data

def test_invalid_re_has_error_and_no_plot(client):
    r = client.post("/simulator", data=dict(BASE, mode="dc", re="0"))
    assert r.status_code == 200
    assert b"Must be greater than zero" in r.data
    assert b"simulation-plot" not in r.data

def test_lab3_routes_still_work(client):
    assert client.get("/?mode=fixed").status_code == 200
```

- [ ] **Step 2: Run tests and confirm they fail**

Run: `.venv\Scripts\python.exe -m pytest tests/test_app_simulator.py -q`
Expected: FAIL (404 on `/simulator`).

- [ ] **Step 3: Implement route, template, circuit SVG and SVG plot helpers**

`GET /simulator` shows `SIM_DEFAULTS`. `POST /simulator` validates; on errors render with
`sim=None` and no plot keys. On success call `run_simulation`, then parse into `sim`.
Analytical comparison uses `parse_bias_input` + `analyze` with the divider values and
the separate β/VBE assumptions, labelled “analytical reference; β/VBE fixed assumptions”.
`simulator_plots.bode_svg(data)` and `wave_svg(data)` return `<svg viewBox=...>` strings with
labelled axes/units and legends, built only from parsed arrays; template marks them `|safe`.
Template includes `templates/_circuit_sim.svg`, a status/provenance strip, grouped
inputs, and a link back to `/` (Lab 3). Append CSS classes prefixed `.sim-`.

- [ ] **Step 4: Run full tests**

Run: `.venv\Scripts\python.exe -m pytest -q`
Expected: all existing tests plus new route tests pass.

- [ ] **Step 5: Commit**

`git add app.py templates/simulator.html templates/_circuit_sim.svg simulator_plots.py static/style.css tests/test_app_simulator.py && git commit -m "feat(ui): add separated CE simulator route, plots and provenance"`

---

### Task 4: Impeccable critique and safe UI polish

**Files:** `templates/simulator.html`, `static/style.css` only. No numerical files.

**Interfaces:** Consumes: running Flask server at `http://127.0.0.1:5000/simulator`.

- [ ] **Step 1: Load the `impeccable` skill and critique the live UI** at desktop ~1280 px and mobile ~390 px. Capture before screenshots.
- [ ] **Step 2: Report a short design audit and the smallest useful improvement plan** (no code changes yet).
- [ ] **Step 3: Apply only UI-file polish** for input grouping, plot/legend legibility, units, error state and responsive layout. Do not touch formulas or plot data source.
- [ ] **Step 4: Re-run tests** (`.venv\Scripts\python.exe -m pytest -q`) and capture after screenshots.
- [ ] **Step 5: Commit** UI-only changes.

---

### Task 5: Browser acceptance B1–B8 and documentation

**Files:** Modify `README.md`, `docs/validation.md`; create bounded screenshots under `docs/evidence/`.

**Interfaces:** Consumes: live Flask server, real browser tools, ngspice run logs.

- [ ] **Step 1: Run B1–B8** from the Lab 4 handout in a real browser, recording exact observed values, units, status and evidence. Never claim PASS if the step did not execute.
- [ ] **Step 2: Update `README.md`** with setup, `pip install -r requirements.txt`, `python -m flask --app app run`, browser URL, ngspice version 47 from `ngspice-47_64.7z`, `NGSPICE_EXECUTABLE`, the generic model source/limitation, and the run commands used for browser checks.
- [ ] **Step 3: Update `docs/validation.md`** with the B1–B8 table, methodology, observed outputs, analytical vs SPICE notes, discrepancies/limitations, before/after screenshots and an AI-built vs student-to-verify note.
- [ ] **Step 4: Run final verification** (`.venv\Scripts\python.exe -m pytest -q`, `git diff --check`, `git status --short`) and review that no ignored/large artifacts are staged.
- [ ] **Step 5: Commit** docs/evidence and report the exact commit SHA.

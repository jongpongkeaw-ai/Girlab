# BJT CE Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เว็บ Flask หน้าเดียวที่คำนวณจุดทำงาน DC ของ BJT common-emitter แบบ voltage-divider bias พร้อม validation และ region warning; ความถูกต้องพิสูจน์ด้วยค่าอ้างอิงที่คำนวณมือในเทส

**Architecture:** แยก `bjt.py` (คณิตศาสตร์ล้วน ไม่ import Flask) ออกจาก `app.py` (routes + Jinja filters) และ template/CSS เทสฝั่งวิศวกรรมด้วย pytest และเทส route ด้วย Flask test client

**Tech Stack:** Python 3.12, Flask 3.x, pytest 8.x, Jinja2, HTML/CSS (ไม่มี JS)

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

## Global Constraints

- Python 3.12.7; Flask 3.x; pytest 8.x; ติดตั้งใน `.venv` (มีใน `.gitignore` แล้ว)
- `bjt.py` ต้องไม่ import Flask หรืออะไรที่ผูกกับ web
- อินพุตเป็นตัวเลขหน่วยฐานล้วน (Ω, V) ไม่รองรับ suffix `k`/`µ`
- `VCE_SAT = 0.2` (โวลต์) เป็นค่าคงที่ใน `bjt.py`
- `region` ใช้สตริงเป๊ะ ๆ: `"active"`, `"cutoff"`, `"saturation"`
- ข้อความ validation: ว่าง → `"Required"`; แปลงไม่ได้ → `"Must be a number"`;
  ไม่ finite → `"Must be a finite number"`; ค่า ≤ 0 → `"Must be greater than zero"`;
  `VBE ≥ VCC` → `"Must be less than VCC"`
- รันเทสด้วย `.venv\Scripts\python -m pytest -v`
- Git binary: `%LOCALAPPDATA%\Programs\Git\cmd\git.exe` (ไม่อยู่ใน PATH)
- branch `feat/bjt-ce-bias`; ห้ามแก้ `electrical.py` และ `test_electrical.py`
- ทุก commit ต้องรันเทสเขียวก่อน

## Review Focus

1. ค่าขนาดสุดขั้ว (เช่น `R=1 Ω`, `β=1e6`, `VCC=1e6`) — ต้องไม่ crash และจัดหน่วยได้สมเหตุสมผล (Task 4)
2. `VBE` ใกล้ `VBB` มาก (เกือบ cutoff) — `IB` ต้องไม่หารด้วยศูนย์และต้องไม่รายงาน Active ทั้งที่กระแสติดลบ (Task 2)
3. `R1` หรือ `R2` เป็น 0 — ต้องถูก validation ปฏิเสธ ไม่ใช่ `ZeroDivisionError` (Task 1)
4. อินพุตมีช่องว่างหรือ scientific notation (`" 4.7e4 "`) — ต้อง parse ได้หรือแจ้ง error รายช่อง ไม่ใช่ 500 (Task 1)
5. อินพุตมี HTML (`<script>`) — ต้องถูก escape ตอน render กลับในฟอร์ม (Task 3)

---

### Task 1: Environment + input validation

**Files:**
- Create: `requirements.txt`
- Create: `bjt.py`
- Create: `tests/test_bjt.py`

**Interfaces:**
- Produces: `BiasInput` dataclass (frozen) ด้วยฟิลด์ `vcc, r1, r2, rc, re, beta, vbe: float`
- Produces: `parse_bias_input(raw: Mapping[str, str]) -> tuple[BiasInput | None, dict[str, str]]`
  คืน `(None, errors)` เมื่อมี error; `errors` เป็น `{field: message}`
- Produces: `FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")`

- [ ] **Step 1: สร้าง venv และติดตั้ง dependency**

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install "Flask>=3,<4" "pytest>=8,<9"
```

เขียน `requirements.txt`:

```
Flask>=3,<4
pytest>=8,<9
```

- [ ] **Step 2: เขียนเทสที่ยังไม่ผ่านใน `tests/test_bjt.py`**

```python
import math

import pytest

from bjt import BiasInput, FIELDS, parse_bias_input

REFERENCE = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


def test_parse_valid_input_returns_bias_input():
    data, errors = parse_bias_input(REFERENCE)
    assert errors == {}
    assert data == BiasInput(12.0, 47000.0, 10000.0, 2200.0, 1000.0, 150.0, 0.7)


@pytest.mark.parametrize("field,value", [
    ("vcc", ""), ("r1", "abc"), ("rc", "-1"), ("re", "nan"),
    ("beta", "0"), ("vbe", "12"),
])
def test_invalid_fields_are_reported(field, value):
    data, errors = parse_bias_input(dict(REFERENCE, **{field: value}))
    assert data is None
    assert field in errors


@pytest.mark.parametrize("field", ["r1", "r2", "rc", "re"])
def test_zero_resistance_is_rejected(field):
    data, errors = parse_bias_input(dict(REFERENCE, **{field: "0"}))
    assert data is None
    assert "greater than zero" in errors[field]


def test_accepts_whitespace_and_scientific_notation():
    data, errors = parse_bias_input(dict(REFERENCE, r1=" 4.7e4 ", beta="1.5e2"))
    assert errors == {}
    assert data.r1 == pytest.approx(47000.0)
    assert data.beta == pytest.approx(150.0)


def test_missing_fields_are_required():
    data, errors = parse_bias_input({})
    assert data is None
    assert set(errors) == set(FIELDS)
    assert all("Required" in message for message in errors.values())


def test_non_finite_input_is_rejected():
    data, errors = parse_bias_input(dict(REFERENCE, vcc="inf"))
    assert data is None
    assert "finite" in errors["vcc"]
```

- [ ] **Step 3: รันเทสให้เห็นว่า fail**

Run: `.venv\Scripts\python -m pytest tests/test_bjt.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'bjt'`

- [ ] **Step 4: สร้าง `bjt.py`**

```python
from dataclasses import dataclass
from math import isfinite
from typing import Mapping

FIELDS = ("vcc", "r1", "r2", "rc", "re", "beta", "vbe")

@dataclass(frozen=True)
class BiasInput:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float


def parse_bias_input(raw: Mapping[str, str]) -> tuple[BiasInput | None, dict[str, str]]:
    """แปลงค่าดิบเป็น BiasInput; คืน (None, errors) เมื่อมีช่องผิด"""
```

กติกาในตัวฟังก์ชัน: ว่าง → `Required`; `float()` ไม่ได้ → `Must be a number`;
`not isfinite` → `Must be a finite number`; `vcc/r1/r2/rc/re <= 0` และ `beta <= 0`
→ `Must be greater than zero`; `vbe <= 0` → `Must be greater than zero`;
`vbe >= vcc` (เมื่อ `vcc` ผ่าน) → `Must be less than VCC` ตรวจทุกฟิลด์แล้วคืน
`(None, errors)` ถ้ามี error อย่างน้อยหนึ่ง

- [ ] **Step 5: รันเทสให้ผ่าน**

Run: `.venv\Scripts\python -m pytest tests/test_bjt.py -v`
Expected: PASS ทั้งหมด

- [ ] **Step 6: Commit**

```powershell
$git = "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
& $git add requirements.txt bjt.py tests/test_bjt.py
& $git commit -m "feat: add BJT input validation"
```

---

### Task 2: Thevenin analysis + region warnings

**Files:**
- Modify: `bjt.py`
- Modify: `tests/test_bjt.py`

**Interfaces:**
- Consumes: `BiasInput`, `parse_bias_input`
- Produces: `VCE_SAT = 0.2`
- Produces: `BiasResult` dataclass (frozen): `ib_a, ic_a, ie_a, vb_v, vc_v, ve_v, vce_v, pc_w: float`; `region: str`; `warnings: tuple[str, ...]`
- Produces: `analyze(data: BiasInput) -> BiasResult` (Thevenin)

- [ ] **Step 1: เขียนเทสที่ยังไม่ผ่าน**

```python
from bjt import VCE_SAT, analyze


def make_input(**overrides):
    raw = dict(REFERENCE, **{key: str(value) for key, value in overrides.items()})
    data, errors = parse_bias_input(raw)
    assert errors == {}
    return data


def test_thevenin_reference_operating_point():
    result = analyze(make_input())
    assert result.region == "active"
    assert result.ib_a == pytest.approx(8.824502e-6, rel=1e-6)
    assert result.ic_a == pytest.approx(1.323675e-3, rel=1e-6)
    assert result.ie_a == pytest.approx(1.332500e-3, rel=1e-6)
    assert result.vb_v == pytest.approx(2.032500, rel=1e-6)
    assert result.vc_v == pytest.approx(9.087914, rel=1e-6)
    assert result.ve_v == pytest.approx(1.332500, rel=1e-6)
    assert result.vce_v == pytest.approx(7.755414, rel=1e-6)
    assert result.pc_w == pytest.approx(10.26565e-3, rel=1e-6)
    assert result.warnings == ()


def test_cutoff_when_base_current_is_not_positive():
    result = analyze(make_input(r2=1000))
    assert result.region == "cutoff"
    assert any("cutoff" in warning.lower() for warning in result.warnings)


def test_saturation_when_vce_at_or_below_vce_sat():
    result = analyze(make_input(rc=10000))
    assert result.region == "saturation"
    assert result.vce_v <= VCE_SAT
    assert any("saturation" in warning.lower() for warning in result.warnings)


def test_warns_when_divider_current_is_small():
    result = analyze(make_input(r1=470000, r2=100000))
    assert result.region == "active"
    assert any("beta" in warning.lower() for warning in result.warnings)


def test_near_cutoff_boundary_does_not_crash():
    result = analyze(make_input(vbe=2.105))
    assert result.region in {"active", "cutoff"}
    assert math.isfinite(result.ib_a)
```

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `.venv\Scripts\python -m pytest tests/test_bjt.py -v -k "thevenin or cutoff or saturation or divider or near"`
Expected: FAIL — `ImportError: cannot import name 'analyze'`

- [ ] **Step 3: เพิ่ม `BiasResult`, `VCE_SAT`, `analyze` ใน `bjt.py`**

สูตร (ตาม spec):

```
vbb = vcc * r2 / (r1 + r2)
rb = r1 * r2 / (r1 + r2)
ib = (vbb - vbe) / (rb + (1 + beta) * re)
ic = beta * ib
ie = (1 + beta) * ib
ve = ie * re
vc = vcc - ic * rc
vce = vc - ve
vb = vbe + ve
pc = vce * ic
```

กติกา region: `ib <= 0` → `"cutoff"`; `vce <= VCE_SAT` → `"saturation"`; ไม่งั้น
`"active"` เตือนเมื่อ `ib <= 0`, เมื่อ `vce <= VCE_SAT`, และเมื่อ
`vcc / (r1 + r2) < 10 * ib` (เฉพาะ `ib > 0`) เก็บเป็น tuple

- [ ] **Step 4: รันเทสให้ผ่าน**

Run: `.venv\Scripts\python -m pytest tests/test_bjt.py -v`
Expected: PASS ทั้งหมด

- [ ] **Step 5: Commit**

```powershell
$git = "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
& $git add bjt.py tests/test_bjt.py
& $git commit -m "feat: analyze CE bias with Thevenin equivalent"
```

---

### Task 3: Flask skeleton, form, validation errors

**Files:**
- Create: `app.py`
- Create: `templates/index.html`
- Create: `static/style.css`
- Create: `tests/test_app.py`

**Interfaces:**
- Consumes: `FIELDS`, `parse_bias_input`
- Produces: `app` (Flask instance), `DEFAULTS: dict[str, str]`
- Produces routes: `GET /` และ `POST /` (ทั้งคู่ render `index.html`)

- [ ] **Step 1: เขียนเทสที่ยังไม่ผ่าน**

```python
import pytest

from app import app

FORM = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    return app.test_client()


def test_get_index_shows_form(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    for field in FORM:
        assert f'name="{field}"' in body


def test_post_invalid_shows_error_and_keeps_value(client):
    response = client.post("/", data=dict(FORM, r2="0"))
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "greater than zero" in body
    assert 'value="0"' in body


def test_html_in_input_is_escaped(client):
    body = client.post("/", data=dict(FORM, r1="<script>")).get_data(as_text=True)
    assert "<script>" not in body
    assert "&lt;script&gt;" in body
```

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `.venv\Scripts\python -m pytest tests/test_app.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: สร้าง `app.py`**

```python
from flask import Flask, render_template, request

from bjt import FIELDS, parse_bias_input

app = Flask(__name__)

DEFAULTS = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "2200",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


@app.get("/")
def index():
    return render_template("index.html", values=DEFAULTS, errors={}, result=None)


@app.post("/")
def calculate():
    values = {field: request.form.get(field, "") for field in FIELDS}
    data, errors = parse_bias_input(values)
    if errors:
        return render_template("index.html", values=values, errors=errors, result=None)
    return render_template("index.html", values=values, errors={}, result=None)
```

- [ ] **Step 4: สร้าง `templates/index.html`**

โครง: `<form method="post" action="/">` มี input `type="text"` `name` ตรงกับ
`FIELDS` และ `value="{{ values[field] }}"` แสดง label หน่วย (V, Ω, V) และ
`<p class="error">{{ errors[field] }}</p>` ใต้ช่องที่มี error ใช้
`<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`

- [ ] **Step 5: สร้าง `static/style.css`**

จัดหน้าให้อ่านง่าย: ตัวอักษร sans-serif, การ์ดกว้างสุด ~720px, ฟอร์มเป็น grid
2 คอลัมน์บนจอใหญ่, `.error` สีแดง, ช่อง input เต็มความกว้าง

- [ ] **Step 6: รันเทสให้ผ่าน**

Run: `.venv\Scripts\python -m pytest tests/test_app.py -v`
Expected: PASS ทั้งหมด

- [ ] **Step 7: Commit**

```powershell
$git = "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
& $git add app.py templates/index.html static/style.css tests/test_app.py
& $git commit -m "feat: add Flask form with server-side validation"
```

---

### Task 4: Operating point and warnings

**Files:**
- Modify: `app.py`
- Modify: `templates/index.html`
- Modify: `static/style.css`
- Modify: `tests/test_app.py`

**Interfaces:**
- Consumes: `analyze`, `BiasResult`
- Produces: `format_current(amperes: float) -> str`, `format_voltage(volts: float) -> str`,
  `format_power(watts: float) -> str` และ Jinja filters ชื่อ `current`, `voltage`, `power`

- [ ] **Step 1: เขียนเทสที่ยังไม่ผ่าน**

```python
from app import format_current, format_power, format_voltage


def test_formatters_pick_units():
    assert format_current(8.824502e-6) == "8.82 µA"
    assert format_current(1.323675e-3) == "1.324 mA"
    assert format_current(2.5) == "2.500 A"
    assert format_voltage(7.755414) == "7.755 V"
    assert format_power(10.2659e-3) == "10.27 mW"


def test_formatters_handle_extreme_magnitudes():
    assert format_current(1e6).endswith(" A")
    assert format_current(1e-9).endswith(" µA")
    assert format_voltage(1e6) == "1000000.000 V"


def test_post_valid_shows_operating_point(client):
    body = client.post("/", data=FORM).get_data(as_text=True)
    assert "Active" in body
    assert "8.82 µA" in body
    assert "1.324 mA" in body
    assert "1.332 mA" in body
    assert "2.032 V" in body
    assert "9.088 V" in body
    assert "7.755 V" in body
    assert "10.27 mW" in body


def test_saturation_region_is_reported(client):
    body = client.post("/", data=dict(FORM, rc="10000")).get_data(as_text=True)
    assert "Saturation" in body
```

- [ ] **Step 2: รันเทสให้เห็นว่า fail**

Run: `.venv\Scripts\python -m pytest tests/test_app.py -v`
Expected: FAIL — `ImportError: cannot import name 'format_current'`

- [ ] **Step 3: เพิ่ม formatter และผูก Jinja filters ใน `app.py`**

```
format_current: |I| < 1e-3 → f"{I*1e6:.2f} µA"; |I| < 1 → f"{I*1e3:.3f} mA"; else f"{I:.3f} A"
format_voltage: f"{V:.3f} V"
format_power:   |P| < 1 → f"{P*1e3:.2f} mW"; else f"{P:.3f} W"
```

ผูกด้วย `app.jinja_env.filters.update(current=..., voltage=..., power=...)`
ใน route `POST /` ที่ผ่าน validation ให้เรียก `analyze(data)` แล้วส่ง
`result=result`

- [ ] **Step 4: แสดงผลใน `templates/index.html`**

เมื่อ `result` ไม่ใช่ `None`: badge ย่านการทำงานด้วย `{{ result.region|title }}`
(class `region-{{ result.region }}`), ตารางค่า `IB, IC, IE, VB, VC, VE, VCE, PC`
ผ่าน filter (`|current`, `|voltage`, `|power`) และรายการ `warnings`

- [ ] **Step 5: เพิ่มสี badge ใน `static/style.css`**

`.region-active` เขียว, `.region-cutoff` เทา, `.region-saturation` ส้ม/แดง
ให้ตัดกันชัดและอ่านออก

- [ ] **Step 6: รันเทสทั้งหมดให้ผ่าน**

Run: `.venv\Scripts\python -m pytest -v`
Expected: PASS ทั้งหมด (รวม `test_electrical.py` เดิม)

- [ ] **Step 7: Commit**

```powershell
$git = "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
& $git add app.py templates/index.html static/style.css tests/test_app.py
& $git commit -m "feat: show bias point and warnings"
```

---

### Task 5: README, full verification, merge and push

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: ทุกอย่างจาก Task 1–5
- Produces: เอกสารวิธีรัน + ประวัติ commit ที่ push ขึ้น GitHub

- [ ] **Step 1: เพิ่มหัวข้อใน `README.md`**

ระบุ: วัตถุประสงค์, วิธีติดตั้ง (`python -m venv .venv`, `pip install -r requirements.txt`),
วิธีรัน (`\.venv\Scripts\python app.py` → `http://127.0.0.1:5000`),
วิธีเทส (`\.venv\Scripts\python -m pytest`), ขอบเขต (ไม่มี AC/transient/FET),
และเคสตัวอย่างพร้อมค่าที่ควรได้

- [ ] **Step 2: รันเทสทั้งหมดและตรวจ smoke test**

Run: `.venv\Scripts\python -m pytest -v`
Expected: PASS ทั้งหมด

Run (background): `.venv\Scripts\python app.py`
แล้ว `Invoke-WebRequest http://127.0.0.1:5000` → `StatusCode 200`
และ POST ฟอร์มด้วย `curl.exe -s -X POST -d "vcc=12&r1=47000&r2=10000&rc=2200&re=1000&beta=150&vbe=0.7" http://127.0.0.1:5000`
Expected: มี `1.324 mA` และ `Active` ในผลลัพธ์ แล้วปิด server

- [ ] **Step 3: Commit เอกสาร**

```powershell
$git = "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
& $git add README.md
& $git commit -m "docs: document CE bias web app"
```

- [ ] **Step 4: Merge เข้า `main` และ push**

```powershell
$git = "$env:LOCALAPPDATA\Programs\Git\cmd\git.exe"
& $git checkout main
& $git merge --ff-only feat/bjt-ce-bias
& $git push origin main
& $git log --oneline -8
```

Expected: push สำเร็จ, `main` มี commit ของงานนี้ครบ, working tree สะอาด

# BJT Bias Modes (Fixed / Emitter) Implementation Plan

**Goal:** เพิ่มโหมด Fixed Bias และ Emitter Bias (แหล่งจ่ายเดียว) ใน Flask app เดิม
โดยผลลัพธ์ของ Voltage Divider ต้องคงเดิมทุกค่า และทุกโหมดคืน dict คีย์/หน่วยชุดเดียวกัน

**Architecture:** คณิตศาสตร์ทั้งหมดอยู่ใน `bjt.py` (ไม่ import Flask) แยกฟังก์ชันตามโหมด
`app.py` ทำหน้าที่เลือกโหมด/ตรวจอินพุต/ส่งผลเข้า template เท่านั้น

**Tech Stack:** Python 3.12, Flask 3.x, pytest 8.x, Jinja2, HTML/CSS (ไม่มี JS)

**Status:** อนุมัติแผน 2026-11-17 — ลงโค้ดแล้ว, refactor routing เป็น if/elif แล้ว, รอตรวจผ่าน Browser ด้วยตารางผู้ใช้

## Global Constraints

- ไม่แก้ `analyze()` และ `parse_bias_input()` ของ Divider (ผลเดิมต้องเท่าเดิมเป๊ะ)
- ไม่แก้ `electrical.py`, `test_electrical.py`
- ไม่สร้าง unittest ใหม่; ชุดเทสเดิม 44 ตัวต้องผ่านทั้งหมด
- อินพุตเป็นหน่วยฐาน (Ω, V) ไม่รองรับ suffix `k`/`µ`
- Result dict ทุกโหมดใช้คีย์: `mode, ib_a, ic_a, ie_a, vb_v, vc_v, ve_v, vce_v, pc_w, region, warnings`
- หน่วย: กระแส A, แรงดัน V, กำลัง W; แปลงหน่วยเฉพาะตอนแสดงผล
- ข้อความ validation ชุดเดิม: `Required`, `Must be a number`, `Must be a finite number`,
  `Must be greater than zero`, `Must be less than VCC`
- Region: `IB ≤ 0` → cutoff, `VCE ≤ 0.2` → saturation, อื่น ๆ → active

## สมการ

Fixed Bias:

```
IB  = (VCC - VBE) / RB
IC  = beta * IB
IE  = (1 + beta) * IB
VB  = VBE
VE  = 0
VC  = VCC - IC * RC
VCE = VC - VE
PC  = VCE * IC
```

Emitter Bias (single supply):

```
IB  = (VCC - VBE) / (RB + (1 + beta) * RE)
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = IE * RE
VC  = VCC - IC * RC
VCE = VC - VE
VB  = VBE + VE
PC  = VCE * IC
```

Divider: คงสูตร Thevenin เดิมทั้งหมด

---

### Task 1: เพิ่มฟังก์ชันคณิตศาสตร์ใน `bjt.py`

**Files:** Modify `bjt.py`

**Interfaces:**
- Produces: `MODES = ("divider", "fixed", "emitter")`
- Produces: `MODE_FIELDS` (ฟิลด์ที่ต้องกรอกต่อโหมด)
- Produces: `FixedBiasInput`, `EmitterBiasInput`
- Produces: `parse_mode_input(mode, raw) -> (data | None, errors)`
- Produces: `analyze_fixed(data) -> dict`, `analyze_emitter(data) -> dict`
- Produces: `analyze_mode(mode, data) -> dict`
- Keeps: `BiasInput`, `BiasResult`, `parse_bias_input`, `analyze`

- [x] เพิ่ม dataclass และตัวตรวจอินพุตร่วม `_parse_mode_values`
- [x] Divider ใน `parse_mode_input` ส่งต่อไป `parse_bias_input` ตัวเดิม
- [x] เพิ่ม `_result_dict` และ `_classify` ให้คีย์/ข้อความตรงกันทุกโหมด
- [x] `analyze_mode` แปลง `BiasResult` ของ Divider เป็น dict โดยไม่แก้สูตร
- [x] รัน `.venv\Scripts\python -m pytest -q` → 44 passed

### Task 2: เลือกโหมดและตรวจอินพุตใน `app.py`

**Files:** Modify `app.py`

**Interfaces:**
- Consumes: `MODES`, `parse_mode_input`, `analyze_mode`
- Produces: `MODE_LABELS`, `MODE_DESCRIPTIONS`, `FIELD_META`, `DEFAULTS` แยกตามโหมด
- Produces: `CIRCUIT_TEMPLATES` สำหรับ include SVG ตามโหมด
- Routes: `GET /?mode=...`, `POST /` (ซ่อน `mode` ในฟอร์ม)

- [x] `_mode_from` fallback เป็น `divider` เมื่อไม่ส่ง `mode` หรือค่าไม่รู้จัก
- [x] `GET /` ใช้ default ของโหมดนั้น
- [x] `POST /` ตรวจเฉพาะฟิลด์ของโหมด และส่ง dict ผลลัพธ์เข้า template
- [x] คง Jinja filters `current`, `voltage`, `power` เดิม

### Task 3: UI หลายโหมด

**Files:**
- Modify `templates/index.html`
- Create `templates/_circuit_fixed.svg`
- Create `templates/_circuit_emitter.svg`
- Modify `static/style.css`

- [x] แท็บโหมดเป็นลิงก์ `?mode=...` (ไม่เพิ่ม JS)
- [x] ฟอร์มสร้างจาก `field_meta` ของโหมด + hidden `mode`
- [x] ผลลัพธ์อ่านจาก dict (`result['ib_a']` ฯลฯ) ผ่าน filter เดิม
- [x] ไดอะแกรม Fixed Bias และ Emitter Bias แยกไฟล์
- [x] สไตล์ `.mode-tabs` / `.mode-tab.active`

### Task 4: เอกสาร

- [x] อัปเดต `README.md` (โหมด, ฟิลด์, ตัวอย่างค่าทั้ง 3 โหมด)

### Task 5: ตรวจรับ

- [x] `.venv\Scripts\python -m pytest -q` → 44 passed
- [x] ตรวจด้วย Flask test client: GET/POST ทั้ง 3 โหมด ตอบ 200, validation ทำงาน
- [x] ตรวจ numerically ว่า Divider ค่าเดิมเท่ากับ `analyze()` ทุกคีย์
- [ ] ตรวจผ่าน Browser เทียบค่ากับตารางของผู้ใช้ทีละแถว
- [ ] เปิด fixed/emitter แล้วเทียบ `VB, VE, VC, VCE, IB, IC, IE, PC`

### Task 6: Refactor routing เป็น if/elif (คำขอผู้ใช้ 2026-11-17)

**Files:** Modify `app.py`, `templates/index.html`, `tests/test_app.py`, `README.md`

- [x] เพิ่ม `DIVIDER_FIELDS` / `FIXED_FIELDS` / `EMITTER_FIELDS` และ `_read_form()`
- [x] `GET /` และ `POST /` ใช้ `if/elif` ตาม `mode` ที่เลือก แทนการ index ตาราง `FIELD_META[mode]`
- [x] `bjt.py` ไม่แก้; Divider ยังใช้ `parse_bias_input` + สูตร Thevenin เดิม
- [x] Footer เปลี่ยน `Week 2 Goal` → `Week 3 Goal`; อัปเดต assertion ใน `test_layout_has_three_panels_and_goal_bar`
- [x] `.venv\Scripts\python -m pytest -q` → 44 passed

## Acceptance
- Divider แสดง `IB=8.82 µA, IC=1.324 mA, IE=1.332 mA, VB=2.032 V, VC=9.088 V, VE=1.332 V, VCE=7.755 V`
- Fixed ด้วย `VCC=12, RB=470000, RC=2200, β=150, VBE=0.7` → `IB=24.04 µA, IC=3.606 mA, VCE=4.066 V`
- Emitter ด้วย `VCC=12, RB=470000, RC=2200, RE=1000, β=150, VBE=0.7` → `IB=18.20 µA, IC=2.729 mA, VCE=3.248 V`
- เทสเดิมทั้ง 44 ตัวยังผ่าน โดยไม่มีเทสใหม่

# Lab 03 · A1–A5 Browser Validation

อินพุตร่วมทุกกรณี (ตามใบงาน): `VCC = 12 V`, `RC = 2.2 kΩ = 2200 Ω`, `β = 100`, `VBE = 0.70 V`

หน้าฟอร์มรับหน่วย **Ω** และ **V** จึงป้อน `100 kΩ` เป็น `100000`, `1 MΩ` เป็น `1000000` เป็นต้น

เกณฑ์เทียบผล (ตามใบงาน): `|ΔIC| ≤ 0.01 mA` และ `|ΔVCE| ≤ 0.02 V` เมื่อเทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ

แหล่งกรณีทดสอบ: `ENG29_2121_Lab03_BJT_Bias_Web_App.html` section 06
URL ที่ตรวจ: `http://127.0.0.1:5000/`

## ค่าคาดหมายอิสระ (คำนวณจากสมการในใบงาน ไม่ได้อ่านจากโค้ดที่ตรวจ)

สมการที่ใช้:

```
Fixed   IB = (VCC - VBE) / RB
Emitter IB = (VCC - VBE) / [RB + (β + 1)RE]
Divider IB = (VTH - VBE) / [RTH + (β + 1)RE]
             VTH = VCC·R2/(R1+R2) = 2.163934 V
             RTH = R1·R2/(R1+R2) = 18032.7869 Ω
ร่วม     IC = β·IB,  IE = (β+1)IB,  VE = IE·RE (Fixed ใช้ VE = 0)
         VC = VCC - IC·RC,  VCE = VC - VE
```

| กรณี | IB (อ้างอิง) | IC (อ้างอิง) | VCE (อ้างอิง) |
|---|---|---|---|
| A1 Divider | 12.2986 µA | **1.22986 mA** | **8.05216 V** |
| A2 Fixed | 11.3000 µA | **1.13000 mA** | **9.51400 V** |
| A3 Emitter RE=1 kΩ | 10.2634 µA | **1.02634 mA** | **8.70545 V** |
| A4 Emitter RE=2 kΩ | 9.4010 µA | **0.94010 mA** | **8.03278 V** |

**ทำนาย A4 ก่อนรัน:** `IC` ต้อง **ลดลง** จาก A3 เพราะตัวหาร `(RB + (β+1)RE)` เพิ่มจาก `1,101,000 Ω` เป็น `1,202,000 Ω` ทำให้ `IB` ลดลง

## ตารางผล

| กรณี | เลือกโหมดและกรอกค่า | คาดหมายก่อนรัน | เห็นจริง | วิธีตรวจ | สถานะ | หลักฐาน |
|---|---|---|---|---|---|---|
| **A1 · โหมดเดิม** | Divider · `R1=100000 Ω`, `R2=22000 Ω`, `RE=1000 Ω` | ตรงกับ Lab 2 ก่อนแก้ · `IC ≈ 1.22986 mA`, `VCE ≈ 8.05216 V` | `IC = 1.230 mA`, `VCE = 8.052 V`, `IB = 12.30 µA` · Active | Playwright MCP | **PASS** | `docs/evidence/A1-divider.yml` |
| **A2 · Fixed** | Fixed · `RB=1000000 Ω` (ไม่มีช่อง RE) | คำนวณได้โดยไม่กรอก RE · `IC ≈ 1.13000 mA`, `VCE ≈ 9.51400 V`, `VE = 0.000 V` | `IC = 1.130 mA`, `VCE = 9.514 V`, `VE = 0.000 V`, `IB = 11.30 µA` · ฟอร์มไม่มีช่อง RE | Playwright MCP | **PASS** | `docs/evidence/A2-fixed.yml`, `docs/evidence/A2-fixed-form.yml` |
| **A3 · Emitter** | Emitter · `RB=1000000 Ω`, `RE=1000 Ω` | มีช่อง RE และใช้ค่า RE · `IC ≈ 1.02634 mA`, `VCE ≈ 8.70545 V` | `IC = 1.026 mA`, `VCE = 8.705 V`, `VE = 1.037 V`, `IB = 10.26 µA` · มีช่อง RE | Playwright MCP | **PASS** | `docs/evidence/A3-emitter.yml`, `docs/evidence/A3-emitter-form.yml` |
| **A4 · เปลี่ยนค่าเดียว** | Emitter · เหมือน A3 เปลี่ยนเฉพาะ `RE=2000 Ω` | `IC` ลดลงจาก A3 · `IC ≈ 0.94010 mA`, `VCE ≈ 8.03278 V` | `IC = 940.10 µA (= 0.94010 mA)`, `VCE = 8.033 V`, `IB = 9.40 µA` · `IC` ลดลงจาก 1.026 mA ตามที่ทำนาย | Playwright MCP | **PASS** | `docs/evidence/A4-emitter-re2k.yml` |
| **A5 · อินพุตผิด** | Fixed · `RB=0 Ω` | ข้อความให้แก้ RB, เว็บไม่ล่ม, ไม่แสดงผลเดิมเป็นผลรอบนี้ | ข้อความ `Must be greater than zero` ใต้ช่อง `RB (Ω)`; ผลแสดง `Enter parameters and press Calculate DC Bias` ไม่มีผลคำนวณค้าง · เว็บไม่ล่ม | Playwright MCP | **PASS** | `docs/evidence/A5-fixed-rb0-final.yml`, `docs/evidence/A5-fixed-rb0.png` |

## สรุปการเทียบผล (เทียบกับค่าอ้างอิงที่ยังไม่ปัดเศษ)

| กรณี | ΔIC | เกณฑ์ 0.01 mA | ΔVCE | เกณฑ์ 0.02 V |
|---|---|---|---|---|
| A1 | 0.00014 mA | ผ่าน | 0.00016 V | ผ่าน |
| A2 | 0.00000 mA | ผ่าน | 0.00000 V | ผ่าน |
| A3 | 0.00034 mA | ผ่าน | 0.00045 V | ผ่าน |
| A4 | 0.00000 mA | ผ่าน | 0.00022 V | ผ่าน |

**ผลรวม: A1–A5 PASS ทั้ง 5 กรณี** ด้วยวิธี Playwright MCP (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill_form`) อ่านค่าจากหน้าเว็บหลังกดปุ่มคำนวณทุกครั้ง

## หมายเหตุ

- A1 ใช้สมการ Thevenin เดิมของ Lab 2 เป็นค่าอ้างอิง ผลที่ได้ตรงกับค่าอ้างอิงเดิมทุกตัว
- A5 ข้อความ `Must be greater than zero` แสดงใต้ช่อง `RB (Ω)` ในฟอร์ม (มาจาก Flask ผ่าน Jinja) และผลคำนวณถูกล้าง ไม่มีผลของรอบก่อนค้างอยู่
- A4 เว็บแสดง `IC = 940.10 µA` แทน `0.940 mA` เพราะตัวจัดรูปแบบสลับหน่วยเมื่อค่าต่ำกว่า 1 mA; ค่าเทียบได้ `0.94010 mA` ตรงตามที่คาดหมาย ควรปรึกษา TA ว่าต้องการให้แสดงเป็น mA เสมอหรือไม่
- Console ของ Chrome มีข้อความ error 1 รายการ: `404 /favicon.ico` ไม่ส่งผลต่อการคำนวณหรือผล A1–A5
- ผลที่บันทึกอ่านจาก snapshot ของหน้าเว็บหลังกดคำนวณ ไม่ใช้ HTTP request หรือการอ่านโค้ดแทน
- ไม่มีการแก้ไฟล์โปรแกรมระหว่างรอบตรวจนี้

---

# Lab 04 · B1–B8 Browser Validation (BJT Amplifier Simulator v1)

## Tooling and honesty statement

- **Playwright MCP was not exposed in this harness.** No `browser_navigate` / `browser_snapshot` /
  `browser_click` MCP tools were available. Navigation, mode selection, field entry, form
  submission and DOM assertions were performed with the in-app browser (OpenCode desktop Review
  pane). Screenshots were captured with `impeccable shot --viewport 1280x900` and
  `--viewport 390x844`. No Playwright MCP PASS is claimed.
- Server under test: `http://127.0.0.1:5001` (Flask), started with
  `NGSPICE_EXECUTABLE` pointing at the downloaded ngspice 47 executable. Port 5000 was occupied by
  a separate app in another directory and was not used.
- Reference fixture: `VCC=12 V`, `R1=100 kΩ`, `R2=22 kΩ`, `RC=2.2 kΩ`, `RE=1 kΩ`, `RL=10 kΩ`,
  `Cin=Cout=10 µF`, SIN 10 mV peak at 1 kHz, no bypass capacitor.
- SPICE model: `.model QGEN NPN` — ngspice generic built-in defaults, explicitly labelled
  **generic, NOT instructor-verified**. β / VBE fields are analytical-reference assumptions only
  and do not change the SPICE model.
- Full observed-value log: [`docs/evidence/L4-browser-results.md`](evidence/L4-browser-results.md).

## B1–B8 results

| Case | Check | Observed (units) | Status | Evidence |
|---|---|---|---|---|
| **B1** | Lab 3 regression: Divider / Fixed / Emitter | Divider `IC=1.324 mA, VCE=7.755 V`; Fixed `3.606 mA, 4.066 V`; Emitter `2.729 mA, 3.248 V`; all Active | **PASS** | `L4-browser-results.md` |
| **B2** | CE DC `.op` | `VB=1.954 V, VE=1.176 V, VC=9.439 V, VCE=8.263 V, IC=1.164 mA`, Active; `Success · real ngspice run` | **PASS** | `L4-after-desktop-dc.png` |
| **B3** | Change only RE `1 kΩ → 2 kΩ`, re-run | `VB=2.049 V, VE=1.287 V, VC=10.599 V, VCE=9.312 V, IC=636.89 µA`; values changed from B2 | **PASS** | `L4-browser-results.md` |
| **B4** | AC `.ac` Bode plot | 201 points per trace; gain `4.726377 dB` at 10 Hz, `4.846087 dB` at 1 kHz; phase `−166.648°` at 10 Hz, `−179.866°` at 1 kHz; cutoff `not determined in sweep range` | **PASS** | `L4-after-desktop-ac.png` |
| **B5** | Transient `.tran`, 10 mV peak / 1 kHz | 1008 points; `Vin peak=0.010 V`, `Vout peak=0.017 V`, phase inversion **Yes**, time window 0–5 ms | **PASS** | `L4-after-desktop-tran.png` |
| **B6** | Change amplitude `0.01→0.02 V` and frequency `1→2 kHz` | `Vin peak=0.020 V`, `Vout peak=0.035 V`, inversion Yes, time ticks 0–2.50 ms | **PASS** | `L4-browser-results.md` |
| **B7** | Invalid `RE=0`; unavailable engine | Invalid: `Must be greater than zero`, `Error · validation`, 0 plots, no stale result. Missing engine: `Error · engine`, `ngspice executable not found...`, 0 plots | **PASS** | `L4-after-invalid-re.png`, `L4-after-engine-error.png` |
| **B8** | Desktop 1280×900, mobile 390×844, mode switching | Desktop three-column input/results layout; mobile single-column inputs and scrollable plots; DC → AC → Transient each rendered its own panel | **PASS** with tooling caveat | `L4-after-desktop-*.png`, `L4-after-mobile-*.png` |

## Analytical `bjt.py` vs SPICE `.op`

`bjt.py` divider reference with β = 100 and VBE = 0.70 V (the same assumptions shown in the UI):

| Quantity | Analytical `bjt.py` | ngspice `.op` | Difference |
|---|---|---|---|
| VB | 1.942 V | 1.954 V | +0.012 V |
| VE | 1.242 V | 1.176 V | −0.066 V |
| VCE | 8.052 V | 8.263 V | +0.211 V |
| IC | 1.230 mA | 1.164 mA | −0.066 mA (−5.4 %) |

The two results are intentionally not forced to agree. `bjt.py` uses a fixed-VBE Thevenin hand
model; ngspice uses the generic NPN model with its own exponential junction equations. The UI keeps
the analytical DC reference in a separate card labelled **NOT ngspice**.

## Discrepancies and limitations

- **Generic model, not instructor-verified.** No instructor starter kit or model line was present
  in the repository, history, Downloads or Documents. The chosen `.model QGEN NPN` is ngspice's
  built-in generic model (`BF=100`, `IS=1e-16` defaults). A student must confirm with the instructor
  whether this is acceptable for Lab 4.
- **No junction capacitances in the generic model.** The AC gain is flat across 10 Hz–1 MHz, so no
  −3 dB point exists in the sweep and the UI correctly prints `not determined in sweep range`. The
  low-frequency coupling-capacitor corner is below the 10 Hz sweep start.
- **IC is derived**, not probed directly: `IC = (VCC − VC) / RC` from the simulated collector node
  and the specified RC. In this topology that is the collector-branch current.
- **DC parsing uses the `.op` node-voltage table.** `.print op` produced ngspice warnings, so it is
  not used.
- **Phase units were corrected.** ngspice `vp()` returns radians; `parse_ac` converts to degrees
  before plotting. The transient inversion flag independently agrees (Yes).
- **ngspice pagination was corrected.** ngspice repeats its `Index` header every ~60 rows; the
  parser now continues across pages, yielding 201 AC points and 1008 transient points instead of
  the first 55 rows.
- ngspice 47 was downloaded from SourceForge and used from a temporary directory for this session;
  no temporary engine path is committed. Setup is documented in `README.md`.
- The browser console has a harmless `404 /favicon.ico`, inherited from the Lab 3 app.

## Impeccable UI review

- Assessment A (design review) was started in a separate sub-agent but the provider usage limit was
  reached; it was completed inline and the critique is therefore **degraded single-context**.
  Assessment B's detector ran on `templates/simulator.html`: **0 findings**, with a warning that
  Jinja `url_for()` stylesheet links could not be resolved, so color/custom-property coverage was
  incomplete. The detector was re-run after the polish and again returned `[]` with the same
  stylesheet-resolution warning. Its browser step was blocked by `[browser.disconnected]`; the
  parent in-app browser supplied the browser evidence.
- Before-state problems: plot legends and cutoff notes were drawn inside the plotting area and
  collided with traces; phase was labelled degrees while ngspice returned radians; the transient
  parser stopped at the first ngspice page (55 of 1008 points); circuit labels collided with wires;
  a six-field group exceeded the ≤4-item chunking guideline; mobile used cramped two-column fields;
  the missing-engine POST showed only a generic warning instead of the actual engine error.
- After-state fixes (UI-only except parser/unit corrections): legends moved outside the plot area
  with line swatches and dashed phase; three gain/phase axis ticks; `peak −3 dB` reference line;
  capacitors hint `10e-6 = 10 µF`; fields split into `Supply & divider`, `Collector/emitter/load`,
  capacitors, source and analytical assumptions; single-column fields below 576 px; scroll hint
  for wide plots; circuit-label halo; `role="status" aria-live="polite"`; running button label;
  engine error now shown explicitly.
- Before/after captures:
  - Before: `L4-before-desktop.png`, `L4-before-ac.png`, `L4-before-tran.png`, `L4-before-mobile.png`
  - After: `L4-after-desktop-dc.png`, `L4-after-desktop-ac.png`, `L4-after-desktop-tran.png`,
    `L4-after-mobile-ac.png`, `L4-after-mobile-tran.png`
  - Errors: `L4-after-invalid-re.png`, `L4-after-engine-error.png`

## What AI built vs what the student must verify

**AI built:** the ngspice adapter (`spice_engine.py`), validation/netlist builder, paginated-log
parsers, Flask `/simulator` route, separated template/circuit SVG, SVG plot renderers, CSS polish,
automated tests, README/validation documentation and the screenshots above. Lab 3 files, routes and
tests were left in place.

**Student must verify:** the generic model is acceptable to the instructor; ngspice is installed
and reports the expected version on the student's machine; B1–B8 still pass locally; the observed
DC/AC/transient values match the Lab 4 handout or TA reference; and the screenshots reflect the
student's own environment. Do not treat the generic model as device-accurate.

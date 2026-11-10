# BJT Common-Emitter DC Bias Web App — Design

- วันที่: 2026-11-10
- สถานะ: อนุมัติแล้ว (UI 3 คอลัมน์ + ไดอะแกรม + Week 2 Goal)
- บริบท: แล็บรายวิชา ENG29 2121 (repo `Girlab`)

## ทำไม / เจตนา

นักศึกษาต้องการสาธิตเว็บแอป Flask จริงที่คำนวณจุดทำงาน DC ของวงจรไบอัส BJT
แบบ common-emitter (voltage-divider bias) ได้ถูกต้อง รวดเร็ว และตรวจสอบผลได้
ด้วยค่าอ้างอิงคำนวณมือ ใช้ประกอบการส่งแล็บและเดโมบนเครื่องตัวเอง

## เป้าหมาย

- รับค่า `VCC, R1, R2, RC, RE, β, VBE`
- แสดง `VB, VE, VC, VCE, IB, IC, IE` (และ `PC` เป็นบรรทัดเสริม) พร้อมหน่วย
- UI 3 คอลัมน์: ซ้าย Input, กลาง Circuit Diagram, ขวา Results & Status
- กล่องสถานะย่านการทำงาน เช่น "Active region approximation OK"
- แถบล่างแสดง "Week 2 Goal"
- ตรวจสอบอินพุตฝั่ง server และเตือนย่านการทำงาน
- ตรวจสอบความถูกต้องด้วยค่าอ้างอิงที่คำนวณมือในชุดเทส
- แยก engineering logic / routes / templates / CSS / tests ออกจากกัน
- รัน `python app.py` ที่ `http://127.0.0.1:5000`
- เทสอัตโนมัติเขียวทั้งหมด

## ไม่ทำ (non-goals)

- AC analysis, transient, กราฟ/plot
- ตัวแก้ไขวงจร, หลายทรานซิสเตอร์
- FET/MOSFET
- login, ฐานข้อมูล, ประวัติการคำนวณ
- deploy ขึ้น cloud
- JS framework, การ parse หน่วยแบบ `47k` / `µF`
- nodal solver หรือตารางเทียบสองวิธีในแอป

## Anti-goals

- ตัวเลขไม่ตรงกับค่าอ้างอิงคำนวณมือ
- ต้องใช้ JavaScript หรืออินเทอร์เน็ตถึงจะเห็นผล
- ขยาย scope เกินเนื้อหาแล็บ
- เทส flaky

## ข้อจำกัด

- Python 3.12.7; Flask และ pytest ยังไม่ติดตั้ง → สร้าง venv + `requirements.txt`
- Git ติดตั้งที่ `%LOCALAPPDATA%\Programs\Git\cmd\git.exe` ไม่อยู่ใน PATH
- ต้องส่งวันนี้: เดโมบน localhost + commit ขึ้น GitHub
- Remote: `github.com/jongpongkeaw-ai/Girlab.git`; `main` สะอาด
- ของเดิม `electrical.py` และ `test_electrical.py` ต้องไม่พัง
- เดโมต้องทำงานได้แม้ไม่มีอินเทอร์เน็ต → vendor Bootstrap CSS ไว้ใน repo

## ทางเลือกที่พิจารณา

1. **หน้าเดียว server-rendered — เลือก**: `GET /` ฟอร์ม, `POST /` คำนวณและแสดงผล,
   Jinja + CSS ไม่มี JS ชิ้นส่วนน้อยสุด เทสด้วย Flask test client ได้ตรง
2. **JSON API + JS fetch — ไม่เลือก**: สัญญา API ชัดกว่า แต่ต้องเทสฝั่ง JS เพิ่ม
   และไม่ได้ประโยชน์กับแล็บนี้
3. **HTMX partial — ไม่เลือก**: ได้ interactivity เล็กน้อย แต่เพิ่ม dependency/CDN
   โดยไม่จำเป็น

การตรวจสอบอิสระ: ใช้ **ค่าอ้างอิงคำนวณมือ** ฝังในเทส ไม่ทำ solver ที่สองในแอป
— scope เล็กลงและยังพิสูจน์ความถูกต้องของสูตรได้

UI framework: เลือก **Bootstrap 5.3 (CSS เท่านั้น) + custom CSS เล็กน้อย**
เพราะได้ grid 3 คอลัมน์และการ์ดที่พร้อมใช้โดยไม่ต้องมี build step;
**vendor ไฟล์ CSS ไว้ใน `static/vendor/`** เพื่อให้เดโมออฟไลน์ได้
(ไม่เลือก Tailwind เพราะ Play CDN ต้องต่อเน็ตและไม่เหมาะกับงานส่งแล็บ)

## การตัดสินใจ

### โครงสร้างไฟล์

```
app.py                          Flask routes เท่านั้น (ไม่มีสูตร)
bjt.py                          ฟังก์ชันวิศวกรรม (ไม่ import Flask)
templates/index.html            3-column layout + ฟอร์ม + ผลลัพธ์
templates/_circuit.svg          ไดอะแกรมวงจรแบบ inline SVG
static/style.css                custom CSS ทับ Bootstrap
static/vendor/bootstrap.min.css Bootstrap 5.3 CSS (vendored)
tests/test_bjt.py               สูตร, validation, region
tests/test_app.py               route + UI tests
requirements.txt
docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md
```

`electrical.py` และ `test_electrical.py` ไม่ถูกแก้ไข

### สูตรหลัก (Thevenin equivalent)

```
VBB = VCC * R2 / (R1 + R2)
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (1 + beta) * RE)
IC  = beta * IB
IE  = (1 + beta) * IB
VE  = IE * RE
VC  = VCC - IC * RC
VCE = VC - VE
VB  = VBE + VE
PC  = VCE * IC
```

### การตรวจสอบอิสระ

ค่าอ้างอิงจากเคสคำนวณมือด้านล่างถูกฝังในเทสและต้องตรงภายใน relative `1e-6`
ไม่มี solver ที่สองหรือตารางเปรียบเทียบในแอป

### การแสดงย่านการทำงาน (linear model + warning)

- `IB <= 0` → **Cutoff**
- `VCE <= 0.2 V` → **Saturation** (โมเดลเชิงเส้นใช้ไม่ได้)
- อื่น ๆ → **Active**
- เตือนเพิ่มถ้ากระแสใน divider (`VCC / (R1 + R2)`) น้อยกว่า `10 * IB`
  ("ไบอัสขึ้นกับ β มาก")
- แสดงตัวเลขที่คำนวณได้เสมอ ไม่ clamp

ข้อความในกล่องสถานะ:

| region | ข้อความ |
|---|---|
| active | `Active region approximation OK` |
| cutoff | `Cutoff region — base current is zero or negative` |
| saturation | `Saturation region — linear model is not valid (VCE ≤ 0.2 V)` |

### Validation

- ทุกค่าเป็นตัวเลข finite
- `VCC > 0`, `R1, R2, RC, RE > 0`, `beta > 0`, `0 < VBE < VCC`
- แสดง error รายช่อง คงค่าที่ผู้ใช้กรอกไว้
- ตรวจฝั่ง server เป็นหลัก; HTML attributes เป็นเพียงความสะดวก

### หน้าจอ (3 คอลัมน์ + แถบล่าง)

```
┌ ENG29 2121 · BJT CE Bias Calculator ─────────────────────────────────┐
│ ┌──────────────┐ ┌──────────────────┐ ┌───────────────────────────┐  │
│ │ INPUT        │ │ CIRCUIT DIAGRAM  │ │ DC BIAS RESULTS           │  │
│ │ VCC   [12] V │ │       VCC        │ │ ┌───────────────────────┐ │  │
│ │ R1 [47000] Ω │ │        │         │ │ │ ● Active region       │ │  │
│ │ R2 [10000] Ω │ │   R1───┼───RC    │ │ │   approximation OK    │ │  │
│ │ RC  [2200] Ω │ │        │    │    │ │ └───────────────────────┘ │  │
│ │ RE  [1000] Ω │ │        B    C    │ │ VB   2.032 V              │  │
│ │ β     [150]  │ │        │   ╱     │ │ VE   1.332 V              │  │
│ │ VBE   [0.7] V│ │   R2───┼──╱      │ │ VC   9.088 V              │  │
│ │              │ │        │  ╲      │ │ VCE  7.755 V              │  │
│ │ [Calculate]  │ │       GND RE    │ │ IB   8.82 µA   IC 1.324 mA│  │
│ └──────────────┘ └──────────────────┘ │ IE   1.332 mA             │  │
│                                       └───────────────────────────┘  │
├──────────────────────────────────────────────────────────────────────┤
│ Week 2 Goal: Analyze and verify the DC operating point of a         │
│ voltage-divider biased common-emitter amplifier.                    │
└──────────────────────────────────────────────────────────────────────┘
```

- Bootstrap grid: `col-lg-4` สามคอลัมน์, ซ้อนแนวตั้งบนจอเล็ก
- ไดอะแกรมเป็น inline SVG (ไม่ใช้รูปภายนอก) มี label `VCC, R1, R2, RC, RE, B, C, E, GND`
- อินพุตเป็นหน่วยฐาน (Ω, V) ตัวเลขล้วน

### เคสอ้างอิงคำนวณมือ

`VCC=12, R1=47000, R2=10000, RC=2200, RE=1000, beta=150, VBE=0.7`

```
VBB = 2.10526 V     RB = 8245.61 Ω
IB  = 8.8245 µA     IC = 1.32367 mA    IE = 1.33249 mA
VB  = 2.0325 V      VC = 9.08792 V     VE = 1.33249 V
VCE = 7.75543 V     PC = 10.266 mW     Region = Active
```

### เทส

- เคสอ้างอิงข้างต้น (ค่าตัวเลขตรง)
- validation: ค่าติดลบ, ศูนย์, non-finite, `VBE >= VCC`, `beta <= 0`
- cutoff: `VBB < VBE`
- saturation: `VCE < 0.2 V`
- route: `GET /` 200 มีฟอร์ม, `POST /` ค่าถูกต้องแสดงผล, `POST /` ค่าไม่ถูกต้องแสดง error
- UI: มี 3 panel (`input-panel`, `circuit-panel`, `results-panel`), มี `<svg>`,
  มีลิงก์ Bootstrap ที่เสิร์ฟจาก local, มีข้อความ `Week 2 Goal`
- กล่องสถานะ: active แสดง `Active region approximation OK`, saturation แสดงข้อความ saturation
- ค่าตรงกับเคสอ้างอิงคำนวณมือภายใน `1e-6` (relative)

### Git

- branch `feat/bjt-ce-bias`
- commit แยกตามงานย่อย
- merge เข้า `main` แล้ว push ขึ้น GitHub

## สิ่งที่เหลือให้ผู้สร้างตัดสิน

- รายละเอียดเส้นและตำแหน่งใน SVG
- ระยะห่าง/สีของ custom CSS ทับ Bootstrap
- ข้อความ error ที่แน่นอน
- ชื่อเทสและโครงสร้าง helper
- พอร์ต (ค่าเริ่มต้น 5000)

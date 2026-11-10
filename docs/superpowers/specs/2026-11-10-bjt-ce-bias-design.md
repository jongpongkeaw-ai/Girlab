# BJT Common-Emitter DC Bias Web App — Design

- วันที่: 2026-11-10
- สถานะ: อนุมัติแล้ว
- บริบท: แล็บรายวิชา ENG29 2121 (repo `Girlab`)

## ทำไม / เจตนา

นักศึกษาต้องการสาธิตเว็บแอป Flask จริงที่คำนวณจุดทำงาน DC ของวงจรไบอัส BJT
แบบ common-emitter (voltage-divider bias) ได้ถูกต้อง รวดเร็ว และตรวจสอบผลได้
ด้วยการคำนวณวิศวกรรมอีกวิธีหนึ่ง ใช้ประกอบการส่งแล็บและเดโมบนเครื่องตัวเอง

## เป้าหมาย

- รับค่า `VCC, R1, R2, RC, RE, β, VBE`
- แสดง `IB, IC, IE, VB, VC, VE, VCE, PC` พร้อมหน่วย
- ตรวจสอบอินพุตฝั่ง server และเตือนย่านการทำงาน
- เทียบผลกับวิธีคำนวณอิสระ (nodal analysis) พร้อมผลต่าง
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

## Anti-goals

- ตัวเลขไม่ตรงกับการคำนวณมือ
- สองวิธีไม่ตรงกันแต่แอปบอกว่าผ่าน
- ต้องใช้ JavaScript ถึงจะเห็นผล
- ขยาย scope เกินเนื้อหาแล็บ
- เทส flaky หรือต้องใช้ network

## ข้อจำกัด

- Python 3.12.7; Flask และ pytest ยังไม่ติดตั้ง → สร้าง venv + `requirements.txt`
- Git ติดตั้งที่ `%LOCALAPPDATA%\Programs\Git\cmd\git.exe` ไม่อยู่ใน PATH
- ต้องส่งวันนี้: เดโมบน localhost + commit ขึ้น GitHub
- Remote: `github.com/jongpongkeaw-ai/Girlab.git`; `main` สะอาด
- ของเดิม `electrical.py` และ `test_electrical.py` ต้องไม่พัง

## ทางเลือกที่พิจารณา

1. **หน้าเดียว server-rendered — เลือก**: `GET /` ฟอร์ม, `POST /` คำนวณและแสดงผล,
   Jinja + CSS ไม่มี JS ชิ้นส่วนน้อยสุด เทสด้วย Flask test client ได้ตรง
2. **JSON API + JS fetch — ไม่เลือก**: สัญญา API ชัดกว่า แต่ต้องเทสฝั่ง JS เพิ่ม
   และไม่ได้ประโยชน์กับแล็บนี้
3. **HTMX partial — ไม่เลือก**: ได้ interactivity เล็กน้อย แต่เพิ่ม dependency/CDN
   โดยไม่จำเป็น

การคำนวณอิสระ: เลือก **nodal analysis + Gaussian elimination** (pure Python)
แทนการ hardcode ค่าอ้างอิงหรือพึ่ง SPICE เพราะเป็นวิธีที่ต่างจริงและตรวจย้อนได้

## การตัดสินใจ

### โครงสร้างไฟล์

```
app.py                  Flask routes เท่านั้น (ไม่มีสูตร)
bjt.py                  ฟังก์ชันวิศวกรรม (ไม่ import Flask)
templates/index.html    ฟอร์ม + ผลลัพธ์
static/style.css
tests/test_bjt.py       สูตร, validation, region
tests/test_app.py       route tests
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

### วิธีอิสระ (nodal analysis)

ตั้ง KCL ที่โหนด B, C, E โดยถือ BJT เป็น current-controlled current source
(`IC = β·IB`, `IE = (1+β)·IB`) และ `VB − VE = VBE` แล้วแก้ระบบเชิงเส้น
ด้วย Gaussian elimination แบบ partial pivoting ที่เขียนเองใน pure Python
ไม่เพิ่ม dependency

### การแสดงย่านการทำงาน (แบบ A: linear model + warning)

- `IB <= 0` → **Cutoff**
- `VCE <= 0.2 V` → **Saturation** (โมเดลเชิงเส้นใช้ไม่ได้)
- อื่น ๆ → **Active**
- เตือนเพิ่มถ้ากระแสใน divider (`VCC / (R1 + R2)`) น้อยกว่า `10 * IB`
  ("ไบอัสขึ้นกับ β มาก")
- แสดงตัวเลขที่คำนวณได้เสมอ ไม่ clamp

### Validation

- ทุกค่าเป็นตัวเลข finite
- `VCC > 0`, `R1, R2, RC, RE > 0`, `beta > 0`, `0 < VBE < VCC`
- แสดง error รายช่อง คงค่าที่ผู้ใช้กรอกไว้
- ตรวจฝั่ง server เป็นหลัก; HTML attributes เป็นเพียงความสะดวก

### หน้าจอ

```
┌ ENG29 2121 · CE Bias Calculator ──────────────────────┐
│ VCC [12] V   R1 [47000] Ω  R2 [10000] Ω               │
│ RC [2200] Ω  RE [1000] Ω   β [150]   VBE [0.7] V      │
│ [ Calculate ]                                          │
├────────────────────────────────────────────────────────┤
│ ● Active region                                        │
│ IB 8.82 µA   IC 1.324 mA   IE 1.333 mA                 │
│ VB 2.033 V   VC 9.088 V    VE 1.333 V   VCE 7.755 V    │
│ PC 10.27 mW                                            │
├────────────────────────────────────────────────────────┤
│ Check: Thevenin vs Nodal — max diff 0.000%  ✓          │
└────────────────────────────────────────────────────────┘
```

อินพุตเป็นหน่วยฐาน (Ω, V) ตัวเลขล้วน

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
- สองวิธีตรงกันภายใน `1e-6` (relative)

### Git

- branch `feat/bjt-ce-bias`
- commit แยกตามงานย่อย
- merge เข้า `main` แล้ว push ขึ้น GitHub

## สิ่งที่เหลือให้ผู้สร้างตัดสิน

- รายละเอียด CSS และการจัดวาง
- ข้อความ error/warning ที่แน่นอน
- ชื่อเทสและโครงสร้าง helper
- พอร์ต (ค่าเริ่มต้น 5000)

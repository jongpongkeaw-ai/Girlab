
# Girlab
ใช้สำหรับเรียนแล็บคอมโปรไฟฟ้า
=======
DC Circuit Calculator (Basic/Intermediate)

คำอธิบาย: โปรแกรมคำนวณวงจรตัวต้านทานแบบอนุกรม ขนาน และผสม โดยรับค่าแรงดันและค่าความต้านทานจากผู้ใช้

วัตถุประสงค์: เพื่อคำนวณกระแสไฟฟ้า กำลังไฟฟ้า และแรงดันตกคร่อมในแต่ละจุดของวงจรได้อย่างถูกต้องและรวดเร็ว

## BJT Common-Emitter DC Bias Web App (ENG29 2121)

เว็บแอป Flask สำหรับคำนวณจุดทำงาน DC ของวงจร BJT common-emitter
รองรับ 3 โหมดไบอัสด้วยแหล่งจ่ายเดียว: voltage-divider, fixed bias และ emitter bias
พร้อมตรวจสอบย่านการทำงาน

### Live demo

https://jongpongkeaw-ai.github.io/Girlab/

GitHub Pages เสิร์ฟ static mirror (JavaScript) ของเครื่องคำนวณเดียวกัน
โดยไม่ต้องมี server — ส่วน Flask app ด้านล่างยังเป็น implementation หลัก

### ความสามารถ

- เลือกโหมดได้ 3 แบบ: `Voltage Divider`, `Fixed Bias`, `Emitter Bias` (แหล่งจ่ายเดียว)
- Divider: รับ `VCC, R1, R2, RC, RE, β, VBE`
- Fixed: รับ `VCC, RB, RC, β, VBE`
- Emitter: รับ `VCC, RB, RC, RE, β, VBE`
- แสดง `VB, VE, VC, VCE, IB, IC, IE` (และ `PC`) พร้อมหน่วย
- ตรวจสอบอินพุตตามโหมดและเตือนย่าน Active / Cutoff / Saturation
- UI 3 คอลัมน์: Input / Circuit Diagram / Results พร้อมแถบ Week 3 Goal
- Bootstrap 5.3.3 ถูก vendor ไว้ใน `static/vendor/` จึงทำงานได้โดยไม่ต่ออินเทอร์เน็ต

### ติดตั้งและรัน

```powershell
git clone https://github.com/jongpongkeaw-ai/Girlab.git
cd Girlab
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

เปิด `http://127.0.0.1:5000`

### เทส

```powershell
.venv\Scripts\python -m pytest -v
```

### ตัวอย่าง

`VCC=12 V, R1=47000 Ω, R2=10000 Ω, RC=2200 Ω, RE=1000 Ω, β=150, VBE=0.7 V`

→ `IB=8.82 µA, IC=1.324 mA, IE=1.332 mA, VB=2.032 V, VC=9.088 V, VE=1.332 V, VCE=7.755 V` (Active region approximation OK)

Fixed Bias: `VCC=12 V, RB=470000 Ω, RC=2200 Ω, β=150, VBE=0.7 V`

→ `IB=24.04 µA, IC=3.606 mA, IE=3.630 mA, VB=0.700 V, VE=0.000 V, VC=4.066 V, VCE=4.066 V`

Emitter Bias: `VCC=12 V, RB=470000 Ω, RC=2200 Ω, RE=1000 Ω, β=150, VBE=0.7 V`

→ `IB=18.20 µA, IC=2.729 mA, IE=2.748 mA, VB=3.448 V, VC=5.995 V, VE=2.748 V, VCE=3.248 V`

### ขอบเขต

เครื่องคำนวณ DC ด้านบนเป็น approximation ด้วยค่าประมาณ β / VBE ที่ผู้ใช้กำหนด
ไม่มี AC analysis, transient, กราฟ, ตัวแก้ไขวงจร หรือ FET — ดูส่วน Lab 4 ด้านล่างสำหรับการจำลองด้วย ngspice

## Lab 4 · BJT Amplifier Simulator v1 (ngspice)

เพิ่มเข้าไปใน Flask app เดิมโดย **ไม่เปลี่ยน** routes `/`, ฟอร์ม Lab 3 หรือ `bjt.py`
(`dc_bias.py` ไม่มีอยู่ใน repository นี้; module วิเคราะห์เดิมคือ `bjt.py`)

### สิ่งที่จำลอง

หนึ่งวงจร CE voltage-divider อ้างอิง (ไม่มี bypass capacitor คร่อม RE):

| Parameter | Value |
|---|---|
| VCC | 12 V |
| R1 / R2 | 100 kΩ / 22 kΩ |
| RC / RE | 2.2 kΩ / 1 kΩ |
| RL | 10 kΩ |
| Cin / Cout | 10 µF / 10 µF |
| Vin | SIN 10 mV peak @ 1 kHz |

ค่าในฟอร์มทั้งหมดส่งเข้า netlist ได้ (ยกเว้น β / VBE ที่เป็นสมมติฐานของการคำนวณเชิงวิเคราะห์เท่านั้น)

### ติดตั้ง ngspice

ใช้ ngspice **47** (Windows 64-bit: `ngspice-47_64.7z` จาก
<https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/>)
แตก zip แล้วตั้ง executable ด้วย:

```powershell
$env:NGSPICE_EXECUTABLE = 'C:\path\to\ngspice47\Spice64\bin\ngspice.exe'
python -m flask --app app run
```

หรือเพิ่มโฟลเดอร์ `bin` ลงใน `PATH` แทนได้ ตรวจสอบว่า engine ใช้ได้ด้วยการรัน batch smoke test
(e.g. `ngspice.exe -b -o run.log circuit.cir`) — บน Windows `-v` อาจค้างในโหมดโต้ตอบ

**BJT model:** `.model QGEN NPN` — ngspice generic built-in default parameters.
โมเดลนี้เป็น **generic, NOT instructor-verified** ไม่มีการอ้างค่า device-specific และผล SPICE
จะไม่ตรงกับ β / VBE แบบ hand calculation เสมอไป

### รันและใช้งาน

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m flask --app app run
```

เปิด <http://127.0.0.1:5000/> สำหรับ Lab 3 และ <http://127.0.0.1:5000/simulator> สำหรับ Lab 4

- **DC · `.op`** — VB, VE, VC, VCE, IC (V / A), circuit state, model, engine status, netlist และ log excerpt
- **AC · `.ac`** — gain |Vout/Vin| (dB และ V/V), phase (deg), frequency (Hz) และ −3 dB cutoff
  (จะแสดง `not determined in sweep range` ถ้าไม่มีจุดตัดในช่วง sweep)
- **Transient · `.tran`** — time (s), Vin (V), Vout (V), peak amplitudes และ phase inversion

Vin อ้างอิงที่ node `src`, Vout ที่ node `out` (คร่อม RL หลัง Cout) ผลทั้งหมดมาจาก ngspice จริง
ผ่าน `subprocess.run([...], timeout=...)` ใน temp directory แยกต่อครั้ง ไม่มี mock data หรือกราฟสำเร็จรูป

ข้อมูลผิด, engine หาย, timeout หรือ solver fail → แสดง error state จริงและ **ไม่มีกราฟ/ผลลัพธ์เก่า**
รายละเอียดการตรวจสอบ B1–B8 ดูที่ `docs/validation.md`
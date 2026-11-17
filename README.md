
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

ไม่มี AC analysis, transient, กราฟ, ตัวแก้ไขวงจร หรือ FET
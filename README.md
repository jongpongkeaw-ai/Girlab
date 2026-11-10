
# Girlab
ใช้สำหรับเรียนแล็บคอมโปรไฟฟ้า
=======
DC Circuit Calculator (Basic/Intermediate)

คำอธิบาย: โปรแกรมคำนวณวงจรตัวต้านทานแบบอนุกรม ขนาน และผสม โดยรับค่าแรงดันและค่าความต้านทานจากผู้ใช้

วัตถุประสงค์: เพื่อคำนวณกระแสไฟฟ้า กำลังไฟฟ้า และแรงดันตกคร่อมในแต่ละจุดของวงจรได้อย่างถูกต้องและรวดเร็ว

## BJT Common-Emitter DC Bias Web App (ENG29 2121)

เว็บแอป Flask สำหรับคำนวณจุดทำงาน DC ของวงจร BJT common-emitter
แบบ voltage-divider bias พร้อมตรวจสอบย่านการทำงาน

### ความสามารถ

- รับค่า `VCC, R1, R2, RC, RE, β, VBE`
- แสดง `VB, VE, VC, VCE, IB, IC, IE` (และ `PC`) พร้อมหน่วย
- ตรวจสอบอินพุตและเตือนย่าน Active / Cutoff / Saturation
- UI 3 คอลัมน์: Input / Circuit Diagram / Results พร้อมแถบ Week 2 Goal
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

### ขอบเขต

ไม่มี AC analysis, transient, กราฟ, ตัวแก้ไขวงจร หรือ FET
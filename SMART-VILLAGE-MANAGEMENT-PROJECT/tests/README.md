
# Smart Village – Test Suite (Python)

> รวมชุดทดสอบ **ครบฟังก์ชัน** แยกเป็น Backend และ Frontend โดยใช้ Python ทั้งหมด

## โครงสร้าง
```
tests/
├─ test_backend.py     # unittest + Flask test_client + SocketIO test client
├─ test_frontend.py    # Selenium (Chrome) สำหรับ UI
└─ README.md
```

## ติดตั้ง Dependencies
```bash
pip install flask flask-socketio flask-cors flask-sqlalchemy werkzeug selenium
# และติดตั้ง Chrome + ChromeDriver ให้ตรงเวอร์ชัน
```

## การรัน Backend App
เปิดเซิร์ฟเวอร์ (ต้องเข้าถึง index.html ได้ที่ http://localhost:5000)
```bash
python app.py
```

## รันชุดทดสอบ
### 1) Backend
```bash
python tests/test_backend.py
```

### 2) Frontend
> ต้องมีเว็บรันอยู่ (ดูหัวข้อ "การรัน Backend App")
```bash
# ใช้พอร์ต/URL เองได้ผ่าน env SMART_VILLAGE_URL เช่น http://127.0.0.1:5000
SMART_VILLAGE_URL=http://localhost:5000 python tests/test_frontend.py
# (ค่าเริ่มต้น HEADLESS=1 ถ้าอยากดูเบราเซอร์จริงๆให้ตั้ง HEADLESS=0)
HEADLESS=0 SMART_VILLAGE_URL=http://localhost:5000 python tests/test_frontend.py
```

## รายการฟีเจอร์ที่ครอบคลุม
- **Auth**: สมัคร / ล็อกอิน (สำเร็จ/ล้มเหลว)
- **Users**: CRUD (เพิ่ม/อ่าน/แก้ไข/ลบ)
- **Announcements**: CRUD
- **Repair Requests**: สร้าง / อ่าน / อัปเดตสถานะ
- **Booking Requests**: สร้าง / อ่าน / แก้ไข / ลบ
- **File Upload**: เดี่ยว/หลายไฟล์
- **Bills**: สร้าง / อ่าน / แก้ไข / ลบ
- **Payments**: สร้าง / อ่าน / อนุมัติ / ปฏิเสธ (ทดสอบ reject หลัง approve ต้องล้มเหลว)
- **Realtime (Socket.IO)**: connect/join/send/receive
- **Frontend UI (Selenium)**: login elements + toggle, navigation showPage, repair form, announcements/bills/payments sections

## หมายเหตุสำคัญ
- ชุดทดสอบ Backend ใช้ฐานข้อมูล **sqlite in-memory** แยกจากไฟล์จริง ปลอดภัยสำหรับการรันเทส
- สำหรับ Upload endpoint เลือกนามสกุลไฟล์ `.png`/`.jpg` เพื่อผ่านตัวตรวจสอบไฟล์
- ถ้า index.html ผูก logic เรียก API อัตโนมัติ แนะนำให้รัน `python app.py` ก่อนทดสอบ Frontend
- หากใช้พอร์ต/โดเมนอื่น ให้กำหนดผ่าน env `SMART_VILLAGE_URL`
- หาก CI/CD ไม่มี GUI ให้รัน Selenium แบบ Headless (`HEADLESS=1` ซึ่งเป็นค่า default)

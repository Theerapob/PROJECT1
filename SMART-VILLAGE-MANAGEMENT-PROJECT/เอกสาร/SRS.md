ระบบจัดการหมู่บ้านจัดสรร SMART VILLAGE
**Software Requirement Specification Document**

เวอร์ชัน: 1.0
วันที่: 5 กรกฎาคม 2568
จัดทำโดย: ทีมพัฒนาระบบจัดการหมู่บ้านจัดสรร 
ระบบจัดการหมู่บ้านจัดสรร SMART VILLAGE
Software Requirement Specification Document

**เวอร์ชัน:** 1.0  
**วันที่:** 5 กรกฎาคม 2025
**จัดทำโดย:** ทีมพัฒนาระบบจัดการหมู่บ้านจัดสรร
ประวัติการจัดทำเอกสาร

วันที่	เวอร์ชัน	รายละเอียดการเปลี่ยนแปลง	ผู้ดำเนินการ
5/07/2025	1.0	จัดทำเอกสารฉบับแรก	ทีมพัฒนา
 

สารบัญ
1. [Introduction](#1-introduction)
   - 1.1 วัตถุประสงค์
   - 1.2 ภาพรวมของระบบ
   - 1.3 ขอบเขต
   - 1.4 กลุ่มผู้ใช้งาน

2. [System Requirements](#2-system-requirements)
   - 2.1 Hardware Requirements
   - 2.2 Software Requirements
   - 2.3 External Interfaces

3. [Software Requirements](#3-software-requirements)
   - 3.1 ระบบสมาชิก
   - 3.2 ระบบจองห้องพัก
   - 3.3 ระบบชำระเงิน
   - 3.4 ระบบจัดการห้องพัก

4. [Non-Functional Requirements](#4-non-functional-requirements)
   - 4.1 Performance Requirements
   - 4.2 Security Requirements
   - 4.3 Usability Requirements
   - 4.4 Reliability Requirements
   - 4.5 Maintainability Requirements

1. Introduction

1.1 วัตถุประสงค์
- เพื่อพัฒนาระบบจัดการหมู่บ้านจัดสรรออนไลน์ที่ใช้งานง่ายและครอบคลุมปัญหาที่ต้องแก้ไข
- เพื่อสร้างช่องทางการสื่อสารและแจ้งข่าวสารระหว่างนิติบุคคลและเจ้าของบ้านที่มีประสิทธิภาพ
- เพื่อเพิ่มความโปร่งใสในการบริหารจัดการค่าส่วนกลางและการแจ้งซ่อม
- เพื่อช่วยให้เจ้าของบ้านและนิติบุคคลสามารถติดตามสถานะงานและข้อมูลต่าง ๆ ได้แบบเรียลไทม์

1.2 ภาพรวมของระบบ
ระบบ SMART VILLAGE เป็นเว็บแอปพลิเคชันที่พัฒนาขึ้นเพื่อเป็นแพลตฟอร์มรวมศูนย์สำหรับกิจกรรมและบริการต่างๆ ภายในหมู่บ้าน โดยมีวัตถุประสงค์หลักเพื่อลดความยุ่งยากในการบริหารจัดการและเพิ่มความสะดวกสบายให้แก่ผู้อยู่อาศัยในด้านต่างๆระบบงานประกอบด้วยส่วนสำคัญดังนี้:
1.3 ขอบเขต
1.การจัดการผู้ใช้งาน: การเข้าสู่ระบบ, การลงทะเบียน, การจัดการโปรไฟล์ และการจัดการรหัสผ่าน
2. การแจ้งซ่อม: การส่งคำขอแจ้งซ่อม, การติดตามสถานะ, และการจัดการคำขอซ่อมโดยผู้ดูแลระบบ
3. การประกาศ: การเผยแพร่ข่าวสารและประกาศจากนิติบุคคลถึงผู้อยู่อาศัย
4. การชำระเงิน: การตรวจสอบบิลค้างชำระ, การแจ้งชำระเงิน, และการดูประวัติการชำระเงิน
5. การจองพื้นที่ส่วนกลาง: การส่งคำขอจองพื้นที่ส่วนกลาง และการติดตามสถานะการจอง
6. การรายงาน (สำหรับผู้ดูแลระบบ): การสร้างรายงานสรุปข้อมูลต่างๆ ระบบนี้จะรองรับบทบาทของผู้ใช้งานสองประเภทหลักคือ ผู้อยู่อาศัย (Resident) และ ผู้ดูแลระบบ (Admin)

1.4 กลุ่มผู้ใช้งาน
1. ลูกค้า
   - ผู้ใช้งานทั่วไป
   -ผู้ใช้งานที่เป็นสมาชิก
2. พนังานของร้าน
   - พนักงานต้อนรับ
   - ผู้จัดการ
3. ผู้ดูแลระบบ
   -แอดมิน
2. System Requirements
2.1 Hardware Requirements
- Server Requirements:
  - CPU: Intel core I5 หรือมากกว่า
  - RAM: 8GB ขึ้นไป
  - Storage: SSD 500GB ขึ้นไป

- Client Requirements:
  - สามารถเข้าถึงอินเทอร์เน็ตได้
  - รองรับ Web Browser ที่ทันสมัย

2.2 Software Requirements
- Operating System: Windows Server 2019 
- Web Server: firebase
- Database: postgresql หรือSQLite
- Programming Language: HTML. Python CSS

2.3 External Interfaces
 2.3.1 User Interfaces
Interface ID	Description	Platform/Technology
UI-01	หน้าเว็บไซต์สำหรับลูกค้า	Web Browser (Responsive)
UI-02	หน้าจัดการระบบสำหรับแอดมิน	Web Browser (Desktop)
UI-03	เว็บไซต์สำหรับการใช้งานของพนักงานในร้านร้าน	Web Browser (Desktop)


 2.3.2 Hardware Interfaces
Interface ID	Description	Protocol
HW-01	เครื่องสแกน QR Code	TCP/IP

 2.3.3 Software Interfaces
Interface ID	Description	Protocol/API
SW-01	ระบบชำระเงินออนไลน์	REST API
SW-02	LINE Notification	LINE API
SW-03	Google Maps	Google Maps API

 2.3.4 Communication Interfaces
Interface ID	Description	Protocol
COM-01	การเชื่อมต่อกับระบบธนาคาร	HTTPS/SSL
COM-03	การแจ้งเตือนผ่าน LINE	HTTPS





3. Software Requirements
3.1 ระบบสมาชิก (User Management)
Requirement ID	Requirement Description	Priority
USR-01	ระบบการลงทะเบียนสมัครสมาชิกสำหรับลูกค้าที่มาใช้งานที่ร้านบ่อยครั้งเพื่อรับส่วนลดหรือสิ่งต่างๆร้านต้องการแจ้งเตือน	High
USR-02	ระบบต้องรองรับการลงทะเบียนผ่าน Social Media เช่น ผ่าน Facebook Line Instragram	Medium
USR-03	ระบบต้องมีฟังก์ชันรีเซ็ตรหัสผ่านผ่านอีเมล	Medium
USR-04	ระบบต้องบันทึกประวัติการเข้าสู่ระบบ	Medium








 


3.2 ระบบจองห้องส่วนตัว (Search & Booking System)

Requirement ID	Requirement Description	Priority
BKG-01	ระบบต้องสามารถจัดการห้องส่วนตัวห้กับลูฏค้าได้โดยที่ระบบจะต้องมีฟังชั่นการทำงานในการจัดการรายละเอียดห้องส่วนตัวให้กับลูกค้า การแจ้งเตือนห้องเต็ม การแจ้งเตือนหมดเวลา	High
BKG-02	ระบบต้องแสดงข้อมูลห้องส่วนตัวที่ลูกค้าจอง
รูปแบบห้องส่วนตัวที่ลูกค้าจอง 
ราคาและค่าใช้จ่ายที่ลูกค้าต้องจ่ายสำหรับการจองห้องที่ใช้ สิ่งอำนวยความสะดวก
ขนาดห้องและจำนวนผู้เข้าใช้งาน 	High
BKG-03	ระบบต้องแสดงห้องที่ว่างสำหรับลูฏค้าที่จะจองใช้งานห้องส่วนตัว	High
BKG-04	ระบบต้องรองรับการจองห้องส่วนตัว
เลือกวันและเวลาที่จะเข้าใช้งาน-เวลาที่ต้องการออก 
เลือกเวลาที่เข้าใช้ห้อง ระบุจำนวนผู้เข้าพัก 	High
BKG-05	ระบบต้องแจ้งเตือนแก่พนักงานและลูกค้าที่จองห้องส่วนตัวที่จองสำเร็จ	High
 
3.3 ระบบชำระเงิน (Payment System)
Requirement ID	Requirement Description	Priority
PAY-01	ระบบต้องรองรับการชำระเงินผ่าน:ระบบธนาคารพร้อมเพลย์
บัตรเครดิต/เดบิต	High
PAY-02	ระบบต้องแสดงรายละเอียดค่าใช้จ่ายทั้งหมดก่อนชำระเงิน	High
PAY-03	ระบบต้องออกใบเสร็จ/ใบกำกับภาษีอิเล็กทรอนิกส์	High
PAY-04	ระบบต้องรองรับการคืนเงินตามนโยบายการยกเลิกโดยมีนโยบายการคืนเงิน จำนวนวันในการคืนเงิน ช่องทางการคืนเงินที่ปลอดภัย	High

3.4 ระบบจัดการห้องส่วนตัว (Room Management)

Requirement ID	Requirement Description	Priority
ROM-01	ระบบต้องรองรับการจัดการห้องส่วนตัวสำหรับพนักงานในร้านและผู้จัดการร้าน	High
ROM-02	ระบบต้องคำนวณค่าใช้จ่ายเพิ่มเติมระหว่างเข้าใช้งานห้องส่วนตัว	High
ROM-03	ระบบต้องอัพเดทสถานะห้องแบบ Real-time	High
ROM-04	ระบบควรมีการแจ้งเตือนเจ้าหน้าที่ในส่วนที่ห้องเต็ม มีการยกเลิกห้อง หรือลูกค้าได้ทำการเช็คอินหรือเช็คเอ้าท์	High
 
3.5 ระบบจัดการสำหรับผู้ดูแลระบบ (Admin System)

Requirement ID	Requirement Description	Priority
ADM-01	ระบบต้องรองรับการจัดการผู้ใช้งาน     จัดการสิทธิ์ดูประวัติการใช้งาน	High
ADM-02	ระบบต้องรองรับการจัดการการเข้าใช้ห้องส่วนตัวจัดการราคาและโปรโมชัน 
อัพโหลดรูปภาพ	High
ADM-03	ระบบต้องสามารถออกรายงานต่างๆได้ในรูปแบบไฟล์เอกสาร PDF หรือ xlsx	Medium
ADM-04	ระบบต้องรองรับการจัดการโปรโมชัน นโยบายของโปรโมชั่นหรือแนวทางของการใช้งานโปรโมชั่น	Medium

4. Non-Functional Requirements

4.1 Performance Requirements
Requirement ID	Requirement Description	Metric
PRF-01	ระบบต้องรองรับผู้ใช้งานพร้อมกันจำนวนมาก	≥ 1,000 users
PRF-02	เวลาตอบสนองการจองห้องส่วนตัว	≤ 3 วินาที
PRF-03	เวลาประมวลผลการชำระเงิน	≤ 5 วินาที
PRF-04	เวลาในการโหลดหน้าเว็บ	≤ 2 วินาที

 
4.2 Security Requirements
Requirement ID	Requirement Description	Priority
SEC-01	การเข้ารหัสข้อมูลด้วย SSL/TLS	High
SEC-02	การเข้ารหัสรหัสผ่านด้วย bcrypt หรือเทียบเท่า	High
SEC-03	การป้องกัน SQL Injection และ XSS	High
SEC-04	การล็อคบัญชีหลังล็อกอินผิด 5 ครั้ง	Medium
SEC-05	Session Timeout หลังไม่มีการใช้งาน 30 นาที	Medium
SEC-06	อีเมลแจ้งเตือนให้กับผู้ดูแลระบบเมื่อพบความผิดปกติจากการเข้าสู่ระบบหรือข้อมูลในระบบเกิดความผิดปกติเพื่อป้องกันข้อมูลของลูกค้าในระบบ	High



4.3 Usability Requirements
Requirement ID	Requirement Description	Priority
USB-01	ส่วนติดต่อผู้ใช้ต้องใช้งานง่าย	High
USB-02	รองรับ Responsive Design	High
USB-03	รองรับภาษาไทยและอังกฤษ	High
USB-04	มีคู่มือการใช้งานออนไลน์	Medium
USB-05	มีระบบช่วยเหลือแบบ Live Chat	Low
 
4.4 Reliability Requirements
Requirement ID	Requirement Description	Metric
REL-01	System Uptime	99.9%
REL-02	ระบบสำรองข้อมูลอัตโนมัติ	ทุก 24 ชั่วโมง
REL-03	ระยะเวลาในการกู้คืนระบบ เพิ่มแนวทางในการแก้ไขปัญหาที่เกิดขึ้นหรือเมื่อระบบล่มควรแก้ไขอย่างไร	≤ 4 ชั่วโมง
REL-04	การสำรองข้อมูลการจอง	Real-time
4.5 Maintainability Requirements
Requirement ID	Requirement Description	Priority
MNT-01	มีเอกสารประกอบการพัฒนาระบบ	High
MNT-02	มีระบบบันทึกและติดตามข้อผิดพลาด	High
MNT-03	มีการแยกส่วนการทำงานเป็นโมดูล	High




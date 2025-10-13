"""
SMART VILLAGE MANAGEMENT SYSTEM - BACKEND API TEST SUITE
=========================================================
ทดสอบเฉพาะ Backend API ที่พร้อมใช้งานเท่านั้น

การติดตั้ง:
pip install pytest requests pytest-html

การรัน:
pytest test_backend.py -v --html=report.html --self-contained-html
"""

import pytest
import requests
import json
import time
from datetime import datetime, timedelta

# ================================
# Configuration
# ================================
BASE_URL = "http://localhost:5000"

TEST_DATA = {
    "admin": {
        "username": "admin",
        "password": "admin123"
    },
    "resident": {
        "username": "resident",
        "password": "resident123"
    }
}

# ================================
# Fixtures
# ================================
@pytest.fixture(scope="session")
def admin_login():
    """Login เป็น Admin"""
    response = requests.post(f"{BASE_URL}/login", json=TEST_DATA["admin"])
    assert response.status_code == 200, "Admin login failed"
    return response.json()

@pytest.fixture(scope="session")
def resident_login():
    """Login เป็น Resident"""
    response = requests.post(f"{BASE_URL}/login", json=TEST_DATA["resident"])
    assert response.status_code == 200, "Resident login failed"
    return response.json()

@pytest.fixture
def test_user(admin_login):
    """สร้าง test user และ cleanup หลังใช้งาน"""
    username = f"testuser_{int(time.time())}"
    user_data = {
        "name": "Test User",
        "username": username,
        "password": "Test@123",
        "phone": "0812345678",
        "email": "test@example.com",
        "address": "A-999",
        "role": "resident",
        "status": "approved"
    }
    
    response = requests.post(f"{BASE_URL}/users", json=user_data)
    assert response.status_code == 201
    user = response.json()["user"]
    
    yield user
    
    # Cleanup
    try:
        requests.delete(f"{BASE_URL}/users/{user['user_id']}")
    except:
        pass

# ================================
# TEST CLASS 1: AUTHENTICATION
# ================================
class TestAuthentication:
    """Test Authentication API"""
    
    def test_login_admin_success(self):
        """TC-001: Login Admin สำเร็จ"""
        response = requests.post(f"{BASE_URL}/login", json=TEST_DATA["admin"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"
        assert "user_id" in data
        assert data["message"] == "Login successful"
        print("✓ TC-001 PASSED: Admin login successful")
    
    def test_login_resident_success(self):
        """TC-002: Login Resident สำเร็จ"""
        response = requests.post(f"{BASE_URL}/login", json=TEST_DATA["resident"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "resident"
        print("✓ TC-002 PASSED: Resident login successful")
    
    def test_login_invalid_password(self):
        """TC-003: Login ด้วยรหัสผ่านผิด"""
        response = requests.post(
            f"{BASE_URL}/login",
            json={"username": "admin", "password": "wrongpass"}
        )
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["message"]
        print("✓ TC-003 PASSED: Invalid password rejected")
    
    def test_login_invalid_username(self):
        """TC-004: Login ด้วย username ที่ไม่มี"""
        response = requests.post(
            f"{BASE_URL}/login",
            json={"username": "notexist", "password": "password"}
        )
        
        assert response.status_code == 401
        print("✓ TC-004 PASSED: Invalid username rejected")
    
    def test_login_missing_credentials(self):
        """TC-005: Login โดยไม่ส่ง credentials"""
        response = requests.post(f"{BASE_URL}/login", json={})
        
        assert response.status_code == 400
        print("✓ TC-005 PASSED: Missing credentials rejected")

# ================================
# TEST CLASS 2: USER MANAGEMENT
# ================================
class TestUserManagement:
    """Test User Management API"""
    
    def test_create_user(self):
        """TC-006: สร้าง user ใหม่"""
        username = f"newuser_{int(time.time())}"
        user_data = {
            "name": "New User",
            "username": username,
            "password": "Pass@123",
            "phone": "0899999999",
            "email": "newuser@test.com",
            "address": "B-101"
        }
        
        response = requests.post(f"{BASE_URL}/users", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["username"] == username
        print("✓ TC-006 PASSED: User created")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/users/{data['user']['user_id']}")
    
    def test_create_user_duplicate_username(self):
        """TC-007: สร้าง user ด้วย username ซ้ำ"""
        response = requests.post(
            f"{BASE_URL}/users",
            json={
                "name": "Duplicate",
                "username": "admin",
                "password": "Pass@123"
            }
        )
        
        assert response.status_code in [409, 500]
        assert "already exists" in response.json()["message"].lower()
        print("✓ TC-007 PASSED: Duplicate username rejected")
    
    def test_get_all_users(self):
        """TC-008: ดึงรายชื่อผู้ใช้ทั้งหมด"""
        response = requests.get(f"{BASE_URL}/users")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        print(f"✓ TC-008 PASSED: Retrieved {len(data)} users")
    
    def test_get_user_by_id(self, resident_login):
        """TC-009: ดึงข้อมูล user ตาม ID"""
        user_id = resident_login["user_id"]
        response = requests.get(f"{BASE_URL}/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        print("✓ TC-009 PASSED: User retrieved by ID")
    
    def test_update_user(self, test_user):
        """TC-010: แก้ไขข้อมูล user"""
        updated_data = {
            "name": "Updated Name",
            "phone": "0811111111"
        }
        
        response = requests.put(
            f"{BASE_URL}/users/{test_user['user_id']}",
            json=updated_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["name"] == updated_data["name"]
        print("✓ TC-010 PASSED: User updated")
    
    def test_delete_user(self):
        """TC-011: ลบ user"""
        username = f"todelete_{int(time.time())}"
        create_response = requests.post(
            f"{BASE_URL}/users",
            json={
                "name": "To Delete",
                "username": username,
                "password": "Pass@123"
            }
        )
        user_id = create_response.json()["user"]["user_id"]
        
        response = requests.delete(f"{BASE_URL}/users/{user_id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        get_response = requests.get(f"{BASE_URL}/users/{user_id}")
        assert get_response.status_code == 404
        print("✓ TC-011 PASSED: User deleted")

# ================================
# TEST CLASS 3: ANNOUNCEMENTS
# ================================
class TestAnnouncements:
    """Test Announcements API"""
    
    def test_create_announcement(self, admin_login):
        """TC-012: สร้างประกาศใหม่"""
        ann_data = {
            "title": "ประกาศทดสอบ",
            "content": "นี่คือประกาศทดสอบ",
            "author_id": admin_login["user_id"],
            "published_date": datetime.now().isoformat(),
            "tag": "ทั่วไป"
        }
        
        response = requests.post(f"{BASE_URL}/announcements", json=ann_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["announcement"]["title"] == ann_data["title"]
        print("✓ TC-012 PASSED: Announcement created")
        
        requests.delete(f"{BASE_URL}/announcements/{data['announcement']['announcement_id']}")
    
    def test_get_all_announcements(self):
        """TC-013: ดึงประกาศทั้งหมด"""
        response = requests.get(f"{BASE_URL}/announcements")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ TC-013 PASSED: Retrieved {len(data)} announcements")
    
    def test_update_announcement(self, admin_login):
        """TC-014: แก้ไขประกาศ"""
        create_response = requests.post(
            f"{BASE_URL}/announcements",
            json={
                "title": "Original",
                "content": "Original Content",
                "author_id": admin_login["user_id"]
            }
        )
        ann_id = create_response.json()["announcement"]["announcement_id"]
        
        response = requests.put(
            f"{BASE_URL}/announcements/{ann_id}",
            json={"title": "Updated", "content": "Updated Content"}
        )
        
        assert response.status_code == 200
        assert response.json()["announcement"]["title"] == "Updated"
        print("✓ TC-014 PASSED: Announcement updated")
        
        requests.delete(f"{BASE_URL}/announcements/{ann_id}")
    
    def test_delete_announcement(self, admin_login):
        """TC-015: ลบประกาศ"""
        create_response = requests.post(
            f"{BASE_URL}/announcements",
            json={
                "title": "To Delete",
                "content": "Will be deleted",
                "author_id": admin_login["user_id"]
            }
        )
        ann_id = create_response.json()["announcement"]["announcement_id"]
        
        response = requests.delete(f"{BASE_URL}/announcements/{ann_id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        print("✓ TC-015 PASSED: Announcement deleted")

# ================================
# TEST CLASS 4: REPAIR REQUESTS
# ================================
class TestRepairRequests:
    """Test Repair Requests API"""
    
    def test_create_repair_request(self, resident_login):
        """TC-016: แจ้งซ่อมใหม่"""
        repair_data = {
            "user_id": resident_login["user_id"],
            "title": "ไฟฟ้าเสีย",
            "category": "ไฟฟ้า",
            "description": "ไฟในห้องน้ำไม่ติด",
            "image_paths": "[]"
        }
        
        response = requests.post(f"{BASE_URL}/repair-requests", json=repair_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["request"]["status"] == "pending"
        assert data["request"]["title"] == repair_data["title"]
        print("✓ TC-016 PASSED: Repair request created")
    
    def test_get_all_repair_requests(self):
        """TC-017: ดึงรายการแจ้งซ่อมทั้งหมด"""
        response = requests.get(f"{BASE_URL}/repair-requests")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ TC-017 PASSED: Retrieved {len(data)} repair requests")
    
    def test_update_repair_status(self, resident_login):
        """TC-018: อัปเดตสถานะงานซ่อม"""
        create_response = requests.post(
            f"{BASE_URL}/repair-requests",
            json={
                "user_id": resident_login["user_id"],
                "title": "Test Repair",
                "category": "อื่นๆ",
                "description": "Test"
            }
        )
        request_id = create_response.json()["request"]["request_id"]
        
        response = requests.put(
            f"{BASE_URL}/repair-requests/{request_id}",
            json={"status": "in_progress"}
        )
        
        assert response.status_code == 200
        assert response.json()["request"]["status"] == "in_progress"
        print("✓ TC-018 PASSED: Repair status updated")
    
    def test_filter_repair_by_user(self, resident_login):
        """TC-019: กรองงานซ่อมตาม user"""
        user_id = resident_login["user_id"]
        response = requests.get(
            f"{BASE_URL}/repair-requests",
            params={"user_id": user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["user_id"] == user_id
        print("✓ TC-019 PASSED: Filtered by user")

# ================================
# TEST CLASS 5: BOOKING REQUESTS
# ================================
class TestBookingRequests:
    """Test Booking Requests API"""
    
    def test_create_booking(self, resident_login):
        """TC-020: จองพื้นที่ใหม่"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        booking_data = {
            "user_id": resident_login["user_id"],
            "location": "สนามกีฬา",
            "date": tomorrow.isoformat(),
            "start_time": "14:00",
            "end_time": "16:00",
            "purpose": "เล่นฟุตบอล",
            "attendee_count": 10
        }
        
        response = requests.post(f"{BASE_URL}/booking-requests", json=booking_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["booking"]["status"] == "pending"
        print("✓ TC-020 PASSED: Booking created")
        
        requests.delete(f"{BASE_URL}/booking-requests/{data['booking']['booking_id']}")
    
    def test_get_all_bookings(self):
        """TC-021: ดึงรายการจองทั้งหมด"""
        response = requests.get(f"{BASE_URL}/booking-requests")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ TC-021 PASSED: Retrieved {len(data)} bookings")
    
    def test_booking_conflict_detection(self, resident_login):
        """TC-022: ตรวจจับการจองซ้อนทับ"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        booking1 = requests.post(
            f"{BASE_URL}/booking-requests",
            json={
                "user_id": resident_login["user_id"],
                "location": "สระว่ายน้ำ",
                "date": tomorrow.isoformat(),
                "start_time": "10:00",
                "end_time": "12:00",
                "purpose": "ว่ายน้ำ",
                "attendee_count": 5
            }
        )
        booking1_id = booking1.json()["booking"]["booking_id"]
        
        requests.put(
            f"{BASE_URL}/booking-requests/{booking1_id}",
            json={"status": "approved"}
        )
        
        response = requests.post(
            f"{BASE_URL}/booking-requests",
            json={
                "user_id": resident_login["user_id"],
                "location": "สระว่ายน้ำ",
                "date": tomorrow.isoformat(),
                "start_time": "11:00",
                "end_time": "13:00",
                "purpose": "ว่ายน้ำ"
            }
        )
        
        assert response.status_code == 409
        assert "already booked" in response.json()["message"].lower()
        print("✓ TC-022 PASSED: Conflict detected")
        
        requests.delete(f"{BASE_URL}/booking-requests/{booking1_id}")
    
    def test_update_booking_status(self, resident_login):
        """TC-023: อัปเดตสถานะการจอง"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        create_response = requests.post(
            f"{BASE_URL}/booking-requests",
            json={
                "user_id": resident_login["user_id"],
                "location": "คลับเฮ้าส์",
                "date": tomorrow.isoformat(),
                "start_time": "18:00",
                "end_time": "20:00",
                "purpose": "งานเลี้ยง"
            }
        )
        booking_id = create_response.json()["booking"]["booking_id"]
        
        response = requests.put(
            f"{BASE_URL}/booking-requests/{booking_id}",
            json={"status": "approved"}
        )
        
        assert response.status_code == 200
        assert response.json()["booking"]["status"] == "approved"
        print("✓ TC-023 PASSED: Booking status updated")
        
        requests.delete(f"{BASE_URL}/booking-requests/{booking_id}")
    
    def test_delete_booking(self, resident_login):
        """TC-024: ยกเลิกการจอง"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        create_response = requests.post(
            f"{BASE_URL}/booking-requests",
            json={
                "user_id": resident_login["user_id"],
                "location": "ห้องประชุม",
                "date": tomorrow.isoformat(),
                "start_time": "09:00",
                "end_time": "11:00",
                "purpose": "ประชุม"
            }
        )
        booking_id = create_response.json()["booking"]["booking_id"]
        
        response = requests.delete(f"{BASE_URL}/booking-requests/{booking_id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        print("✓ TC-024 PASSED: Booking deleted")

# ================================
# TEST CLASS 6: BILLS
# ================================
class TestBills:
    """Test Bills API"""
    
    def test_create_bill(self, admin_login):
        """TC-025: สร้างบิลใหม่"""
        next_month = (datetime.now() + timedelta(days=30)).date()
        bill_data = {
            "item_name": "ค่าส่วนกลาง",
            "amount": 1500.00,
            "due_date": next_month.isoformat(),
            "recipient_id": "all",
            "issued_by_user_id": admin_login["user_id"]
        }
        
        response = requests.post(f"{BASE_URL}/bills", json=bill_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["bill"]["amount"] == 1500.00
        assert data["bill"]["status"] == "unpaid"
        print("✓ TC-025 PASSED: Bill created")
        
        requests.delete(f"{BASE_URL}/bills/{data['bill']['bill_id']}")
    
    def test_get_all_bills(self):
        """TC-026: ดึงบิลทั้งหมด"""
        response = requests.get(f"{BASE_URL}/bills")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ TC-026 PASSED: Retrieved {len(data)} bills")
    
    def test_get_bills_for_user(self, resident_login):
        """TC-027: ดึงบิลของ user"""
        user_id = resident_login["user_id"]
        response = requests.get(f"{BASE_URL}/bills", params={"user_id": user_id})
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ TC-027 PASSED: Retrieved {len(data)} bills for user")
    
    def test_update_bill(self, admin_login):
        """TC-028: แก้ไขบิล"""
        next_month = (datetime.now() + timedelta(days=30)).date()
        
        create_response = requests.post(
            f"{BASE_URL}/bills",
            json={
                "item_name": "Original",
                "amount": 100.00,
                "due_date": next_month.isoformat(),
                "recipient_id": "all",
                "issued_by_user_id": admin_login["user_id"]
            }
        )
        bill_id = create_response.json()["bill"]["bill_id"]
        
        response = requests.put(
            f"{BASE_URL}/bills/{bill_id}",
            json={"item_name": "Updated", "amount": 200.00}
        )
        
        assert response.status_code == 200
        assert response.json()["bill"]["item_name"] == "Updated"
        print("✓ TC-028 PASSED: Bill updated")
        
        requests.delete(f"{BASE_URL}/bills/{bill_id}")
    
    def test_delete_bill(self, admin_login):
        """TC-029: ลบบิล"""
        next_month = (datetime.now() + timedelta(days=30)).date()
        
        create_response = requests.post(
            f"{BASE_URL}/bills",
            json={
                "item_name": "To Delete",
                "amount": 50.00,
                "due_date": next_month.isoformat(),
                "recipient_id": "all",
                "issued_by_user_id": admin_login["user_id"]
            }
        )
        bill_id = create_response.json()["bill"]["bill_id"]
        
        response = requests.delete(f"{BASE_URL}/bills/{bill_id}")
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        print("✓ TC-029 PASSED: Bill deleted")

# ================================
# TEST CLASS 7: PAYMENTS
# ================================
class TestPayments:
    """Test Payments API"""
    
    def test_create_payment(self, resident_login, admin_login):
        """TC-030: สร้างการชำระเงิน"""
        next_month = (datetime.now() + timedelta(days=30)).date()
        
        bill_response = requests.post(
            f"{BASE_URL}/bills",
            json={
                "item_name": "ค่าจอดรถ",
                "amount": 300.00,
                "due_date": next_month.isoformat(),
                "recipient_id": resident_login["user_id"],
                "issued_by_user_id": admin_login["user_id"]
            }
        )
        bill_id = bill_response.json()["bill"]["bill_id"]
        
        payment_data = {
            "bill_id": bill_id,
            "user_id": resident_login["user_id"],
            "amount": 300.00,
            "payment_method": "bank_transfer",
            "slip_path": "test/slip.jpg"
        }
        
        response = requests.post(f"{BASE_URL}/payments", json=payment_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["payment"]["status"] == "pending"
        print("✓ TC-030 PASSED: Payment created")
        
        requests.delete(f"{BASE_URL}/bills/{bill_id}")
    
    def test_get_all_payments(self):
        """TC-031: ดึงการชำระเงินทั้งหมด (Admin)"""
        response = requests.get(f"{BASE_URL}/payments")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ TC-031 PASSED: Retrieved {len(data)} payments")
    
    def test_get_user_payments(self, resident_login):
        """TC-032: ดึงการชำระเงินของ user"""
        user_id = resident_login["user_id"]
        response = requests.get(f"{BASE_URL}/payments", params={"user_id": user_id})
        
        assert response.status_code == 200
        data = response.json()
        for payment in data:
            assert payment["user_id"] == user_id
        print("✓ TC-032 PASSED: User payments retrieved")
    
    def test_approve_payment(self, resident_login, admin_login):
        """TC-033: Admin อนุมัติการชำระเงิน"""
        next_month = (datetime.now() + timedelta(days=30)).date()
        
        bill_response = requests.post(
            f"{BASE_URL}/bills",
            json={
                "item_name": "ค่าบริการ",
                "amount": 500.00,
                "due_date": next_month.isoformat(),
                "recipient_id": resident_login["user_id"],
                "issued_by_user_id": admin_login["user_id"]
            }
        )
        bill_id = bill_response.json()["bill"]["bill_id"]
        
        payment_response = requests.post(
            f"{BASE_URL}/payments",
            json={
                "bill_id": bill_id,
                "user_id": resident_login["user_id"],
                "amount": 500.00,
                "payment_method": "promptpay",
                "slip_path": "test/slip2.jpg"
            }
        )
        payment_id = payment_response.json()["payment"]["payment_id"]
        
        response = requests.put(f"{BASE_URL}/payments/approve/{payment_id}")
        
        assert response.status_code == 200
        assert response.json()["payment"]["status"] == "paid"
        print("✓ TC-033 PASSED: Payment approved")
        
        bill_check = requests.get(f"{BASE_URL}/bills")
        bills = bill_check.json()
        bill = next((b for b in bills if b["bill_id"] == bill_id), None)
        assert bill["status"] == "paid"
        
        requests.delete(f"{BASE_URL}/bills/{bill_id}")
    
    def test_reject_payment(self, resident_login, admin_login):
        """TC-034: Admin ปฏิเสธการชำระเงิน"""
        next_month = (datetime.now() + timedelta(days=30)).date()
        
        bill_response = requests.post(
            f"{BASE_URL}/bills",
            json={
                "item_name": "ค่าปรับ",
                "amount": 100.00,
                "due_date": next_month.isoformat(),
                "recipient_id": resident_login["user_id"],
                "issued_by_user_id": admin_login["user_id"]
            }
        )
        bill_id = bill_response.json()["bill"]["bill_id"]
        
        payment_response = requests.post(
            f"{BASE_URL}/payments",
            json={
                "bill_id": bill_id,
                "user_id": resident_login["user_id"],
                "amount": 100.00,
                "payment_method": "bank_transfer",
                "slip_path": "test/invalid.jpg"
            }
        )
        payment_id = payment_response.json()["payment"]["payment_id"]
        
        response = requests.put(f"{BASE_URL}/payments/reject/{payment_id}")
        
        assert response.status_code == 200
        assert response.json()["payment"]["status"] == "rejected"
        print("✓ TC-034 PASSED: Payment rejected")
        
        bill_check = requests.get(f"{BASE_URL}/bills")
        bills = bill_check.json()
        bill = next((b for b in bills if b["bill_id"] == bill_id), None)
        assert bill["status"] == "unpaid"
        
        requests.delete(f"{BASE_URL}/bills/{bill_id}")

# ================================
# TEST CLASS 8: FILE UPLOADS
# ================================
class TestFileUploads:
    """Test File Upload API"""
    
    def test_upload_single_file(self, resident_login):
        """TC-035: อัปโหลดไฟล์เดี่ยว"""
        test_file = ('test.txt', b'Test content', 'text/plain')
        
        response = requests.post(
            f"{BASE_URL}/upload",
            files={'file': test_file},
            data={
                'type': 'repair',
                'user_id': resident_login["user_id"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'path' in data
        assert data['message'] == 'File uploaded successfully'
        print("✓ TC-035 PASSED: File uploaded")
    
    def test_upload_multiple_files(self, resident_login):
        """TC-036: อัปโหลดหลายไฟล์"""
        files = [
            ('files[]', ('test1.txt', b'Content 1', 'text/plain')),
            ('files[]', ('test2.txt', b'Content 2', 'text/plain'))
        ]
        
        response = requests.post(
            f"{BASE_URL}/upload-multiple",
            files=files,
            data={
                'type': 'profile',
                'user_id': resident_login["user_id"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'paths' in data
        assert len(data['paths']) == 2
        print("✓ TC-036 PASSED: Multiple files uploaded")
    
    def test_upload_invalid_file_type(self, resident_login):
        """TC-037: อัปโหลดไฟล์ที่ไม่อนุญาต"""
        invalid_file = ('test.exe', b'Executable', 'application/exe')
        
        response = requests.post(
            f"{BASE_URL}/upload",
            files={'file': invalid_file},
            data={
                'type': 'general',
                'user_id': resident_login["user_id"]
            }
        )
        
        assert response.status_code == 400
        assert 'not allowed' in response.json()['message'].lower()
        print("✓ TC-037 PASSED: Invalid file rejected")
    
    def test_upload_without_file(self):
        """TC-038: พยายามอัปโหลดโดยไม่มีไฟล์"""
        response = requests.post(
            f"{BASE_URL}/upload",
            data={'type': 'general', 'user_id': 'test'}
        )
        
        assert response.status_code == 400
        assert 'No file' in response.json()['message']
        print("✓ TC-038 PASSED: Upload without file rejected")

# ================================
# TEST CLASS 9: INTEGRATION WORKFLOWS
# ================================
class TestIntegrationWorkflows:
    """Test Complete Workflows"""
    
    def test_complete_repair_workflow(self, resident_login, admin_login):
        """TC-039: Workflow การแจ้งซ่อมแบบสมบูรณ์"""
        # 1. Resident แจ้งซ่อม
        repair_response = requests.post(
            f"{BASE_URL}/repair-requests",
            json={
                "user_id": resident_login["user_id"],
                "title": "ประตูชำรุด",
                "category": "อื่นๆ",
                "description": "ประตูหลักเปิดไม่ได้"
            }
        )
        assert repair_response.status_code == 201
        request_id = repair_response.json()["request"]["request_id"]
        print("  Step 1: Resident แจ้งซ่อม ✓")
        
        # 2. Admin รับเรื่อง
        accept_response = requests.put(
            f"{BASE_URL}/repair-requests/{request_id}",
            json={"status": "in_progress"}
        )
        assert accept_response.status_code == 200
        assert accept_response.json()["request"]["status"] == "in_progress"
        print("  Step 2: Admin รับเรื่อง ✓")
        
        # 3. Admin ทำเสร็จ
        complete_response = requests.put(
            f"{BASE_URL}/repair-requests/{request_id}",
            json={"status": "completed"}
        )
        assert complete_response.status_code == 200
        assert complete_response.json()["request"]["status"] == "completed"
        print("  Step 3: Admin ปิดงาน ✓")
        
        print("✓ TC-039 PASSED: Complete repair workflow")
    
    def test_complete_booking_workflow(self, resident_login, admin_login):
        """TC-040: Workflow การจองแบบสมบูรณ์"""
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        # 1. Resident ส่งคำขอจอง
        booking_response = requests.post(
            f"{BASE_URL}/booking-requests",
            json={
                "user_id": resident_login["user_id"],
                "location": "สนามเด็กเล่น",
                "date": tomorrow.isoformat(),
                "start_time": "15:00",
                "end_time": "17:00",
                "purpose": "จัดงานวันเด็ก",
                "attendee_count": 50
            }
        )
        assert booking_response.status_code == 201
        booking_id = booking_response.json()["booking"]["booking_id"]
        print("  Step 1: Resident ส่งคำขอจอง ✓")
        
        # 2. Admin อนุมัติ
        approve_response = requests.put(
            f"{BASE_URL}/booking-requests/{booking_id}",
            json={"status": "approved"}
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["booking"]["status"] == "approved"
        print("  Step 2: Admin อนุมัติ ✓")
        
        # 3. Resident ยกเลิก
        cancel_response = requests.delete(
            f"{BASE_URL}/booking-requests/{booking_id}"
        )
        assert cancel_response.status_code == 200
        print("  Step 3: Resident ยกเลิก ✓")
        
        print("✓ TC-040 PASSED: Complete booking workflow")
    
    def test_complete_payment_workflow(self, resident_login, admin_login):
        """TC-041: Workflow การชำระเงินแบบสมบูรณ์"""
        next_month = (datetime.now() + timedelta(days=30)).date()
        
        # 1. Admin สร้างบิล
        bill_response = requests.post(
            f"{BASE_URL}/bills",
            json={
                "item_name": "ค่าน้ำ",
                "amount": 250.00,
                "due_date": next_month.isoformat(),
                "recipient_id": resident_login["user_id"],
                "issued_by_user_id": admin_login["user_id"]
            }
        )
        assert bill_response.status_code == 201
        bill_id = bill_response.json()["bill"]["bill_id"]
        print("  Step 1: Admin สร้างบิล ✓")
        
        # 2. Resident ชำระเงิน
        payment_response = requests.post(
            f"{BASE_URL}/payments",
            json={
                "bill_id": bill_id,
                "user_id": resident_login["user_id"],
                "amount": 250.00,
                "payment_method": "promptpay",
                "slip_path": "test/payment_slip.jpg"
            }
        )
        assert payment_response.status_code == 201
        payment_id = payment_response.json()["payment"]["payment_id"]
        print("  Step 2: Resident ชำระเงิน ✓")
        
        # 3. Admin อนุมัติ
        approve_response = requests.put(
            f"{BASE_URL}/payments/approve/{payment_id}"
        )
        assert approve_response.status_code == 200
        assert approve_response.json()["payment"]["status"] == "paid"
        print("  Step 3: Admin อนุมัติการชำระ ✓")
        
        # 4. ตรวจสอบบิล
        bill_check = requests.get(f"{BASE_URL}/bills")
        bills = bill_check.json()
        bill = next((b for b in bills if b["bill_id"] == bill_id), None)
        assert bill["status"] == "paid"
        print("  Step 4: บิลเปลี่ยนเป็น paid ✓")
        
        print("✓ TC-041 PASSED: Complete payment workflow")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/bills/{bill_id}")
    
    def test_user_registration_workflow(self, admin_login):
        """TC-042: Workflow การลงทะเบียนและอนุมัติ"""
        new_username = f"newresident_{int(time.time())}"
        
        # 1. User ลงทะเบียน
        register_response = requests.post(
            f"{BASE_URL}/users",
            json={
                "name": "ผู้อยู่อาศัยใหม่",
                "username": new_username,
                "password": "NewPass@123",
                "phone": "0898765432",
                "email": "newresident@test.com",
                "address": "C-201",
                "role": "resident"
            }
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["user"]["user_id"]
        print("  Step 1: User ลงทะเบียน ✓")
        
        # 2. ตรวจสอบสถานะ pending
        user_check = requests.get(f"{BASE_URL}/users/{user_id}")
        assert user_check.json()["status"] == "pending"
        print("  Step 2: สถานะ pending ✓")
        
        # 3. พยายาม login (ควรไม่สำเร็จ)
        login_response = requests.post(
            f"{BASE_URL}/login",
            json={"username": new_username, "password": "NewPass@123"}
        )
        assert login_response.status_code == 403
        print("  Step 3: Login ไม่สำเร็จ (pending) ✓")
        
        # 4. Admin อนุมัติ
        approve_response = requests.put(
            f"{BASE_URL}/users/{user_id}",
            json={"status": "approved"}
        )
        assert approve_response.status_code == 200
        print("  Step 4: Admin อนุมัติ ✓")
        
        # 5. Login สำเร็จ
        login_again = requests.post(
            f"{BASE_URL}/login",
            json={"username": new_username, "password": "NewPass@123"}
        )
        assert login_again.status_code == 200
        print("  Step 5: Login สำเร็จ ✓")
        
        print("✓ TC-042 PASSED: User registration workflow")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/users/{user_id}")

# ================================
# SUMMARY FUNCTION
# ================================
def print_test_summary():
    """พิมพ์สรุปการทดสอบ"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("\nTest Categories:")
    print("  1. Authentication (TC-001 to TC-005)         : 5 tests")
    print("  2. User Management (TC-006 to TC-011)        : 6 tests")
    print("  3. Announcements (TC-012 to TC-015)          : 4 tests")
    print("  4. Repair Requests (TC-016 to TC-019)        : 4 tests")
    print("  5. Booking Requests (TC-020 to TC-024)       : 5 tests")
    print("  6. Bills (TC-025 to TC-029)                  : 5 tests")
    print("  7. Payments (TC-030 to TC-034)               : 5 tests")
    print("  8. File Uploads (TC-035 to TC-038)           : 4 tests")
    print("  9. Integration Workflows (TC-039 to TC-042)  : 4 tests")
    print("\n" + "="*70)
    print("TOTAL: 42 Test Cases")
    print("="*70)
    print("\nBackend APIs Covered:")
    print("  ✓ /login")
    print("  ✓ /users (GET, POST, PUT, DELETE)")
    print("  ✓ /announcements (GET, POST, PUT, DELETE)")
    print("  ✓ /repair-requests (GET, POST, PUT)")
    print("  ✓ /booking-requests (GET, POST, PUT, DELETE)")
    print("  ✓ /bills (GET, POST, PUT, DELETE)")
    print("  ✓ /payments (GET, POST)")
    print("  ✓ /payments/approve/{id} (PUT)")
    print("  ✓ /payments/reject/{id} (PUT)")
    print("  ✓ /upload (POST)")
    print("  ✓ /upload-multiple (POST)")
    print("="*70 + "\n")

# ================================
# MAIN TEST RUNNER
# ================================
if __name__ == "__main__":
    print("\n" + "="*70)
    print("SMART VILLAGE BACKEND API TEST SUITE")
    print("="*70)
    print("\nTest Configuration:")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Admin User: {TEST_DATA['admin']['username']}")
    print(f"  Resident User: {TEST_DATA['resident']['username']}")
    print("="*70 + "\n")
    
    # Print summary before running
    print_test_summary()
    
    print("\nStarting test execution...\n")
    
    # Run tests with verbose output and HTML report
    exit_code = pytest.main([
        __file__,
        "-v",                                    # Verbose
        "-s",                                    # Show print statements
        "--tb=short",                            # Short traceback
        "--html=test_report.html",               # HTML report
        "--self-contained-html",                 # Self-contained HTML
        "-W", "ignore::DeprecationWarning"       # Ignore warnings
    ])
    
    print("\n" + "="*70)
    print("TEST EXECUTION COMPLETED!")
    print("="*70)
    print("\nResults:")
    print(f"  Exit Code: {exit_code}")
    print(f"  Report: test_report.html")
    print("\nTo view the report:")
    print("  Open 'test_report.html' in your web browser")
    print("="*70 + "\n")
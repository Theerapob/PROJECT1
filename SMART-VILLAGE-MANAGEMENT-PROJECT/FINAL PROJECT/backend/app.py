import os
import uuid
from datetime import datetime, date, timedelta
import json

from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# --- Configuration ---
DATABASE_FILE = 'smart_village.db'
UPLOAD_FOLDER = 'static/uploads'

app = Flask(__name__, static_folder='static')
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_FILE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- File Upload Configuration ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Models (Same as original) ---
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.String(255))
    role = db.Column(db.String(20), default='resident')
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'username': self.username,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Announcement(db.Model):
    __tablename__ = 'announcements'
    announcement_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    published_date = db.Column(db.DateTime, default=datetime.now)
    author_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    tag = db.Column(db.String(50))
    tag_color = db.Column(db.String(20))
    tag_bg = db.Column(db.String(20))

    author = db.relationship('User', backref='announcements_authored')

    def to_dict(self):
        return {
            'announcement_id': self.announcement_id,
            'title': self.title,
            'content': self.content,
            'published_date': self.published_date.isoformat(),
            'author_id': self.author_id,
            'author_name': self.author.name if self.author else None,
            'tag': self.tag,
            'tag_color': self.tag_color,
            'tag_bg': self.tag_bg
        }

class RepairRequest(db.Model):
    __tablename__ = 'repair_requests'
    request_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    submitted_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50), default='pending')
    image_paths = db.Column(db.Text)

    requester = db.relationship('User', backref='repair_requests_made')

    def to_dict(self):
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'user_name': self.requester.name if self.requester else None,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'submitted_date': self.submitted_date.isoformat(),
            'status': self.status,
            'image_paths': self.image_paths
        }

class BookingRequest(db.Model):
    __tablename__ = 'booking_requests'
    booking_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), nullable=False)
    end_time = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.Text)
    attendee_count = db.Column(db.Integer)
    status = db.Column(db.String(50), default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.now)

    booker = db.relationship('User', backref='booking_requests_made')

    def to_dict(self):
        return {
            'booking_id': self.booking_id,
            'user_id': self.user_id,
            'user_name': self.booker.name if self.booker else None,
            'location': self.location,
            'date': self.date.isoformat(),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'purpose': self.purpose,
            'attendee_count': self.attendee_count,
            'status': self.status,
            'requested_at': self.requested_at.isoformat()
        }

class Bill(db.Model):
    __tablename__ = 'bills'
    bill_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    recipient_id = db.Column(db.String(36), nullable=False)  # 'all' or user_id
    issued_by_user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'))
    issued_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(50), default='unpaid')

    issuer = db.relationship('User', backref='bills_issued_by_me')

    def to_dict(self):
        return {
            'bill_id': self.bill_id,
            'item_name': self.item_name,
            'amount': self.amount,
            'due_date': self.due_date.isoformat(),
            'recipient_id': self.recipient_id,
            'issued_by_user_id': self.issued_by_user_id,
            'issued_by_user_name': self.issuer.name if self.issuer else None,
            'issued_date': self.issued_date.isoformat(),
            'status': self.status
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bill_id = db.Column(db.String(36), db.ForeignKey('bills.bill_id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.user_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.now)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(50), default='pending')
    slip_path = db.Column(db.String(255))

    bill = db.relationship('Bill', backref='payments_for_bill')
    payer = db.relationship('User', backref='payments_made')

    def to_dict(self):
        return {
            'payment_id': self.payment_id,
            'bill_id': self.bill_id,
            'item_name': self.bill.item_name if self.bill else None,
            'user_id': self.user_id,
            'user_name': self.payer.name if self.payer else None,
            'amount': self.amount,
            'payment_date': self.payment_date.isoformat(),
            'payment_method': self.payment_method,
            'status': self.status,
            'slip_path': self.slip_path
        }

# --- Database Initialization ---
def populate_initial_data():
    """Populates the database with some initial data."""
    print("Database is empty. Populating with initial data...")
    try:
        # Create a default admin user
        admin_user = User(
            name='Admin User',
            username='admin',
            password_hash=generate_password_hash('admin123'),
            phone='0987654321',
            email='admin@smartvillage.com',
            address='Admin House 1',
            role='admin',
            status='approved'
        )
        db.session.add(admin_user)

        # Create a default resident user
        resident_user = User(
            name='Resident User',
            username='resident',
            password_hash=generate_password_hash('resident123'),
            phone='0812345678',
            email='resident@smartvillage.com',
            address='House A-101',
            role='resident',
            status='approved'
        )
        db.session.add(resident_user)

        # Create a pending resident user
        pending_user = User(
            name='Pending User',
            username='pending',
            password_hash=generate_password_hash('pending123'),
            phone='0801112222',
            email='pending@smartvillage.com',
            address='House B-202',
            role='resident',
            status='pending'
        )
        db.session.add(pending_user)

        db.session.flush()

        # Announcements
        announcement1 = Announcement(
            title='ประชุมคณะกรรมการประจำเดือน',
            content='เรียนเชิญสมาชิกทุกท่านเข้าร่วมประชุมคณะกรรมการประจำเดือน พฤศจิกายน 2567 ในวันที่ 15 พฤศจิกายน 2567 เวลา 19:00 น. ณ ห้องประชุมอาคาร A',
            published_date=datetime.now() - timedelta(days=5),
            author_id=admin_user.user_id,
            tag='สำคัญ',
            tag_color='#1976d2',
            tag_bg='#e3f2fd'
        )
        
        announcement2 = Announcement(
            title='กิจกรรมทำความสะอาดหมู่บ้าน',
            content='ขอเชิญชวนสมาชิกทุกครอบครัวร่วมกิจกรรมทำความสะอาดหมู่บ้าน ในวันเสาร์ที่ 18 พฤศจิกายน 2567 เวลา 08:00-12:00 น. จุดนัดพบ: ลานจอดรถกลาง',
            published_date=datetime.now() - timedelta(days=7),
            author_id=admin_user.user_id,
            tag='กิจกรรม',
            tag_color='#2e7d32',
            tag_bg='#e8f5e8'
        )
        
        db.session.add_all([announcement1, announcement2])

        # Repair Requests
        repair1 = RepairRequest(
            user_id=resident_user.user_id,
            title='ไฟทางเดินเสีย',
            category='ไฟฟ้า',
            description='ไฟทางเดินหน้าบ้านเลขที่ A-101 เสีย ไม่ติดมา 2 วันแล้ว',
            submitted_date=datetime.now() - timedelta(days=3),
            status='pending'
        )
        
        repair2 = RepairRequest(
            user_id=resident_user.user_id,
            title='น้ำรั่วซึม',
            category='น้ำประปา',
            description='ท่อน้ำประปาหน้าบ้านเลขที่ A-101 มีน้ำรั่วซึมเล็กน้อย',
            submitted_date=datetime.now() - timedelta(days=7),
            status='in_progress'
        )
        
        db.session.add_all([repair1, repair2])

        # Booking Requests
        booking1 = BookingRequest(
            user_id=resident_user.user_id,
            location='สนามกีฬา',
            date=datetime.now().date() + timedelta(days=5),
            start_time='14:00',
            end_time='16:00',
            purpose='เล่นฟุตบอล',
            attendee_count=10,
            status='approved'
        )
        
        booking2 = BookingRequest(
            user_id=resident_user.user_id,
            location='คลับเฮ้าส์',
            date=datetime.now().date() + timedelta(days=12),
            start_time='18:00',
            end_time='22:00', # FIX: ถูกตัดในโค้ดเดิม
            purpose='จัดงานวันเกิด', # FIX: ถูกตัดในโค้ดเดิม
            attendee_count=25,
            status='pending'
        )
        
        db.session.add_all([booking1, booking2])

        # Bills
        bill1 = Bill(
            item_name='ค่าส่วนกลาง เดือน พ.ย. 67',
            amount=1500.00,
            due_date=datetime.now().date() + timedelta(days=30),
            recipient_id='all',
            issued_by_user_id=admin_user.user_id,
            status='unpaid'
        )
        bill2 = Bill(
            item_name='ค่าจอดรถเพิ่มเติม',
            amount=300.00,
            due_date=datetime.now().date() + timedelta(days=15),
            recipient_id=resident_user.user_id,
            issued_by_user_id=admin_user.user_id,
            status='unpaid'
        )
        bill3 = Bill(
            item_name='ค่าส่วนกลาง เดือน ต.ค. 67',
            amount=1500.00,
            due_date=datetime.now().date() - timedelta(days=10),
            recipient_id='all',
            issued_by_user_id=admin_user.user_id,
            status='paid'
        )
        db.session.add_all([bill1, bill2, bill3])
        db.session.flush()

        # Payment for bill3
        payment1 = Payment(
            bill_id=bill3.bill_id,
            user_id=resident_user.user_id,
            amount=1500.00,
            payment_date=datetime.now() - timedelta(days=15),
            payment_method='bank_transfer',
            status='paid',
            slip_path='slip_oct_resident.jpg'
        )
        db.session.add(payment1)
        db.session.commit()
        print("Initial data populated successfully.")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error populating initial data: {e}")
    except Exception as e:
        db.session.rollback()
        print(f"An unexpected error occurred during data population: {e}")

# --- Routes ---
@app.route('/')
def home():
    return "Smart Village Backend is running!"

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Auth Routes ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    if user.status != 'approved':
        return jsonify({'message': f'Your account is {user.status}. Please contact admin.'}), 403
    
    return jsonify({
        'message': 'Login successful',
        'user_id': user.user_id,
        'name': user.name,
        'username': user.username,
        'phone': user.phone,
        'email': user.email,
        'address': user.address,
        'role': user.role
    }), 200

# --- User Routes (CRUD) ---
@app.route('/users', methods=['POST'])
def create_user(): # TC-006, TC-007 (Duplicate Username)
    data = request.get_json()
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')
    email = data.get('email')
    address = data.get('address')
    role = data.get('role', 'resident')
    status = data.get('status', 'pending')
    
    if not name or not username or not password:
        return jsonify({'message': 'Name, username, and password are required'}), 400

    try:
        new_user = User(
            name=name,
            username=username,
            password_hash=generate_password_hash(password),
            phone=phone,
            email=email,
            address=address,
            role=role,
            status=status
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Username already exists'}), 409
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating user: {e}")
        return jsonify({'message': 'An error occurred during user creation'}), 500

@app.route('/users', methods=['GET'])
def get_users(): # TC-008
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id): # TC-009
    user = User.query.get(user_id)
    if user:
        return jsonify(user.to_dict()), 200
    return jsonify({'message': 'User not found'}), 404

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id): # TC-010
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    try:
        if 'name' in data:
            user.name = data['name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'email' in data:
            user.email = data['email']
        if 'address' in data:
            user.address = data['address']
        if 'role' in data:
            user.role = data['role']
        if 'status' in data:
            user.status = data['status']
        if 'password' in data and data['password']:
            user.password_hash = generate_password_hash(data['password'])

        db.session.commit()
        return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating user: {e}")
        return jsonify({'message': 'An error occurred during user update'}), 500

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id): # TC-011
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting user: {e}")
        return jsonify({'message': 'An error occurred during user deletion'}), 500

# --- Announcement Routes (CRUD) ---
@app.route('/announcements', methods=['POST'])
def create_announcement(): # TC-012
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    author_id = data.get('author_id')
    tag = data.get('tag')
    tag_color = data.get('tag_color')
    tag_bg = data.get('tag_bg')
    
    if not title or not content or not author_id:
        return jsonify({'message': 'Title, content, and author_id are required'}), 400

    if not User.query.get(author_id):
        return jsonify({'message': 'Author not found'}), 404

    try:
        new_announcement = Announcement(
            title=title,
            content=content,
            author_id=author_id,
            tag=tag,
            tag_color=tag_color,
            tag_bg=tag_bg,
            published_date=datetime.fromisoformat(data.get('published_date')) if data.get('published_date') else datetime.now()
        )
        db.session.add(new_announcement)
        db.session.commit()
        return jsonify({'message': 'Announcement created successfully', 'announcement': new_announcement.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating announcement: {e}")
        return jsonify({'message': 'An error occurred during announcement creation'}), 500

@app.route('/announcements', methods=['GET'])
def get_announcements(): # TC-013
    announcements = Announcement.query.order_by(Announcement.published_date.desc()).all()
    return jsonify([ann.to_dict() for ann in announcements]), 200

@app.route('/announcements/<announcement_id>', methods=['PUT'])
def update_announcement(announcement_id): # TC-014
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'message': 'Announcement not found'}), 404

    data = request.get_json()
    try:
        if 'title' in data:
            announcement.title = data['title']
        if 'content' in data:
            announcement.content = data['content']
        if 'tag' in data:
            announcement.tag = data['tag']
        if 'tag_color' in data:
            announcement.tag_color = data['tag_color']
        if 'tag_bg' in data:
            announcement.tag_bg = data['tag_bg']

        db.session.commit()
        return jsonify({'message': 'Announcement updated successfully', 'announcement': announcement.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating announcement: {e}")
        return jsonify({'message': 'An error occurred during announcement update'}), 500

@app.route('/announcements/<announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id): # TC-015
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'message': 'Announcement not found'}), 404

    try:
        db.session.delete(announcement)
        db.session.commit()
        return jsonify({'message': 'Announcement deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting announcement: {e}")
        return jsonify({'message': 'An error occurred during announcement deletion'}), 500

# --- Repair Request Routes ---
@app.route('/repair-requests', methods=['POST'])
def create_repair_request(): # TC-016
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    category = data.get('category')
    description = data.get('description')
    image_paths = data.get('image_paths')
    
    if not user_id or not title:
        return jsonify({'message': 'User ID and title are required'}), 400

    if not User.query.get(user_id):
        return jsonify({'message': 'User not found'}), 404

    try:
        new_request = RepairRequest(
            user_id=user_id,
            title=title,
            category=category,
            description=description,
            image_paths=image_paths,
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
        return jsonify({'message': 'Repair request created successfully', 'request': new_request.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating repair request: {e}")
        return jsonify({'message': 'An error occurred during repair request creation'}), 500

@app.route('/repair-requests', methods=['GET'])
def get_repair_requests(): # TC-017, TC-019 (Filter)
    query = RepairRequest.query.order_by(RepairRequest.submitted_date.desc())
    
    user_id = request.args.get('user_id')
    if user_id: # TC-019
        query = query.filter_by(user_id=user_id)

    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    requests_list = query.all()
    return jsonify([req.to_dict() for req in requests_list]), 200

@app.route('/repair-requests/<request_id>', methods=['PUT'])
def update_repair_request(request_id): # TC-018
    request_obj = RepairRequest.query.get(request_id)
    if not request_obj:
        return jsonify({'message': 'Repair request not found'}), 404

    data = request.get_json()
    try:
        if 'status' in data:
            request_obj.status = data['status']
        if 'title' in data:
            request_obj.title = data['title']
        if 'description' in data:
            request_obj.description = data['description']
        
        db.session.commit()
        return jsonify({'message': 'Repair request updated successfully', 'request': request_obj.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating repair request: {e}")
        return jsonify({'message': 'An error occurred during repair request update'}), 500

# --- Booking Request Routes ---
def time_to_minutes(time_str):
    """Convert time string ('HH:MM') to minutes since midnight."""
    try:
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    except:
        return -1 # Invalid time

def check_booking_conflict(location, date_str, start_time, end_time, exclude_id=None):
    """Helper function to check for approved booking conflicts (TC-022)."""
    try:
        new_start_min = time_to_minutes(start_time)
        new_end_min = time_to_minutes(end_time)

        if new_start_min < 0 or new_end_min < 0 or new_start_min >= new_end_min:
            return True # Invalid time range treated as conflict for safety

        # Query existing APPROVED bookings for the same location and date
        conflict_query = BookingRequest.query.filter(
            BookingRequest.location == location,
            BookingRequest.date == date.fromisoformat(date_str),
            BookingRequest.status == 'approved'
        )

        if exclude_id:
            conflict_query = conflict_query.filter(BookingRequest.booking_id != exclude_id)
            
        existing_bookings = conflict_query.all()
        
        for booking in existing_bookings:
            existing_start_min = time_to_minutes(booking.start_time)
            existing_end_min = time_to_minutes(booking.end_time)
            
            # Check for overlap: [new_start < existing_end] AND [new_end > existing_start]
            if (new_start_min < existing_end_min) and (new_end_min > existing_start_min):
                return True # Conflict found

        return False # No conflict
        
    except ValueError:
        app.logger.error("Invalid date/time format in booking conflict check")
        return True # Treat as conflict if data is bad

@app.route('/booking-requests', methods=['POST'])
def create_booking_request(): # TC-020, TC-022 (Conflict)
    data = request.get_json()
    user_id = data.get('user_id')
    location = data.get('location')
    date_str = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    purpose = data.get('purpose')
    attendee_count = data.get('attendee_count')

    if not all([user_id, location, date_str, start_time, end_time]):
        return jsonify({'message': 'User ID, location, date, start_time, and end_time are required'}), 400

    if not User.query.get(user_id):
        return jsonify({'message': 'User not found'}), 404
        
    # Check for conflict first (TC-022)
    if check_booking_conflict(location, date_str, start_time, end_time):
        return jsonify({'message': 'The selected time slot for this location is already booked (approved)'}), 409

    try:
        new_request = BookingRequest(
            user_id=user_id,
            location=location,
            date=date.fromisoformat(date_str),
            start_time=start_time,
            end_time=end_time,
            purpose=purpose,
            attendee_count=attendee_count,
            status='pending'
        )
        db.session.add(new_request)
        db.session.commit()
        return jsonify({'message': 'Booking request created successfully', 'booking': new_request.to_dict()}), 201
    except ValueError:
        db.session.rollback()
        return jsonify({'message': 'Invalid date format. Use ISO format (YYYY-MM-DD)'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating booking request: {e}")
        return jsonify({'message': 'An error occurred during booking request creation'}), 500


@app.route('/booking-requests', methods=['GET'])
def get_booking_requests(): # TC-021
    query = BookingRequest.query.order_by(BookingRequest.requested_at.desc())
    
    # Optional filtering
    user_id = request.args.get('user_id')
    if user_id:
        query = query.filter_by(user_id=user_id)
        
    bookings = query.all()
    return jsonify([booking.to_dict() for booking in bookings]), 200

@app.route('/booking-requests/<booking_id>', methods=['PUT'])
def update_booking_request(booking_id): # TC-023
    booking_obj = BookingRequest.query.get(booking_id)
    if not booking_obj:
        return jsonify({'message': 'Booking request not found'}), 404

    data = request.get_json()
    try:
        # Prevent conflict during status change to 'approved'
        if 'status' in data and data['status'] == 'approved' and booking_obj.status != 'approved':
            # Check for conflict with existing APPROVED bookings, excluding the current one
            if check_booking_conflict(
                booking_obj.location, 
                booking_obj.date.isoformat(), 
                booking_obj.start_time, 
                booking_obj.end_time, 
                exclude_id=booking_obj.booking_id
            ):
                return jsonify({'message': 'Cannot approve. Conflict with an existing approved booking'}), 409
        
        if 'status' in data:
            booking_obj.status = data['status']
        if 'purpose' in data:
            booking_obj.purpose = data['purpose']

        db.session.commit()
        return jsonify({'message': 'Booking request updated successfully', 'booking': booking_obj.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating booking request: {e}")
        return jsonify({'message': 'An error occurred during booking request update'}), 500

@app.route('/booking-requests/<booking_id>', methods=['DELETE'])
def delete_booking_request(booking_id): 
    booking_obj = BookingRequest.query.get(booking_id)
    if not booking_obj:
        return jsonify({'message': 'Booking request not found'}), 404

    try:
        db.session.delete(booking_obj)
        db.session.commit()
        return jsonify({'message': 'Booking request deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting booking request: {e}")
        return jsonify({'message': 'An error occurred during booking request deletion'}), 500

# --- Bill Routes (CRUD) ---
@app.route('/bills', methods=['POST'])
def create_bill():
    data = request.get_json()
    item_name = data.get('item_name')
    amount = data.get('amount')
    due_date_str = data.get('due_date')
    recipient_id = data.get('recipient_id')
    issued_by_user_id = data.get('issued_by_user_id')

    if not all([item_name, amount, due_date_str, recipient_id, issued_by_user_id]):
        return jsonify({'message': 'Missing required fields'}), 400

    if recipient_id != 'all' and not User.query.get(recipient_id):
        return jsonify({'message': 'Recipient user not found'}), 404
        
    if not User.query.get(issued_by_user_id):
        return jsonify({'message': 'Issuer user not found'}), 404

    try:
        new_bill = Bill(
            item_name=item_name,
            amount=float(amount),
            due_date=date.fromisoformat(due_date_str),
            recipient_id=recipient_id,
            issued_by_user_id=issued_by_user_id,
            status='unpaid'
        )
        db.session.add(new_bill)
        db.session.commit()
        return jsonify({'message': 'Bill created successfully', 'bill': new_bill.to_dict()}), 201
    except ValueError:
        db.session.rollback()
        return jsonify({'message': 'Invalid date or amount format'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating bill: {e}")
        return jsonify({'message': 'An error occurred during bill creation'}), 500

@app.route('/bills', methods=['GET'])
def get_bills():
    query = Bill.query.order_by(Bill.issued_date.desc())
    
    recipient_id = request.args.get('recipient_id')
    if recipient_id:
        # Filter by recipient_id or 'all'
        query = query.filter(
            (Bill.recipient_id == recipient_id) | (Bill.recipient_id == 'all')
        )
        
    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)
        
    bills = query.all()
    return jsonify([bill.to_dict() for bill in bills]), 200

@app.route('/bills/<bill_id>', methods=['PUT'])
def update_bill(bill_id):
    bill_obj = Bill.query.get(bill_id)
    if not bill_obj:
        return jsonify({'message': 'Bill not found'}), 404

    data = request.get_json()
    try:
        if 'item_name' in data:
            bill_obj.item_name = data['item_name']
        if 'amount' in data:
            bill_obj.amount = float(data['amount'])
        if 'due_date' in data:
            bill_obj.due_date = date.fromisoformat(data['due_date'])
        if 'status' in data:
            bill_obj.status = data['status']
            
        db.session.commit()
        return jsonify({'message': 'Bill updated successfully', 'bill': bill_obj.to_dict()}), 200
    except ValueError:
        db.session.rollback()
        return jsonify({'message': 'Invalid date or amount format'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating bill: {e}")
        return jsonify({'message': 'An error occurred during bill update'}), 500

@app.route('/bills/<bill_id>', methods=['DELETE'])
def delete_bill(bill_id):
    bill_obj = Bill.query.get(bill_id)
    if not bill_obj:
        return jsonify({'message': 'Bill not found'}), 404

    try:
        # Delete associated payments before deleting the bill
        Payment.query.filter_by(bill_id=bill_id).delete()
        
        db.session.delete(bill_obj)
        db.session.commit()
        return jsonify({'message': 'Bill deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting bill: {e}")
        return jsonify({'message': 'An error occurred during bill deletion'}), 500

# --- Payment Routes (CRUD) ---
@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    bill_id = data.get('bill_id')
    user_id = data.get('user_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method')
    slip_path = data.get('slip_path')
    
    if not all([bill_id, user_id, amount]):
        return jsonify({'message': 'Bill ID, User ID, and amount are required'}), 400

    bill = Bill.query.get(bill_id)
    user = User.query.get(user_id)
    if not bill or not user:
        return jsonify({'message': 'Bill or User not found'}), 404

    try:
        new_payment = Payment(
            bill_id=bill_id,
            user_id=user_id,
            amount=float(amount),
            payment_method=payment_method,
            slip_path=slip_path,
            status='pending' # Initial status is pending review
        )
        db.session.add(new_payment)
        db.session.commit()
        
        return jsonify({'message': 'Payment submitted successfully', 'payment': new_payment.to_dict()}), 201
    except ValueError:
        db.session.rollback()
        return jsonify({'message': 'Invalid amount format'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating payment: {e}")
        return jsonify({'message': 'An error occurred during payment submission'}), 500

@app.route('/payments', methods=['GET'])
def get_payments():
    query = Payment.query.order_by(Payment.payment_date.desc())
    
    user_id = request.args.get('user_id')
    bill_id = request.args.get('bill_id')
    status = request.args.get('status')
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    if bill_id:
        query = query.filter_by(bill_id=bill_id)
    if status:
        query = query.filter_by(status=status)
        
    payments = query.all()
    return jsonify([payment.to_dict() for payment in payments]), 200

@app.route('/payments/<payment_id>', methods=['PUT'])
def update_payment(payment_id):
    payment_obj = Payment.query.get(payment_id)
    if not payment_obj:
        return jsonify({'message': 'Payment not found'}), 404

    data = request.get_json()
    try:
        new_status = data.get('status')
        
        if new_status and new_status != payment_obj.status:
            # Prevent re-approving/re-rejecting an already processed payment
            if payment_obj.status in ['paid', 'rejected']:
                 return jsonify({'message': f'Payment is already {payment_obj.status} and cannot be modified'}), 400
                 
            payment_obj.status = new_status
            
            # If approved, update the corresponding bill status to 'paid'
            if new_status == 'paid':
                bill = Bill.query.get(payment_obj.bill_id)
                if bill:
                    bill.status = 'paid'
                    
        db.session.commit()
        return jsonify({'message': 'Payment updated successfully', 'payment': payment_obj.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating payment: {e}")
        return jsonify({'message': 'An error occurred during payment update'}), 500

# --- File Upload Routes ---
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Create a unique filename to prevent overwrites
        filename_ext = secure_filename(file.filename).rsplit('.', 1)
        unique_filename = f"{uuid.uuid4().hex}.{filename_ext[1]}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Return the public URL path
        file_url = f"/uploads/{unique_filename}"
        return jsonify({'message': 'File uploaded successfully', 'file_path': file_url}), 201
    
    return jsonify({'message': 'File type not allowed'}), 400

@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_files():
    if 'files' not in request.files:
        return jsonify({'message': 'No files part'}), 400

    uploaded_files = request.files.getlist('files')
    file_urls = []
    
    for file in uploaded_files:
        if file.filename == '':
            continue
        
        if file and allowed_file(file.filename):
            filename_ext = secure_filename(file.filename).rsplit('.', 1)
            unique_filename = f"{uuid.uuid4().hex}.{filename_ext[1]}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            file_urls.append(f"/uploads/{unique_filename}")
        else:
            return jsonify({'message': f'File type not allowed for file: {file.filename}'}), 400

    if not file_urls:
        return jsonify({'message': 'No valid files uploaded'}), 400

    return jsonify({'message': 'Files uploaded successfully', 'file_paths': file_urls}), 201

# --- SocketIO Handlers (Same as original) ---
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_chat_room')
def handle_join_room(data):
    room_name = data.get('room_name')
    if room_name:
        join_room(room_name)
        print(f"Client {request.sid} joined room: {room_name}")

@socketio.on('leave_chat_room')
def handle_leave_room(data):
    room_name = data.get('room_name')
    if room_name:
        leave_room(room_name)
        print(f"Client {request.sid} left room: {room_name}")

@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data.get('sender_id')
    room_name = data.get('room_name')
    content = data.get('content')
    sender_name = data.get('sender_name', 'Unknown User')
    sender_avatar = data.get('sender_avatar', 'U')

    if not sender_id or not room_name or not content:
        emit('error', {'message': 'Missing message data'})
        return

    emit('receive_message', {
        'sender_id': sender_id,
        'sender_name': sender_name,
        'sender_avatar': sender_avatar,
        'room_name': room_name,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }, room=room_name)
    
    print(f"Message sent to room {room_name} by {sender_name}: {content}")

# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
        # Drop and recreate tables for a clean test environment 
        db.drop_all()
        db.create_all()
        
        # Populate with initial data
        if not User.query.first():
            populate_initial_data()
            
    # Run the Flask app with SocketIO
    socketio.run(app, debug=True)
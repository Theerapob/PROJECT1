import os
import uuid
from datetime import datetime, date, timedelta
import json

from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
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

# --- Models ---
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
            end_time='22:00',
            purpose='จัดงานวันเกิด',
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

# --- User Routes ---
@app.route('/users', methods=['POST'])
def create_user():
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

    hashed_password = generate_password_hash(password)

    new_user = User(
        name=name,
        username=username,
        password_hash=hashed_password,
        phone=phone,
        email=email,
        address=address,
        role=role,
        status=status
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User created successfully', 'user': new_user.to_dict()}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Username already exists'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    
    if 'password' in data and data['password']:
        if 'current_password' in data:
            current_password = data.get('current_password')
            if not check_password_hash(user.password_hash, current_password):
                return jsonify({'message': 'Incorrect current password'}), 401
        
        user.password_hash = generate_password_hash(data['password'])
        
    user.name = data.get('name', user.name)
    user.username = data.get('username', user.username)
    user.phone = data.get('phone', user.phone)
    user.email = data.get('email', user.email)
    user.address = data.get('address', user.address)
    user.role = data.get('role', user.role)
    user.status = data.get('status', user.status)

    try:
        db.session.commit()
        return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Username already exists'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating user: {str(e)}'}), 500

@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting user: {str(e)}'}), 500

# --- Announcement Routes ---
@app.route('/announcements', methods=['POST'])
def create_announcement():
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    published_date_str = data.get('published_date')
    author_id = data.get('author_id')
    tag = data.get('tag')

    if not title or not content or not author_id:
        return jsonify({'message': 'Title, content, and author_id are required'}), 400

    try:
        if published_date_str:
            published_date = datetime.fromisoformat(published_date_str.replace('Z', '+00:00'))
        else:
            published_date = datetime.now()
    except ValueError:
        return jsonify({'message': 'Invalid date format for published_date'}), 400

    tag_color = None
    tag_bg = None
    if tag == 'สำคัญ':
        tag_color = '#1976d2'
        tag_bg = '#e3f2fd'
    elif tag == 'กิจกรรม':
        tag_color = '#2e7d32'
        tag_bg = '#e8f5e8'
    elif tag == 'แจ้งเตือน':
        tag_color = '#856404'
        tag_bg = '#fff3cd'

    new_announcement = Announcement(
        title=title,
        content=content,
        published_date=published_date,
        author_id=author_id,
        tag=tag,
        tag_color=tag_color,
        tag_bg=tag_bg
    )
    
    try:
        db.session.add(new_announcement)
        db.session.commit()
        socketio.emit('new_announcement', new_announcement.to_dict())
        return jsonify({'message': 'Announcement created successfully', 'announcement': new_announcement.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating announcement: {str(e)}'}), 500

@app.route('/announcements', methods=['GET'])
def get_all_announcements():
    announcements = Announcement.query.order_by(Announcement.published_date.desc()).all()
    return jsonify([announcement.to_dict() for announcement in announcements]), 200

@app.route('/announcements/<announcement_id>', methods=['GET'])
def get_announcement(announcement_id):
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'message': 'Announcement not found'}), 404
    return jsonify(announcement.to_dict()), 200

@app.route('/announcements/<announcement_id>', methods=['PUT'])
def update_announcement(announcement_id):
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'message': 'Announcement not found'}), 404

    data = request.get_json()
    announcement.title = data.get('title', announcement.title)
    announcement.content = data.get('content', announcement.content)
    
    published_date_str = data.get('published_date')
    if published_date_str:
        try:
            announcement.published_date = datetime.fromisoformat(published_date_str.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'message': 'Invalid date format for published_date'}), 400
            
    announcement.tag = data.get('tag', announcement.tag)

    if announcement.tag == 'สำคัญ':
        announcement.tag_color = '#1976d2'
        announcement.tag_bg = '#e3f2fd'
    elif announcement.tag == 'กิจกรรม':
        announcement.tag_color = '#2e7d32'
        announcement.tag_bg = '#e8f5e8'
    elif announcement.tag == 'แจ้งเตือน':
        announcement.tag_color = '#856404'
        announcement.tag_bg = '#fff3cd'
    else:
        announcement.tag_color = None
        announcement.tag_bg = None

    try:
        db.session.commit()
        socketio.emit('announcement_updated', announcement.to_dict())
        return jsonify({'message': 'Announcement updated successfully', 'announcement': announcement.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating announcement: {str(e)}'}), 500

@app.route('/announcements/<announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    announcement = Announcement.query.get(announcement_id)
    if not announcement:
        return jsonify({'message': 'Announcement not found'}), 404

    try:
        db.session.delete(announcement)
        db.session.commit()
        socketio.emit('announcement_deleted', {'announcement_id': announcement_id})
        return jsonify({'message': 'Announcement deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting announcement: {str(e)}'}), 500

# --- Repair Request Routes ---
@app.route('/repair-requests', methods=['POST'])
def create_repair_request():
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    category = data.get('category')
    description = data.get('description')
    image_paths = data.get('image_paths')

    if not user_id or not title or not category:
        return jsonify({'message': 'User ID, title, and category are required'}), 400

    new_request = RepairRequest(
        user_id=user_id,
        title=title,
        category=category,
        description=description,
        image_paths=image_paths
    )
    
    try:
        db.session.add(new_request)
        db.session.commit()
        socketio.emit('new_repair_request', new_request.to_dict(), room='admins')
        return jsonify({'message': 'Repair request created successfully', 'request': new_request.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating repair request: {str(e)}'}), 500

@app.route('/repair-requests', methods=['GET'])
def get_all_repair_requests():
    user_id = request.args.get('user_id')
    if user_id:
        requests = RepairRequest.query.filter_by(user_id=user_id).order_by(RepairRequest.submitted_date.desc()).all()
    else:
        requests = RepairRequest.query.order_by(RepairRequest.submitted_date.desc()).all()
    return jsonify([req.to_dict() for req in requests]), 200

@app.route('/repair-requests/<request_id>', methods=['GET'])
def get_repair_request(request_id):
    req = RepairRequest.query.get(request_id)
    if not req:
        return jsonify({'message': 'Repair request not found'}), 404
    return jsonify(req.to_dict()), 200

@app.route('/repair-requests/<request_id>', methods=['PUT'])
def update_repair_request(request_id):
    req = RepairRequest.query.get(request_id)
    if not req:
        return jsonify({'message': 'Repair request not found'}), 404

    data = request.get_json()
    req.title = data.get('title', req.title)
    req.category = data.get('category', req.category)
    req.description = data.get('description', req.description)
    
    old_status = req.status
    req.status = data.get('status', req.status)
    req.image_paths = data.get('image_paths', req.image_paths)

    try:
        db.session.commit()
        if old_status != req.status:
            socketio.emit('repair_status_updated', req.to_dict(), room=req.user_id)
        return jsonify({'message': 'Repair request updated successfully', 'request': req.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating repair request: {str(e)}'}), 500

@app.route('/repair-requests/<request_id>', methods=['DELETE'])
def delete_repair_request(request_id):
    req = RepairRequest.query.get(request_id)
    if not req:
        return jsonify({'message': 'Repair request not found'}), 404

    try:
        db.session.delete(req)
        db.session.commit()
        return jsonify({'message': 'Repair request deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting repair request: {str(e)}'}), 500

# --- Booking Request Routes ---
@app.route('/booking-requests', methods=['POST'])
def create_booking_request():
    data = request.get_json()
    user_id = data.get('user_id')
    location = data.get('location')
    date_str = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')
    purpose = data.get('purpose')
    attendee_count = data.get('attendee_count')

    if not user_id or not location or not date_str or not start_time or not end_time:
        return jsonify({'message': 'User ID, location, date, start time, and end time are required'}), 400

    try:
        booking_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    new_booking = BookingRequest(
        user_id=user_id,
        location=location,
        date=booking_date,
        start_time=start_time,
        end_time=end_time,
        purpose=purpose,
        attendee_count=attendee_count
    )
    
    try:
        db.session.add(new_booking)
        db.session.commit()
        socketio.emit('new_booking_request', new_booking.to_dict(), room='admins')
        return jsonify({'message': 'Booking request created successfully', 'booking': new_booking.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating booking request: {str(e)}'}), 500

@app.route('/booking-requests', methods=['GET'])
def get_all_booking_requests():
    user_id = request.args.get('user_id')
    if user_id:
        requests = BookingRequest.query.filter_by(user_id=user_id).order_by(BookingRequest.date.desc(), BookingRequest.start_time.desc()).all()
    else:
        requests = BookingRequest.query.order_by(BookingRequest.date.desc(), BookingRequest.start_time.desc()).all()
    return jsonify([req.to_dict() for req in requests]), 200

@app.route('/booking-requests/<booking_id>', methods=['GET'])
def get_booking_request(booking_id):
    req = BookingRequest.query.get(booking_id)
    if not req:
        return jsonify({'message': 'Booking request not found'}), 404
    return jsonify(req.to_dict()), 200

@app.route('/booking-requests/<booking_id>', methods=['PUT'])
def update_booking_request(booking_id):
    req = BookingRequest.query.get(booking_id)
    if not req:
        return jsonify({'message': 'Booking request not found'}), 404

    data = request.get_json()
    req.location = data.get('location', req.location)
    
    date_str = data.get('date')
    if date_str:
        try:
            req.date = datetime.fromisoformat(date_str).date()
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    req.start_time = data.get('start_time', req.start_time)
    req.end_time = data.get('end_time', req.end_time)
    req.purpose = data.get('purpose', req.purpose)
    req.attendee_count = data.get('attendee_count', req.attendee_count)
    req.status = data.get('status', req.status)

    try:
        db.session.commit()
        return jsonify({'message': 'Booking request updated successfully', 'booking': req.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating booking request: {str(e)}'}), 500

@app.route('/booking-requests/<booking_id>', methods=['DELETE'])
def delete_booking_request(booking_id):
    req = BookingRequest.query.get(booking_id)
    if not req:
        return jsonify({'message': 'Booking request not found'}), 404

    try:
        db.session.delete(req)
        db.session.commit()
        return jsonify({'message': 'Booking request deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting booking request: {str(e)}'}), 500

# --- Bill Routes ---
@app.route('/bills', methods=['POST'])
def create_bill():
    data = request.get_json()
    item_name = data.get('item_name')
    amount = data.get('amount')
    due_date_str = data.get('due_date')
    recipient_id = data.get('recipient_id')
    issued_by_user_id = data.get('issued_by_user_id')

    if not item_name or amount is None or not due_date_str or not recipient_id or not issued_by_user_id:
        return jsonify({'message': 'Missing required fields'}), 400

    try:
        due_date = datetime.fromisoformat(due_date_str).date()
        amount = float(amount)
    except ValueError:
        return jsonify({'message': 'Invalid date or amount format'}), 400

    new_bill = Bill(
        item_name=item_name,
        amount=amount,
        due_date=due_date,
        recipient_id=recipient_id,
        issued_by_user_id=issued_by_user_id,
        status='unpaid'
    )
    
    try:
        db.session.add(new_bill)
        db.session.commit()
        socketio.emit('new_bill_created', new_bill.to_dict())
        return jsonify({'message': 'Bill created successfully', 'bill': new_bill.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating bill: {str(e)}'}), 500

@app.route('/bills', methods=['GET'])
def get_all_bills():
    user_id = request.args.get('user_id')
    
    if user_id:
        bills = Bill.query.filter(
            (Bill.recipient_id == user_id) | (Bill.recipient_id == 'all')
        ).order_by(Bill.issued_date.desc()).all()
    else:
        bills = Bill.query.order_by(Bill.issued_date.desc()).all()
    
    return jsonify([bill.to_dict() for bill in bills]), 200

@app.route('/bills/<bill_id>', methods=['GET'])
def get_bill(bill_id):
    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify({'message': 'Bill not found'}), 404
    return jsonify(bill.to_dict()), 200

@app.route('/bills/<bill_id>', methods=['PUT'])
def update_bill(bill_id):
    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify({'message': 'Bill not found'}), 404

    data = request.get_json()
    bill.item_name = data.get('item_name', bill.item_name)
    bill.amount = data.get('amount', bill.amount)
    
    due_date_str = data.get('due_date')
    if due_date_str:
        try:
            bill.due_date = datetime.fromisoformat(due_date_str).date()
        except ValueError:
            return jsonify({'message': 'Invalid date format for due_date'}), 400
            
    bill.recipient_id = data.get('recipient_id', bill.recipient_id)
    bill.status = data.get('status', bill.status)

    try:
        db.session.commit()
        socketio.emit('bill_updated', bill.to_dict())
        return jsonify({'message': 'Bill updated successfully', 'bill': bill.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating bill: {str(e)}'}), 500

@app.route('/bills/<bill_id>', methods=['DELETE'])
def delete_bill(bill_id):
    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify({'message': 'Bill not found'}), 404

    bill_data = bill.to_dict()
    
    try:
        db.session.delete(bill)
        db.session.commit()
        socketio.emit('bill_deleted', {'bill_id': bill_id, 'item_name': bill_data['item_name'], 'recipient_id': bill_data['recipient_id']})
        return jsonify({'message': 'Bill deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting bill: {str(e)}'}), 500

# --- Payment Routes ---
@app.route('/payments', methods=['POST'])
def create_payment():
    data = request.get_json()
    bill_id = data.get('bill_id')
    user_id = data.get('user_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method')
    slip_path = data.get('slip_path')

    if not bill_id or not user_id or amount is None or not payment_method:
        return jsonify({'message': 'Missing required fields'}), 400

    bill = Bill.query.get(bill_id)
    if not bill:
        return jsonify({'message': 'Bill not found'}), 404

    new_payment = Payment(
        bill_id=bill_id,
        user_id=user_id,
        amount=amount,
        payment_method=payment_method,
        slip_path=slip_path,
        status='pending'
    )
    
    try:
        db.session.add(new_payment)
        bill.status = 'pending_verification'
        db.session.commit()
        socketio.emit('new_payment_receipt', new_payment.to_dict(), room='admins')
        return jsonify({'message': 'Payment recorded successfully, awaiting verification', 'payment': new_payment.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error recording payment: {str(e)}'}), 500

@app.route('/payments', methods=['GET'])
def get_all_payments():
    user_id = request.args.get('user_id')
    if user_id:
        payments = Payment.query.filter_by(user_id=user_id).order_by(Payment.payment_date.desc()).all()
    else:
        payments = Payment.query.order_by(Payment.payment_date.desc()).all()
    return jsonify([payment.to_dict() for payment in payments]), 200

@app.route('/payments/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'message': 'Payment not found'}), 404
    return jsonify(payment.to_dict()), 200

@app.route('/payments/approve/<payment_id>', methods=['PUT'])
def approve_payment(payment_id):
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'message': 'Payment not found'}), 404

    if payment.status == 'paid':
        return jsonify({'message': 'Payment already approved'}), 400

    try:
        payment.status = 'paid'
        
        bill = Bill.query.get(payment.bill_id)
        if bill:
            bill.status = 'paid'

        db.session.commit()
        
        socketio.emit('payment_approved', payment_data, room=payment.user_id)
        socketio.emit('payment_approved', payment_data, room='admins')
        
        return jsonify({'message': 'Payment approved successfully', 'payment': payment.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error approving payment: {str(e)}'}), 500

@app.route('/payments/reject/<payment_id>', methods=['PUT'])
def reject_payment(payment_id):
    payment = Payment.query.get(payment_id)
    if not payment:
        return jsonify({'message': 'Payment not found'}), 404

    if payment.status == 'paid':
        return jsonify({'message': 'Cannot reject an already paid payment'}), 400

    try:
        payment.status = 'rejected'
        
        bill = Bill.query.get(payment.bill_id)
        if bill and bill.status == 'pending_verification':
            bill.status = 'unpaid'

        db.session.commit()
        return jsonify({'message': 'Payment rejected', 'payment': payment.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error rejecting payment: {str(e)}'}), 500

# --- SocketIO Events ---
@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)

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
        db.create_all()

        # Check if database needs initial data
        if User.query.count() == 0:
            populate_initial_data()
        else:
            print("Database already contains data. Skipping initial population.")

    # Run the app with SocketIO
    socketio.run(app, debug=True, port=5000)
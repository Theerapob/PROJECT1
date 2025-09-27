-- ตารางผู้ใช้ (Users)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(255),
    role VARCHAR(50) DEFAULT 'resident' NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางประกาศ (Announcements)
CREATE TABLE announcements (
    announcement_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    published_date DATE NOT NULL,
    author_id INTEGER REFERENCES users(user_id),
    author_name VARCHAR(255),
    tag VARCHAR(100),
    tag_color VARCHAR(7),
    tag_bg VARCHAR(7),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางคำร้องซ่อม (Repair Requests)
CREATE TABLE repair_requests (
    request_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    user_name VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    image_paths TEXT,
    submitted_date DATE DEFAULT CURRENT_DATE,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    assigned_to INTEGER REFERENCES users(user_id),
    completed_date DATE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางบิล (Bills)
CREATE TABLE bills (
    bill_id SERIAL PRIMARY KEY,
    item_name VARCHAR(255) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    due_date DATE NOT NULL,
    recipient_id VARCHAR(255) NOT NULL,
    issued_by_user_id INTEGER REFERENCES users(user_id),
    status VARCHAR(50) DEFAULT 'unpaid' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางการชำระเงิน (Payments)
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    bill_id INTEGER NOT NULL REFERENCES bills(bill_id),
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    amount NUMERIC(10,2) NOT NULL,
    payment_method VARCHAR(100) NOT NULL,
    slip_path VARCHAR(255),
    payment_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางคำร้องจองสถานที่ (Booking Requests)
CREATE TABLE booking_requests (
    booking_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    user_name VARCHAR(255),
    location VARCHAR(255) NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    purpose TEXT,
    attendee_count INTEGER,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางกิจกรรมปฏิทิน (Calendar Events)
CREATE TABLE calendar_events (
    event_id SERIAL PRIMARY KEY,
    event_name VARCHAR(255) NOT NULL,
    event_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    location VARCHAR(255),
    description TEXT,
    created_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางข้อความแชท (Chat Messages)
CREATE TABLE chat_messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INTEGER NOT NULL REFERENCES users(user_id),
    sender_name VARCHAR(255),
    sender_avatar VARCHAR(10),
    room_name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางเอกสาร (Documents)
CREATE TABLE documents (
    document_id SERIAL PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_by_user_id INTEGER NOT NULL REFERENCES users(user_id),
    category VARCHAR(100),
    upload_date DATE DEFAULT CURRENT_DATE,
    file_size VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางผู้มาติดต่อรักษาความปลอดภัย (Security Visitors)
CREATE TABLE security_visitors (
    visitor_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    visit_date DATE NOT NULL,
    visit_time TIME NOT NULL,
    purpose TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางเหตุการณ์รักษาความปลอดภัย (Security Incidents)
CREATE TABLE security_incidents (
    incident_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    user_name VARCHAR(255),
    description TEXT NOT NULL,
    evidence_paths TEXT,
    reported_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตารางโหวต (Voting Polls)
CREATE TABLE voting_polls (
    poll_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE DEFAULT CURRENT_DATE,
    end_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'open' NOT NULL,
    created_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ตัวเลือกโหวต (Voting Options)
CREATE TABLE voting_options (
    option_id SERIAL PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES voting_polls(poll_id),
    option_text VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ผลโหวต (Voting Results)
CREATE TABLE voting_results (
    result_id SERIAL PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES voting_polls(poll_id),
    option_id INTEGER NOT NULL REFERENCES voting_options(option_id),
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    voted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (poll_id, user_id)
);
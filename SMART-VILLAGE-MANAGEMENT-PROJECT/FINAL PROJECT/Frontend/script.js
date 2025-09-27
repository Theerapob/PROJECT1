// script.js - Fixed Version

// --- Global Data Variables ---
let currentUser = {
    user_id: null,
    name: 'ผู้ใช้งาน',
    role: 'resident',
    avatar: 'A',
    phone: '',
    email: '',
    address: ''
};

let currentDate = new Date();
let currentMonth = currentDate.getMonth();
let currentYear = currentDate.getFullYear();

const monthNames = [
    'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
    'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
];

// Data caches
let announcementsCache = [];
let repairRequestsCache = [];
let bookingRequestsCache = [];
let allUsersCache = [];
let billsCache = [];
let paymentsCache = [];

// Socket.IO Client
let socket = null;

// --- Utility Functions ---
function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notificationContainer');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.closest('.notification').remove()" style="background: none; border: none; color: inherit; font-size: 18px; cursor: pointer; padding: 0; margin-left: 10px;">&times;</button>
        </div>
    `;
    container.appendChild(notification);
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
        const form = modal.querySelector('form');
        if (form) form.reset();
        modal.querySelectorAll('[id$="Preview"]').forEach(p => p.innerHTML = '');
    }
}

function togglePasswordVisibility(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const icon = input.nextElementSibling;
    input.type = input.type === 'password' ? 'text' : 'password';
    if (icon) {
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
    }
}

function handleFileUpload(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    if (!input || !preview || !input.files || !input.files[0]) {
        if (preview) preview.innerHTML = '';
        return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.innerHTML = `<img src="${e.target.result}" style="max-width: 200px; max-height: 200px; margin-top: 10px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">`;
    };
    reader.readAsDataURL(input.files[0]);
}

// Generic API Functions
async function fetchData(endpoint) {
    try {
        const response = await fetch(`http://localhost:5000/${endpoint}`);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `Failed to fetch ${endpoint}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        showNotification(`ไม่สามารถโหลดข้อมูล ${endpoint} ได้`, 'error');
        return [];
    }
}

async function sendData(endpoint, method, body = null) {
    try {
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: body ? JSON.stringify(body) : undefined,
        };
        const response = await fetch(`http://localhost:5000/${endpoint}`, options);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || `API call to ${endpoint} failed`);
        }
        return data;
    } catch (error) {
        console.error(`Error sending data to ${endpoint}:`, error);
        showNotification(error.message || 'เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์', 'error');
        throw error;
    }
}

// --- Authentication Functions ---
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    try {
        const data = await sendData('login', 'POST', { username, password });
        currentUser = {
            user_id: data.user_id,
            name: data.name,
            role: data.role,
            avatar: data.name[0].toUpperCase(),
            phone: data.phone || '',
            email: data.email || '',
            address: data.address || ''
        };
        sessionStorage.setItem('isLoggedIn', 'true');
        sessionStorage.setItem('userData', JSON.stringify(currentUser));
        showNotification('เข้าสู่ระบบสำเร็จ', 'success');
        showDashboard();
        initializeSocketIO();
    } catch (error) {
        // Error handled by sendData
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('regName').value;
    const username = document.getElementById('regUsername').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;
    const phone = document.getElementById('regPhone').value;
    const email = document.getElementById('regEmail').value;
    const address = document.getElementById('regAddress').value;

    if (password !== confirmPassword) {
        showNotification('รหัสผ่านไม่ตรงกัน', 'error');
        return;
    }

    try {
        await sendData('users', 'POST', {
            name, username, password, phone, email, address, role: 'resident'
        });
        showNotification('ส่งคำขอลงทะเบียนสำเร็จ รอการอนุมัติจากผู้ดูแล', 'success');
        document.getElementById('registerForm').reset();
        setTimeout(() => showLogin(), 2000);
    } catch (error) {
        // Error handled by sendData
    }
}

function logout() {
    sessionStorage.removeItem('isLoggedIn');
    sessionStorage.removeItem('userData');
    currentUser = {
        user_id: null,
        name: 'ผู้ใช้งาน',
        role: 'resident',
        avatar: 'A',
        phone: '',
        email: '',
        address: ''
    };
    if (socket && socket.connected) {
        socket.disconnect();
    }
    showNotification('ออกจากระบบแล้ว', 'success');
    showLogin();
}

function showForgotPassword() {
    showNotification('ส่งลิงก์รีเซ็ตรหัสผ่านไปยังอีเมลของคุณแล้ว', 'info');
}

// --- Page Navigation Functions ---
const pageMap = {
    'dashboard-home': { id: 'dashboard-home', loadFunc: loadDashboardStats },
    'profile': { id: 'profile', loadFunc: loadProfileData },
    'repair-request': { id: 'repair-request', loadFunc: fetchRepairRequests },
    'announcements': { id: 'announcements', loadFunc: fetchAnnouncements },
    'payments': { id: 'payments', loadFunc: fetchPayments },
    'booking': { id: 'booking', loadFunc: fetchBookingRequests },
    'calendar': { id: 'calendar', loadFunc: loadCalendarData },
    'chat': { id: 'chat', loadFunc: loadChatData },
    'documents': { id: 'documents', loadFunc: loadDocumentsData },
    'security': { id: 'security', loadFunc: loadSecurityData },
    'voting': { id: 'voting', loadFunc: loadVotingData },
    'manage-users': { id: 'manage-users', loadFunc: fetchAllUsers },
    'manage-repairs': { id: 'manage-repairs', loadFunc: fetchRepairRequests },
    'manage-bills': { id: 'manage-bills', loadFunc: fetchBills },
    'reports': { id: 'reports', loadFunc: renderMonthlyChart }
};

function showLogin() {
    document.getElementById('loginPage').classList.remove('hidden');
    document.getElementById('registerPage').classList.add('hidden');
    document.getElementById('dashboard').classList.add('hidden');
}

function showRegister() {
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('registerPage').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('loginPage').classList.add('hidden');
    document.getElementById('registerPage').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');
    updateUserInfo();
    showPage('dashboard-home');
}

function showPage(pageId) {
    const pageInfo = pageMap[pageId];
    if (!pageInfo) {
        console.error(`Page ID "${pageId}" not found.`);
        return;
    }

    // Hide all page content divs
    document.querySelectorAll('.page-content').forEach(pageDiv => {
        pageDiv.classList.add('hidden');
    });

    // Show target page
    const targetContentDiv = document.getElementById(pageInfo.id);
    if (targetContentDiv) {
        targetContentDiv.classList.remove('hidden');
    } else {
        console.error(`Content div "${pageInfo.id}" not found.`);
        return;
    }

    // Update active menu item
    document.querySelectorAll('.sidebar-menu a').forEach(item => {
        item.classList.remove('active');
    });
    const activeLink = document.querySelector(`.sidebar-menu a[onclick*="showPage('${pageId}')"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    // Load page data
    if (pageInfo.loadFunc) {
        pageInfo.loadFunc();
    }

    // Setup form listeners
    setupDynamicFormListeners();

    // Close sidebar on mobile
    if (window.innerWidth <= 768) {
        toggleSidebar();
    }
}

function updateUserInfo() {
    const userNameEl = document.getElementById('userName');
    const userRoleEl = document.getElementById('userRole');
    const userAvatarEl = document.getElementById('userAvatar');

    if (userNameEl) userNameEl.textContent = currentUser.name;
    if (userRoleEl) userRoleEl.textContent = currentUser.role === 'admin' ? 'ผู้ดูแลระบบ' : 'ผู้อยู่อาศัย';
    if (userAvatarEl) userAvatarEl.textContent = currentUser.avatar;

    // Show/hide admin menus
    document.querySelectorAll('.admin-menu').forEach(menu => {
        if (currentUser.role === 'admin') {
            menu.classList.remove('hidden');
        } else {
            menu.classList.add('hidden');
        }
    });

    // Show resident menus
    document.querySelectorAll('.resident-menu').forEach(menu => {
        menu.classList.remove('hidden');
    });
}

// --- Form Handlers ---
async function handleRepairSubmit(e) {
    e.preventDefault();
    const title = document.getElementById('repairTitle').value;
    const category = document.getElementById('repairCategory').value;
    const description = document.getElementById('repairDescription').value;
    const imagePaths = JSON.stringify([]);

    try {
        await sendData('repair-requests', 'POST', {
            user_id: currentUser.user_id,
            title,
            category,
            description,
            image_paths: imagePaths
        });
        showNotification('ส่งคำขอแจ้งซ่อมเรียบร้อยแล้ว', 'success');
        document.getElementById('repairForm').reset();
        const preview = document.getElementById('repairImagesPreview');
        if (preview) preview.innerHTML = '';
        fetchRepairRequests();
    } catch (error) {
        // Error handled by sendData
    }
}

async function handleBookingSubmit(e) {
    e.preventDefault();
    const location = document.getElementById('bookingLocation').value;
    const date = document.getElementById('bookingDate').value;
    const timeStart = document.getElementById('bookingTimeStart').value;
    const timeEnd = document.getElementById('bookingTimeEnd').value;
    const purpose = document.getElementById('bookingPurpose').value;
    const attendeeCount = document.getElementById('attendeeCount').value;

    try {
        await sendData('booking-requests', 'POST', {
            user_id: currentUser.user_id,
            location,
            date,
            start_time: timeStart,
            end_time: timeEnd,
            purpose,
            attendee_count: parseInt(attendeeCount)
        });
        showNotification('ส่งคำขอจองเรียบร้อยแล้ว', 'success');
        document.getElementById('bookingForm').reset();
        fetchBookingRequests();
    } catch (error) {
        // Error handled by sendData
    }
}

async function handlePaymentSubmit(e) {
    e.preventDefault();
    const billId = document.getElementById('paymentBillId').value;
    const amountStr = document.getElementById('paymentAmount').value;
    const paymentMethod = document.getElementById('paymentMethod').value;
    const slipFile = document.getElementById('paymentSlipFile')?.files[0];

    if (!slipFile) {
        showNotification('กรุณาอัปโหลดหลักฐานการโอนเงิน', 'error');
        return;
    }

    const amount = parseFloat(amountStr.replace(' บาท', '').replace(/,/g, ''));

    try {
        await sendData('payments', 'POST', {
            bill_id: parseInt(billId),
            user_id: currentUser.user_id,
            amount: amount,
            payment_method: paymentMethod,
            status: 'pending',
            slip_path: slipFile.name
        });
        showNotification('ส่งหลักฐานการชำระเงินเรียบร้อยแล้ว รอการตรวจสอบ', 'success');
        closeModal('paymentModal');
        fetchPayments();
    } catch (error) {
        // Error handled by sendData
    }
}

async function handleProfileUpdate(e) {
    e.preventDefault();
    const name = document.getElementById('profileName').value;
    const phone = document.getElementById('profilePhone').value;
    const email = document.getElementById('profileEmail').value;
    const address = document.getElementById('profileAddress').value;

    try {
        await sendData(`users/${currentUser.user_id}`, 'PUT', {
            name, phone, email, address
        });
        
        // Update current user data
        currentUser.name = name;
        currentUser.phone = phone;
        currentUser.email = email;
        currentUser.address = address;
        currentUser.avatar = name[0].toUpperCase();
        
        sessionStorage.setItem('userData', JSON.stringify(currentUser));
        updateUserInfo();
        showNotification('อัปเดตข้อมูลส่วนตัวเรียบร้อยแล้ว', 'success');
        
        const preview = document.getElementById('profileDocumentsPreview');
        if (preview) preview.innerHTML = '';
    } catch (error) {
        // Error handled by sendData
    }
}

async function handlePasswordChange(e) {
    e.preventDefault();
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmNewPassword = document.getElementById('confirmNewPassword').value;

    if (newPassword !== confirmNewPassword) {
        showNotification('รหัสผ่านใหม่ไม่ตรงกัน', 'error');
        return;
    }

    try {
        await sendData(`users/${currentUser.user_id}`, 'PUT', {
            password: newPassword,
            current_password: currentPassword
        });
        showNotification('เปลี่ยนรหัสผ่านสำเร็จ', 'success');
        document.getElementById('changePasswordForm').reset();
    } catch (error) {
        // Error handled by sendData
    }
}

async function handleUserSubmit(e) {
    e.preventDefault();
    const userId = document.getElementById('userId').value;
    const name = document.getElementById('userName').value;
    const username = document.getElementById('userUsername').value;
    const password = document.getElementById('userPassword').value;
    const phone = document.getElementById('userPhone').value;
    const email = document.getElementById('userEmail').value;
    const address = document.getElementById('userAddress').value;
    const role = document.getElementById('userRoleSelect').value;
    const status = document.getElementById('userStatusSelect').value;

    const userData = { name, username, phone, email, address, role, status };
    if (password) {
        userData.password = password;
    }

    try {
        if (userId) {
            await sendData(`users/${userId}`, 'PUT', userData);
            showNotification('อัปเดตข้อมูลผู้ใช้สำเร็จ', 'success');
        } else {
            if (!password) {
                showNotification('กรุณาระบุรหัสผ่านสำหรับผู้ใช้ใหม่', 'error');
                return;
            }
            await sendData('users', 'POST', userData);
            showNotification('เพิ่มผู้ใช้ใหม่สำเร็จ', 'success');
        }
        closeModal('userModal');
        fetchAllUsers();
    } catch (error) {
        // Error handled by sendData
    }
}

// --- Status Mapping ---
const STATUS_MAP = {
    'pending': { text: 'รอรับเรื่อง', class: 'status-pending' },
    'in_progress': { text: 'กำลังดำเนินการ', class: 'status-progress' },
    'completed': { text: 'เสร็จสิ้น', class: 'status-completed' },
    'rejected': { text: 'ถูกปฏิเสธ', class: 'status-unpaid' },
    'approved': { text: 'อนุมัติ', class: 'status-approved' },
    'unpaid': { text: 'ยังไม่ชำระ', class: 'status-unpaid' },
    'paid': { text: 'ชำระแล้ว', class: 'status-paid' },
    'pending_verification': { text: 'รอตรวจสอบ', class: 'status-pending' },
    'suspended': { text: 'ระงับ', class: 'status-unpaid' }
};

function getStatusHtml(status) {
    const info = STATUS_MAP[status] || { text: status, class: 'status-info' };
    return `<span class="status-badge ${info.class}">${info.text}</span>`;
}

// --- Table Rendering ---
function renderTable(data, tbodyId, columns, getActionsHtml, noDataMessage = 'ไม่มีข้อมูล') {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!data || data.length === 0) {
        const colSpan = columns.length + (getActionsHtml ? 1 : 0);
        tbody.innerHTML = `<tr><td colspan="${colSpan}" style="text-align: center; color: #666;">${noDataMessage}</td></tr>`;
        return;
    }

    data.forEach(item => {
        const row = document.createElement('tr');
        let rowHtml = '';
        
        columns.forEach(col => {
            let value = item[col.key];
            if (col.format && typeof col.format === 'function') {
                value = col.format(value, item);
            }
            rowHtml += `<td>${value || ''}</td>`;
        });

        if (getActionsHtml) {
            rowHtml += `<td>${getActionsHtml(item)}</td>`;
        }

        row.innerHTML = rowHtml;
        tbody.appendChild(row);
    });
}

// --- Data Fetching Functions ---
async function fetchAnnouncements() {
    announcementsCache = await fetchData('announcements');
    renderAnnouncements();
}

function renderAnnouncements() {
    const commonColumns = [
        { key: 'title', header: 'หัวข้อ' },
        { key: 'published_date', header: 'วันที่', format: (date) => new Date(date).toLocaleDateString('th-TH') },
        { key: 'author_name', header: 'โดย', format: (name) => name || 'ผู้ดูแลระบบ' }
    ];

    if (currentUser.role === 'admin') {
        renderTable(announcementsCache, 'adminAnnouncementsTable', commonColumns, (announcement) => `
            <button class="btn btn-secondary btn-sm" onclick="editAnnouncement('${announcement.announcement_id}')">แก้ไข</button>
            <button class="btn btn-secondary btn-sm" onclick="deleteAnnouncement('${announcement.announcement_id}')">ลบ</button>
        `, 'ไม่มีประกาศ');
    }

    // Render announcements list
    const announcementsList = document.getElementById('announcementsList');
    if (!announcementsList || !announcementsCache) return;

    announcementsList.innerHTML = announcementsCache.map(announcement => {
        const tagColors = {
            'สำคัญ': { bg: '#e3f2fd', color: '#1976d2' },
            'กิจกรรม': { bg: '#e8f5e8', color: '#2e7d32' },
            'แจ้งเตือน': { bg: '#fff3cd', color: '#856404' },
            'ทั่วไป': { bg: '#f0f0f0', color: '#555' }
        };
        const tagInfo = tagColors[announcement.tag] || tagColors['ทั่วไป'];

        return `
            <div class="announcement-item" style="border-left: 4px solid ${tagInfo.color}; padding-left: 20px; margin-bottom: 25px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <h4 style="color: #333; margin: 0;">${announcement.title}</h4>
                    <span style="color: #666; font-size: 14px;">${new Date(announcement.published_date).toLocaleDateString('th-TH')}</span>
                </div>
                <p style="color: #666; line-height: 1.6; margin-bottom: 10px;">${announcement.content}</p>
                <div style="display: flex; gap: 10px;">
                    <span class="status-badge" style="background: ${tagInfo.bg}; color: ${tagInfo.color};">${announcement.tag || 'ทั่วไป'}</span>
                    <span style="color: #666; font-size: 14px;"><i class="fas fa-user"></i> โดย: ${announcement.author_name || 'ผู้ดูแลระบบ'}</span>
                </div>
                <div class="admin-actions ${currentUser.role === 'admin' ? '' : 'hidden'}" style="margin-top: 15px;">
                    <button class="btn btn-secondary btn-sm" onclick="editAnnouncement('${announcement.announcement_id}')">แก้ไข</button>
                    <button class="btn btn-secondary btn-sm" onclick="deleteAnnouncement('${announcement.announcement_id}')">ลบ</button>
                </div>
            </div>
        `;
    }).join('');
}

async function showAddAnnouncementModal() {
    document.getElementById('announcementModalTitle').innerText = 'เพิ่มประกาศใหม่';
    document.getElementById('announcementId').value = '';
    document.getElementById('announcementForm').reset();
    document.getElementById('announcementDate').value = new Date().toISOString().slice(0, 10);
    document.getElementById('announcementAuthor').value = currentUser.name;
    openModal('announcementModal');
}

async function handleAnnouncementSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('announcementId').value;
    const title = document.getElementById('announcementTitle').value;
    const content = document.getElementById('announcementContent').value;
    const date = document.getElementById('announcementDate').value;
    const tag = document.getElementById('announcementTag').value;

    const announcementData = {
        title,
        content,
        published_date: date,
        author_id: currentUser.user_id,
        tag
    };

    try {
        if (id) {
            await sendData(`announcements/${id}`, 'PUT', announcementData);
            showNotification('อัปเดตประกาศสำเร็จ', 'success');
        } else {
            await sendData('announcements', 'POST', announcementData);
            showNotification('บันทึกประกาศสำเร็จ', 'success');
        }
        closeModal('announcementModal');
        fetchAnnouncements();
    } catch (error) {
        // Error handled by sendData
    }
}

async function editAnnouncement(announcementId) {
    const ann = announcementsCache.find(a => a.announcement_id == announcementId);
    if (!ann) return;

    document.getElementById('announcementModalTitle').innerText = 'แก้ไขประกาศ';
    document.getElementById('announcementId').value = ann.announcement_id;
    document.getElementById('announcementTitle').value = ann.title;
    document.getElementById('announcementContent').value = ann.content;
    document.getElementById('announcementDate').value = new Date(ann.published_date).toISOString().slice(0, 10);
    document.getElementById('announcementAuthor').value = ann.author_name || currentUser.name;
    document.getElementById('announcementTag').value = ann.tag || '';
    openModal('announcementModal');
}

async function deleteAnnouncement(announcementId) {
    const confirmation = window.prompt('คุณแน่ใจหรือไม่ที่จะลบประกาศนี้? (พิมพ์ "yes" เพื่อยืนยัน)');
    if (confirmation && confirmation.toLowerCase() === 'yes') {
        try {
            await sendData(`announcements/${announcementId}`, 'DELETE');
            showNotification('ลบประกาศสำเร็จ', 'success');
            fetchAnnouncements();
        } catch (error) {
            // Error handled by sendData
        }
    } else {
        showNotification('การลบถูกยกเลิก', 'info');
    }
}

async function fetchPayments() {
    try {
        const allBills = await fetchData('bills');
        paymentsCache = await fetchData(`payments?user_id=${currentUser.user_id}`);

        // Map bills with payment status
        const billsWithStatus = allBills.map(bill => {
            if (bill.recipient_id === 'all' || bill.recipient_id == currentUser.user_id) {
                const userPaymentForBill = paymentsCache.find(p => p.bill_id === bill.bill_id);
                let status = 'unpaid';
                let payment_id = null;
                if (userPaymentForBill) {
                    status = userPaymentForBill.status === 'paid' ? 'paid' : 'pending_verification';
                    payment_id = userPaymentForBill.payment_id;
                }
                return { ...bill, status: status, payment_id: payment_id };
            }
            return null;
        }).filter(Boolean);

        renderPaymentTable(billsWithStatus.filter(b => b.status === 'unpaid' || b.status === 'pending_verification'));
        renderPaymentHistoryTable(billsWithStatus.filter(b => b.status === 'paid'));

        const unpaidCount = billsWithStatus.filter(b => b.status === 'unpaid' || b.status === 'pending_verification').length;
        const unpaidEl = document.getElementById('unpaidBills');
        if (unpaidEl) unpaidEl.textContent = unpaidCount;
    } catch (error) {
        console.error('Error fetching payments:', error);
    }
}

function renderPaymentTable(unpaidBills) {
    renderTable(unpaidBills, 'paymentTable',
        [
            { key: 'item_name', header: 'รายการ' },
            { key: 'amount', header: 'ยอดเงิน', format: (amount) => `${parseFloat(amount).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} บาท` },
            { key: 'due_date', header: 'กำหนดชำระ', format: (date) => new Date(date).toLocaleDateString('th-TH') },
            { key: 'status', header: 'สถานะ', format: (status) => getStatusHtml(status) }
        ],
        (bill) => {
            if (bill.status === 'unpaid') {
                return `<button class="btn btn-primary btn-sm" onclick="payBill('${bill.bill_id}', ${bill.amount})">ชำระเงิน</button>`;
            } else if (bill.status === 'pending_verification') {
                return `<button class="btn btn-secondary btn-sm" disabled>รอตรวจสอบ</button>`;
            }
            return '';
        },
        'ไม่มีบิลค้างชำระ'
    );
}

function renderPaymentHistoryTable(paidBills) {
    renderTable(paidBills, 'paymentHistoryTable',
        [
            { key: 'payment_date', header: 'วันที่ชำระ', format: (val, bill) => {
                const payment = paymentsCache.find(p => p.bill_id === bill.bill_id && p.status === 'paid');
                return payment ? new Date(payment.payment_date).toLocaleDateString('th-TH') : 'N/A';
            }},
            { key: 'item_name', header: 'รายการ' },
            { key: 'amount', header: 'ยอดเงิน', format: (amount) => `${parseFloat(amount).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} บาท` },
            { key: 'payment_method', header: 'วิธีชำระ', format: (val, bill) => {
                const payment = paymentsCache.find(p => p.bill_id === bill.bill_id && p.status === 'paid');
                return payment ? payment.payment_method : 'N/A';
            }}
        ],
        (bill) => `<button class="btn btn-secondary btn-sm" onclick="viewReceipt('${bill.payment_id}')">ดูใบเสร็จ</button>`,
        'ไม่มีประวัติการชำระเงิน'
    );
}

function viewReceipt(paymentId) {
    showNotification(`กำลังจะดูใบเสร็จสำหรับ Payment ID: ${paymentId}`, 'info');
}

function payBill(billId, amount) {
    document.getElementById('paymentBillId').value = billId;
    document.getElementById('paymentAmount').value = `${amount.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} บาท`;
    document.getElementById('paymentMethod').value = '';
    document.getElementById('qrCodeContainer').style.display = 'none';
    document.getElementById('bankDetails').classList.add('hidden');
    const preview = document.getElementById('paymentSlipPreview');
    if (preview) preview.innerHTML = '';
    openModal('paymentModal');
}

function showQRCode() {
    const paymentMethod = document.getElementById('paymentMethod');
    const qrCodeContainer = document.getElementById('qrCodeContainer');
    const bankDetails = document.getElementById('bankDetails');
    
    if (!paymentMethod || !qrCodeContainer || !bankDetails) return;
    
    if (paymentMethod.value === "promptpay") {
        qrCodeContainer.style.display = "block";
        bankDetails.classList.add("hidden");
    } else if (paymentMethod.value === "bank_transfer") {
        qrCodeContainer.style.display = "none";
        bankDetails.classList.remove("hidden");
    } else {
        qrCodeContainer.style.display = "none";
        bankDetails.classList.add("hidden");
    }
}

async function fetchRepairRequests() {
    repairRequestsCache = await fetchData('repair-requests');
    renderRepairRequestsTable();
    loadDashboardStats();
}

function renderRepairRequestsTable() {
    const userRepairColumns = [
        { key: 'request_id', header: 'รหัส', format: (id) => `#${id}` },
        { key: 'title', header: 'หัวข้อ' },
        { key: 'category', header: 'หมวดหมู่' },
        { key: 'submitted_date', header: 'วันที่แจ้ง', format: (date) => new Date(date).toLocaleDateString('th-TH') },
        { key: 'status', header: 'สถานะ', format: (status) => getStatusHtml(status) }
    ];
    
    const userRequests = repairRequestsCache.filter(r => r.user_id === currentUser.user_id);
    renderTable(userRequests, 'repairStatusTable', userRepairColumns, (repair) => `
        <button class="btn btn-secondary btn-sm" onclick="viewRepairDetails(${repair.request_id})">ดูรายละเอียด</button>
    `, 'ไม่มีคำขอแจ้งซ่อม');

    if (currentUser.role === 'admin') {
        const adminRepairColumns = [
            { key: 'request_id', header: 'รหัส', format: (id) => `#${id}` },
            { key: 'user_name', header: 'ผู้แจ้ง', format: (name) => name || 'N/A' },
            { key: 'title', header: 'หัวข้อ' },
            { key: 'category', header: 'หมวดหมู่' },
            { key: 'submitted_date', header: 'วันที่แจ้ง', format: (date) => new Date(date).toLocaleDateString('th-TH') },
            { key: 'status', header: 'สถานะ', format: (status) => getStatusHtml(status) }
        ];
        
        renderTable(repairRequestsCache, 'manageRepairsTable', adminRepairColumns, (repair) => {
            let buttons = '';
            if (repair.status === 'pending') {
                buttons += `<button class="btn btn-primary btn-sm" onclick="updateRepairStatus(${repair.request_id}, 'in_progress')">รับเรื่อง</button> `;
            }
            if (repair.status === 'in_progress') {
                buttons += `<button class="btn btn-primary btn-sm" onclick="updateRepairStatus(${repair.request_id}, 'completed')">เสร็จสิ้น</button> `;
            }
            buttons += `<button class="btn btn-secondary btn-sm" onclick="viewRepairDetails(${repair.request_id})">ดูรายละเอียด</button>`;
            if (repair.status !== 'completed' && repair.status !== 'rejected') {
                buttons += ` <button class="btn btn-secondary btn-sm" onclick="updateRepairStatus(${repair.request_id}, 'rejected')">ปฏิเสธ</button>`;
            }
            return buttons;
        }, 'ไม่มีคำขอแจ้งซ่อม');
    }
}

async function viewRepairDetails(requestId) {
    const repair = repairRequestsCache.find(r => r.request_id == requestId);
    if (!repair) {
        showNotification('ไม่พบรายละเอียดงานซ่อมนี้', 'error');
        return;
    }

    document.getElementById('modalRepairId').textContent = repair.request_id;
    document.getElementById('modalRepairReporter').textContent = repair.user_name || 'N/A';
    document.getElementById('modalRepairTitle').textContent = repair.title;
    document.getElementById('modalRepairCategory').textContent = repair.category;
    document.getElementById('modalRepairDate').textContent = new Date(repair.submitted_date).toLocaleDateString('th-TH');
    document.getElementById('modalRepairDescription').textContent = repair.description;

    const modalRepairStatus = document.getElementById('modalRepairStatus');
    const statusInfo = STATUS_MAP[repair.status] || { text: repair.status, class: 'status-info' };
    modalRepairStatus.textContent = statusInfo.text;
    modalRepairStatus.className = `status-badge ${statusInfo.class}`;

    const imageContainer = document.getElementById('modalRepairImageContainer');
    if (repair.image_paths && repair.image_paths !== '[]') {
        try {
            const paths = JSON.parse(repair.image_paths);
            if (paths.length > 0) {
                imageContainer.innerHTML = paths.map(path => 
                    `<img src="http://localhost:5000/uploads/${path}" alt="${repair.title}" style="max-width: 150px; max-height: 150px; border-radius: 8px; object-fit: cover; margin-right: 10px;">`
                ).join('');
            } else {
                imageContainer.innerHTML = '<p style="color: #666;">ไม่มีรูปภาพประกอบ</p>';
            }
        } catch (e) {
            imageContainer.innerHTML = '<p style="color: #666;">ไม่มีรูปภาพประกอบ</p>';
        }
    } else {
        imageContainer.innerHTML = '<p style="color: #666;">ไม่มีรูปภาพประกอบ</p>';
    }
    
    openModal('viewRepairModal');
}

async function updateRepairStatus(requestId, newStatus) {
    try {
        await sendData(`repair-requests/${requestId}`, 'PUT', { status: newStatus });
        const statusText = STATUS_MAP[newStatus]?.text || newStatus;
        showNotification(`อัปเดตสถานะงานซ่อม #${requestId} เป็น ${statusText} สำเร็จ`, 'success');
        fetchRepairRequests();
    } catch (error) {
        // Error handled by sendData
    }
}

async function fetchBookingRequests() {
    bookingRequestsCache = await fetchData('booking-requests');
    renderBookingRequestsTable();
}

function renderBookingRequestsTable() {
    const bookingColumns = [
        { key: 'location', header: 'สถานที่' },
        { key: 'date', header: 'วันที่', format: (date) => new Date(date).toLocaleDateString('th-TH') },
        { 
            key: 'start_time', 
            header: 'เวลา', 
            format: (start, item) => `${start}-${item.end_time}`
        },
        { key: 'status', header: 'สถานะ', format: (status) => getStatusHtml(status) }
    ];
    
    const userBookings = bookingRequestsCache.filter(b => 
        b.user_id === currentUser.user_id || currentUser.role === 'admin'
    );
    
    renderTable(userBookings, 'bookingTable', bookingColumns, (booking) => {
        let buttons = '';
        if (booking.status === 'pending' && currentUser.role === 'admin') {
            buttons += `<button class="btn btn-primary btn-sm" onclick="updateBookingStatus(${booking.booking_id}, 'approved')">อนุมัติ</button> `;
            buttons += `<button class="btn btn-secondary btn-sm" onclick="updateBookingStatus(${booking.booking_id}, 'rejected')">ปฏิเสธ</button> `;
        }
        if ((booking.status === 'approved' || booking.status === 'pending') && booking.user_id === currentUser.user_id) {
            buttons += `<button class="btn btn-secondary btn-sm" onclick="deleteBooking(${booking.booking_id})">ยกเลิก</button>`;
        }
        return buttons;
    }, 'ไม่มีการจอง');
}

async function deleteBooking(bookingId) {
    const confirmation = window.prompt('คุณแน่ใจหรือไม่ที่จะยกเลิกการจองนี้? (พิมพ์ "yes" เพื่อยืนยัน)');
    if (confirmation && confirmation.toLowerCase() === 'yes') {
        try {
            await sendData(`booking-requests/${bookingId}`, 'DELETE');
            showNotification('ยกเลิกการจองสำเร็จ', 'success');
            fetchBookingRequests();
        } catch (error) {
            // Error handled by sendData
        }
    } else {
        showNotification('การยกเลิกถูกยกเลิก', 'info');
    }
}

async function updateBookingStatus(bookingId, newStatus) {
    try {
        await sendData(`booking-requests/${bookingId}`, 'PUT', { status: newStatus });
        const statusText = STATUS_MAP[newStatus]?.text || newStatus;
        showNotification(`อัปเดตสถานะการจอง #${bookingId} เป็น ${statusText} สำเร็จ`, 'success');
        fetchBookingRequests();
    } catch (error) {
        // Error handled by sendData
    }
}

async function fetchAllUsers() {
    allUsersCache = await fetchData('users');
    renderManageUsersTable();
    populateBillRecipients();
}

async function showAddUserModal() {
    document.getElementById('userModalTitle').innerText = 'เพิ่มผู้ใช้ใหม่';
    document.getElementById('userId').value = '';
    document.getElementById('userForm').reset();
    document.getElementById('userPassword').required = true;
    document.getElementById('userRoleSelect').value = 'resident';
    document.getElementById('userStatusSelect').value = 'pending';
    openModal('userModal');
}

async function editUser(userId) {
    const user = allUsersCache.find(u => u.user_id == userId);
    if (!user) {
        showNotification('ไม่พบข้อมูลผู้ใช้', 'error');
        return;
    }

    document.getElementById('userModalTitle').innerText = 'แก้ไขข้อมูลผู้ใช้';
    document.getElementById('userId').value = user.user_id;
    document.getElementById('userName').value = user.name;
    document.getElementById('userUsername').value = user.username;
    document.getElementById('userPassword').value = '';
    document.getElementById('userPassword').required = false;
    document.getElementById('userPhone').value = user.phone || '';
    document.getElementById('userEmail').value = user.email || '';
    document.getElementById('userAddress').value = user.address || '';
    document.getElementById('userRoleSelect').value = user.role;
    document.getElementById('userStatusSelect').value = user.status;

    openModal('userModal');
}

function renderManageUsersTable() {
    const userColumns = [
        { key: 'name', header: 'ชื่อ-นามสกุล' },
        { key: 'address', header: 'ที่อยู่', format: (addr) => addr || '-' },
        { key: 'phone', header: 'เบอร์ติดต่อ', format: (phone) => phone || '-' },
        { key: 'status', header: 'สถานะ', format: (status) => getStatusHtml(status) },
        { key: 'role', header: 'บทบาท', format: (role) => role === 'admin' ? 'ผู้ดูแลระบบ' : 'ผู้อยู่อาศัย' }
    ];
    
    renderTable(allUsersCache, 'manageUsersTable', userColumns, (user) => {
        let buttons = '';
        if (user.status === 'pending') {
            buttons += `<button class="btn btn-primary btn-sm" onclick="updateUserStatus('${user.user_id}', 'approved')">อนุมัติ</button> `;
            buttons += `<button class="btn btn-secondary btn-sm" onclick="updateUserStatus('${user.user_id}', 'rejected')">ปฏิเสธ</button> `;
        }
        buttons += `<button class="btn btn-secondary btn-sm" onclick="editUser('${user.user_id}')">แก้ไข</button> `;
        if (user.status === 'approved') {
            buttons += `<button class="btn btn-secondary btn-sm" onclick="updateUserStatus('${user.user_id}', 'suspended')">ระงับ</button> `;
        }
        buttons += `<button class="btn btn-secondary btn-sm" onclick="deleteUser('${user.user_id}')">ลบ</button>`;
        return buttons;
    }, 'ไม่มีข้อมูลผู้ใช้');
}

async function deleteUser(userId) {
    const confirmation = window.prompt('คุณแน่ใจหรือไม่ที่จะลบผู้ใช้นี้? (พิมพ์ "yes" เพื่อยืนยัน)');
    if (confirmation && confirmation.toLowerCase() === 'yes') {
        try {
            await sendData(`users/${userId}`, 'DELETE');
            showNotification('ลบผู้ใช้สำเร็จ', 'success');
            fetchAllUsers();
        } catch (error) {
            // Error handled by sendData
        }
    } else {
        showNotification('การลบถูกยกเลิก', 'info');
    }
}

async function updateUserStatus(userId, newStatus) {
    try {
        await sendData(`users/${userId}`, 'PUT', { status: newStatus });
        const statusText = STATUS_MAP[newStatus]?.text || newStatus;
        showNotification(`อัปเดตสถานะผู้ใช้ ID: ${userId} เป็น ${statusText} สำเร็จ`, 'success');
        fetchAllUsers();
    } catch (error) {
        // Error handled by sendData
    }
}

function loadDashboardStats() {
    const totalEl = document.getElementById('totalResidents');
    const pendingEl = document.getElementById('pendingRepairs');
    const completedEl = document.getElementById('completedRepairs');
    const unpaidEl = document.getElementById('unpaidBills');

    if (totalEl && allUsersCache) {
        totalEl.textContent = allUsersCache.filter(u => u.role === 'resident' && u.status === 'approved').length;
    }
    if (pendingEl && repairRequestsCache) {
        pendingEl.textContent = repairRequestsCache.filter(r => r.status === 'pending').length;
    }
    if (completedEl && repairRequestsCache) {
        completedEl.textContent = repairRequestsCache.filter(r => r.status === 'completed').length;
    }
    if (unpaidEl && billsCache) {
        unpaidEl.textContent = billsCache.filter(b => b.status === 'unpaid' || b.status === 'pending_verification').length;
    }

    // Update recent activities table
    const activitiesEl = document.getElementById('recentActivities');
    if (activitiesEl) {
        activitiesEl.innerHTML = `
            <tr><td>10:30</td><td>แจ้งซ่อมไฟฟ้า</td><td>คุณสมชาย ใจดี</td><td>${getStatusHtml('pending')}</td></tr>
            <tr><td>09:15</td><td>ชำระค่าส่วนกลาง</td><td>คุณมาลี สวยใส</td><td>${getStatusHtml('completed')}</td></tr>
            <tr><td>08:45</td><td>จองสนามกีฬา</td><td>คุณวิชัย กล้าหาญ</td><td>${getStatusHtml('approved')}</td></tr>
        `;
    }
}

async function loadProfileData() {
    try {
        const data = await fetchData(`users/${currentUser.user_id}`);
        currentUser = { ...currentUser, ...data };
        sessionStorage.setItem('userData', JSON.stringify(currentUser));
        
        const nameEl = document.getElementById('profileName');
        const phoneEl = document.getElementById('profilePhone');
        const emailEl = document.getElementById('profileEmail');
        const addressEl = document.getElementById('profileAddress');

        if (nameEl) nameEl.value = currentUser.name || '';
        if (phoneEl) phoneEl.value = currentUser.phone || '';
        if (emailEl) emailEl.value = currentUser.email || '';
        if (addressEl) addressEl.value = currentUser.address || '';
    } catch (error) {
        console.error('Error loading profile data:', error);
    }
}

async function fetchBills() {
    billsCache = await fetchData('bills');
    renderManageBillsTable();
    loadDashboardStats();
}

function renderManageBillsTable() {
    const billColumns = [
        { key: 'item_name', header: 'รายการ' },
        { 
            key: 'recipient_id', 
            header: 'สำหรับผู้ใช้', 
            format: (id) => {
                if (id === 'all') return 'ทุกคนในหมู่บ้าน';
                const user = allUsersCache.find(u => u.user_id == id);
                return user ? user.name : 'ผู้ใช้ไม่ระบุ';
            }
        },
        { 
            key: 'amount', 
            header: 'ยอดเงิน (บาท)', 
            format: (amount) => parseFloat(amount).toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
        },
        { key: 'due_date', header: 'กำหนดชำระ', format: (date) => new Date(date).toLocaleDateString('th-TH') },
        { key: 'status', header: 'สถานะ', format: (status) => getStatusHtml(status) }
    ];
    
    renderTable(billsCache, 'manageBillsTable', billColumns, (bill) => {
        let buttons = `<button class="btn btn-secondary btn-sm" onclick="editBill('${bill.bill_id}')">แก้ไข</button> `;
        buttons += `<button class="btn btn-secondary btn-sm" onclick="deleteBill('${bill.bill_id}')">ลบ</button>`;
        if (bill.status === 'pending_verification') {
            buttons += ` <button class="btn btn-primary btn-sm" onclick="approvePaymentForBill('${bill.bill_id}')">อนุมัติการชำระ</button>`;
        }
        return buttons;
    }, 'ไม่มีบิลค่าใช้จ่าย');
}

async function showAddBillModal() {
    document.getElementById('billModalTitle').innerText = 'เพิ่มบิลค่าใช้จ่ายใหม่';
    document.getElementById('billId').value = '';
    document.getElementById('billForm').reset();
    await populateBillRecipients();
    document.getElementById('billRecipient').value = 'all';
    openModal('manageBillModal');
}

async function populateBillRecipients() {
    const billRecipientSelect = document.getElementById('billRecipient');
    if (!billRecipientSelect) return;
    
    billRecipientSelect.innerHTML = '<option value="all">ทุกคนในหมู่บ้าน</option>';
    
    if (allUsersCache.length === 0) {
        await fetchAllUsers();
    }
    
    allUsersCache
        .filter(u => u.role === 'resident' && u.status === 'approved')
        .forEach(user => {
            billRecipientSelect.innerHTML += `<option value="${user.user_id}">${user.name} (${user.address || 'ไม่ระบุที่อยู่'})</option>`;
        });
}

async function handleBillSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('billId').value;
    const itemName = document.getElementById('billItemName').value;
    const amount = document.getElementById('billAmount').value;
    const dueDate = document.getElementById('billDueDate').value;
    const recipientId = document.getElementById('billRecipient').value;

    const billData = {
        item_name: itemName,
        amount: parseFloat(amount),
        due_date: dueDate,
        recipient_id: recipientId,
        issued_by_user_id: currentUser.user_id,
        status: 'unpaid'
    };

    try {
        if (id) {
            await sendData(`bills/${id}`, 'PUT', billData);
            showNotification('อัปเดตบิลสำเร็จ', 'success');
        } else {
            await sendData('bills', 'POST', billData);
            showNotification('บันทึกบิลสำเร็จ', 'success');
        }
        closeModal('manageBillModal');
        fetchBills();
    } catch (error) {
        // Error handled by sendData
    }
}

async function editBill(billId) {
    const bill = billsCache.find(b => b.bill_id == billId);
    if (!bill) return;

    document.getElementById('billModalTitle').innerText = 'แก้ไขบิลค่าใช้จ่าย';
    document.getElementById('billId').value = bill.bill_id;
    document.getElementById('billItemName').value = bill.item_name;
    document.getElementById('billAmount').value = bill.amount;
    document.getElementById('billDueDate').value = new Date(bill.due_date).toISOString().slice(0, 10);
    await populateBillRecipients();
    document.getElementById('billRecipient').value = bill.recipient_id;
    openModal('manageBillModal');
}

async function deleteBill(billId) {
    const confirmation = window.prompt('คุณแน่ใจหรือไม่ที่จะลบบิลนี้? (พิมพ์ "yes" เพื่อยืนยัน)');
    if (confirmation && confirmation.toLowerCase() === 'yes') {
        try {
            await sendData(`bills/${billId}`, 'DELETE');
            showNotification('ลบบิลสำเร็จ', 'success');
            fetchBills();
        } catch (error) {
            // Error handled by sendData
        }
    } else {
        showNotification('การลบถูกยกเลิก', 'info');
    }
}

async function approvePaymentForBill(billId) {
    const paymentToApprove = paymentsCache.find(p => p.bill_id == billId && p.status === 'pending');
    if (!paymentToApprove) {
        showNotification('ไม่พบการชำระเงินที่รออนุมัติสำหรับบิลนี้', 'warning');
        return;
    }

    const confirmation = window.prompt(`คุณแน่ใจหรือไม่ที่จะอนุมัติการชำระเงินสำหรับบิล "${paymentToApprove.item_name}"? (พิมพ์ "yes" เพื่อยืนยัน)`);
    if (confirmation && confirmation.toLowerCase() === 'yes') {
        try {
            await sendData(`payments/approve/${paymentToApprove.payment_id}`, 'PUT', { status: 'paid' });
            showNotification(`อนุมัติการชำระเงินสำหรับบิล "${paymentToApprove.item_name}" สำเร็จ`, 'success');
            fetchBills();
            fetchPayments();
        } catch (error) {
            // Error handled by sendData
        }
    } else {
        showNotification('การอนุมัติถูกยกเลิก', 'info');
    }
}

// --- Chart.js for Reports ---
let monthlyChartInstance = null;

function renderMonthlyChart() {
    const ctx = document.getElementById('monthlyChart');
    if (!ctx) {
        console.warn("Canvas element 'monthlyChart' not found.");
        return;
    }
    
    if (monthlyChartInstance) {
        monthlyChartInstance.destroy();
    }
    
    const data = {
        labels: ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'],
        datasets: [
            {
                label: 'รายรับ (บาท)',
                data: [120000, 130000, 110000, 140000, 150000, 135000, 145000, 160000, 155000, 170000, 165000, 180000],
                backgroundColor: 'rgba(102, 126, 234, 0.6)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1,
                fill: true,
                tension: 0.3
            },
            {
                label: 'รายจ่าย (บาท)',
                data: [80000, 90000, 85000, 95000, 100000, 90000, 98000, 105000, 100000, 110000, 108000, 115000],
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1,
                fill: true,
                tension: 0.3
            }
        ]
    };
    
    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'สรุปรายรับ-รายจ่ายรายเดือน'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'จำนวนเงิน (บาท)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'เดือน'
                    }
                }
            }
        }
    };
    
    monthlyChartInstance = new Chart(ctx, config);
}

// --- Placeholder Functions for Other Pages ---
function loadCalendarData() {
    showNotification('ฟังก์ชันปฏิทินกิจกรรมยังไม่พร้อมใช้งาน', 'info');
}

function loadChatData() {
    showNotification('ฟังก์ชันแชทยังไม่พร้อมใช้งาน', 'info');
}

function loadDocumentsData() {
    showNotification('ฟังก์ชันเอกสารยังไม่พร้อมใช้งาน', 'info');
}

function loadSecurityData() {
    showNotification('ฟังก์ชันความปลอดภัยยังไม่พร้อมใช้งาน', 'info');
}

function loadVotingData() {
    showNotification('ฟังก์ชันโหวตยังไม่พร้อมใช้งาน', 'info');
}

async function handleVisitorSubmit(e) {
    e.preventDefault();
    showNotification('ฟังก์ชันแจ้งผู้มาเยือนยังไม่พร้อมใช้งาน', 'info');
}

async function handleIncidentSubmit(e) {
    e.preventDefault();
    showNotification('ฟังก์ชันรายงานเหตุการณ์ผิดปกติยังไม่พร้อมใช้งาน', 'info');
}

async function handleDocumentUpload(e) {
    e.preventDefault();
    showNotification('ฟังก์ชันอัปโหลดเอกสารยังไม่พร้อมใช้งาน', 'info');
}

function sendMessage() {
    showNotification('ฟังก์ชันส่งข้อความยังไม่พร้อมใช้งาน', 'info');
}

function openGroupChat(groupName) {
    showNotification(`กำลังเปิดแชทกลุ่ม: ${groupName}`, 'info');
}

function submitVote(pollName) {
    showNotification(`กำลังส่งโหวตสำหรับ: ${pollName}`, 'info');
}

function toggleNotifications() {
    showNotification('ฟังก์ชันการแจ้งเตือนยังไม่พร้อมใช้งาน', 'info');
}

function previousMonth() {
    currentMonth = currentMonth === 0 ? 11 : currentMonth - 1;
    if (currentMonth === 11) currentYear--;
    updateCalendarDisplay();
}

function nextMonth() {
    currentMonth = currentMonth === 11 ? 0 : currentMonth + 1;
    if (currentMonth === 0) currentYear++;
    updateCalendarDisplay();
}

function updateCalendarDisplay() {
    const monthEl = document.getElementById('currentMonth');
    if (monthEl) {
        monthEl.textContent = `${monthNames[currentMonth]} ${currentYear + 543}`;
    }
}

// --- Event Listeners Setup ---
function setupEventListeners() {
    // Login and register forms
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginForm) {
        loginForm.removeEventListener('submit', handleLogin);
        loginForm.addEventListener('submit', handleLogin);
    }

    if (registerForm) {
        registerForm.removeEventListener('submit', handleRegister);
        registerForm.addEventListener('submit', handleRegister);
    }

    // Close modals when clicking outside
    window.onclick = (event) => {
        document.querySelectorAll('.modal').forEach(modal => {
            if (event.target === modal && modal.style.display !== 'none') {
                closeModal(modal.id);
            }
        });
    };

    // Mobile sidebar toggle
    const headerH1 = document.querySelector('.header-content h1');
    if (headerH1) {
        headerH1.removeEventListener('click', toggleSidebar);
        if (window.innerWidth <= 768) {
            headerH1.style.cursor = 'pointer';
            headerH1.addEventListener('click', toggleSidebar);
        }

        window.addEventListener('resize', () => {
            const sidebar = document.getElementById('sidebar');
            if (sidebar) {
                sidebar.classList.toggle('open', window.innerWidth <= 768 && sidebar.classList.contains('open'));
            }

            headerH1.style.cursor = window.innerWidth <= 768 ? 'pointer' : 'default';
            headerH1.removeEventListener('click', toggleSidebar);
            if (window.innerWidth <= 768) {
                headerH1.addEventListener('click', toggleSidebar);
            }
        });
    }

    setupDynamicFormListeners();
}

function setupDynamicFormListeners() {
    const formHandlers = [
        { id: 'repairForm', handler: handleRepairSubmit },
        { id: 'bookingForm', handler: handleBookingSubmit },
        { id: 'paymentForm', handler: handlePaymentSubmit },
        { id: 'profileForm', handler: handleProfileUpdate },
        { id: 'changePasswordForm', handler: handlePasswordChange },
        { id: 'announcementForm', handler: handleAnnouncementSubmit },
        { id: 'billForm', handler: handleBillSubmit },
        { id: 'userForm', handler: handleUserSubmit },
        { id: 'visitorForm', handler: handleVisitorSubmit },
        { id: 'incidentForm', handler: handleIncidentSubmit },
        { id: 'documentUploadForm', handler: handleDocumentUpload }
    ];

    formHandlers.forEach(({ id, handler }) => {
        const form = document.getElementById(id);
        if (form) {
            form.removeEventListener('submit', handler);
            form.addEventListener('submit', handler);
        }
    });

    // File input previews
    const fileInputPreviews = [
        { inputId: 'paymentSlipFile', previewId: 'paymentSlipPreview' },
        { inputId: 'repairImages', previewId: 'repairImagesPreview' },
        { inputId: 'profileDocuments', previewId: 'profileDocumentsPreview' },
        { inputId: 'incidentEvidence', previewId: 'incidentEvidencePreview' },
        { inputId: 'documentFile', previewId: 'documentFilePreview' }
    ];

    fileInputPreviews.forEach(({ inputId, previewId }) => {
        const input = document.getElementById(inputId);
        if (input) {
            input.removeEventListener('change', () => handleFileUpload(inputId, previewId));
            input.addEventListener('change', () => handleFileUpload(inputId, previewId));
        }
    });

    // Payment method change
    const paymentMethodEl = document.getElementById('paymentMethod');
    if (paymentMethodEl) {
        paymentMethodEl.removeEventListener('change', showQRCode);
        paymentMethodEl.addEventListener('change', showQRCode);
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

function initializeSocketIO() {
    if (socket && socket.connected) {
        socket.disconnect();
    }

    socket = io('http://localhost:5000');

    socket.on('connect', () => {
        console.log('Connected to WebSocket server');
        // Join user-specific room
        socket.emit('join_chat_room', { room_name: currentUser.user_id });
        // Join admin room if admin
        if (currentUser.role === 'admin') {
            socket.emit('join_chat_room', { room_name: 'admins' });
        }
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket server');
    });

    // Announcements
    socket.on('new_announcement', (data) => {
        announcementsCache.unshift(data);
        showNotification(`ประกาศใหม่: ${data.title}`, 'info');
        const announcementsPage = document.getElementById('announcements');
        if (announcementsPage && !announcementsPage.classList.contains('hidden')) {
            renderAnnouncements();
        }
    });

    socket.on('announcement_updated', (data) => {
        const idx = announcementsCache.findIndex(a => a.announcement_id === data.announcement_id);
        if (idx !== -1) {
            announcementsCache[idx] = data;
        }
        showNotification(`ประกาศ "${data.title}" ได้รับการแก้ไข`, 'info');
        const announcementsPage = document.getElementById('announcements');
        if (announcementsPage && !announcementsPage.classList.contains('hidden')) {
            renderAnnouncements();
        }
    });

    socket.on('announcement_deleted', (data) => {
        announcementsCache = announcementsCache.filter(a => a.announcement_id !== data.announcement_id);
        showNotification('ประกาศถูกลบแล้ว', 'info');
        const announcementsPage = document.getElementById('announcements');
        if (announcementsPage && !announcementsPage.classList.contains('hidden')) {
            renderAnnouncements();
        }
    });

    // Repair Requests
    socket.on('new_repair_request', (data) => {
        if (currentUser.role === 'admin') {
            showNotification(`มีคำขอแจ้งซ่อมใหม่: ${data.title} โดย ${data.user_name || 'ผู้ใช้งาน'}`, 'warning');
            fetchRepairRequests();
        } else if (currentUser.user_id === data.user_id) {
            showNotification(`คำขอแจ้งซ่อมของคุณ "${data.title}" ถูกสร้างแล้ว`, 'success');
            fetchRepairRequests();
        }
    });

    socket.on('repair_status_updated', (data) => {
        if (currentUser.user_id === data.user_id) {
            const statusText = STATUS_MAP[data.status]?.text || data.status;
            showNotification(`สถานะงานซ่อม "${data.title}" เปลี่ยนเป็น "${statusText}"`, 'success');
            fetchRepairRequests();
        } else if (currentUser.role === 'admin') {
            const statusText = STATUS_MAP[data.status]?.text || data.status;
            showNotification(`สถานะงานซ่อม #${data.request_id} โดย ${data.user_name} เปลี่ยนเป็น "${statusText}"`, 'info');
            fetchRepairRequests();
        }
    });

    // Booking Requests
    socket.on('new_booking_request', (data) => {
        if (currentUser.role === 'admin') {
            showNotification(`มีการจองพื้นที่ใหม่: ${data.location} โดย ${data.user_name || 'ผู้ใช้งาน'}`, 'warning');
            fetchBookingRequests();
        } else if (currentUser.user_id === data.user_id) {
            showNotification(`คำขอจองพื้นที่ของคุณ "${data.location}" ถูกสร้างแล้ว`, 'success');
            fetchBookingRequests();
        }
    });

    // Payments & Bills
    socket.on('new_payment_receipt', (data) => {
        if (currentUser.role === 'admin') {
            showNotification(`มีหลักฐานการชำระเงินใหม่: ${data.amount} บาท โดย ${data.user_name || 'ผู้ใช้งาน'}`, 'warning');
            fetchPayments();
            fetchBills();
        } else if (currentUser.user_id === data.user_id) {
            showNotification(`หลักฐานการชำระเงินของคุณสำหรับบิล #${data.bill_id} ถูกส่งแล้ว`, 'success');
            fetchPayments();
        }
    });

    socket.on('payment_approved', (data) => {
        if (currentUser.user_id === data.user_id) {
            showNotification(`การชำระเงินสำหรับบิล #${data.bill_id} ของคุณได้รับการอนุมัติแล้ว`, 'success');
            fetchPayments();
        } else if (currentUser.role === 'admin') {
            showNotification(`การชำระเงินสำหรับบิล #${data.bill_id} โดย ${data.user_name} ได้รับการอนุมัติ`, 'info');
            fetchPayments();
            fetchBills();
        }
    });

    socket.on('new_bill_created', (data) => {
        showNotification(`มีบิลใหม่: ${data.item_name} จำนวน ${data.amount} บาท`, 'info');
        if (currentUser.role === 'admin') {
            fetchBills();
        } else if (data.recipient_id === 'all' || data.recipient_id == currentUser.user_id) {
            fetchPayments();
        }
    });

    socket.on('bill_updated', (data) => {
        showNotification(`บิล "${data.item_name}" ได้รับการแก้ไข`, 'info');
        if (currentUser.role === 'admin') {
            fetchBills();
        } else if (data.recipient_id === 'all' || data.recipient_id == currentUser.user_id) {
            fetchPayments();
        }
    });

    socket.on('bill_deleted', (data) => {
        showNotification(`บิล "${data.item_name}" ถูกลบแล้ว`, 'info');
        if (currentUser.role === 'admin') {
            fetchBills();
        } else if (data.recipient_id === 'all' || data.recipient_id == currentUser.user_id) {
            fetchPayments();
        }
    });
}

// --- Initialize Application ---
document.addEventListener('DOMContentLoaded', () => {
    const storedUserData = sessionStorage.getItem('userData');
    if (storedUserData) {
        try {
            currentUser = JSON.parse(storedUserData);
            showDashboard();
            initializeSocketIO();
        } catch (e) {
            console.error('Error parsing stored user data:', e);
            sessionStorage.removeItem('userData');
            sessionStorage.removeItem('isLoggedIn');
            showLogin();
        }
    } else {
        showLogin();
    }
    
    setupEventListeners();
});

// Global functions that need to be accessible from HTML onclick attributes
window.showPage = showPage;
window.showLogin = showLogin;
window.showRegister = showRegister;
window.logout = logout;
window.showForgotPassword = showForgotPassword;
window.togglePasswordVisibility = togglePasswordVisibility;
window.openModal = openModal;
window.closeModal = closeModal;
window.toggleSidebar = toggleSidebar;
window.showAddAnnouncementModal = showAddAnnouncementModal;
window.editAnnouncement = editAnnouncement;
window.deleteAnnouncement = deleteAnnouncement;
window.payBill = payBill;
window.viewReceipt = viewReceipt;
window.viewRepairDetails = viewRepairDetails;
window.updateRepairStatus = updateRepairStatus;
window.deleteBooking = deleteBooking;
window.updateBookingStatus = updateBookingStatus;
window.showAddUserModal = showAddUserModal;
window.editUser = editUser;
window.deleteUser = deleteUser;
window.updateUserStatus = updateUserStatus;
window.showAddBillModal = showAddBillModal;
window.editBill = editBill;
window.deleteBill = deleteBill;
window.approvePaymentForBill = approvePaymentForBill;
window.sendMessage = sendMessage;
window.openGroupChat = openGroupChat;
window.submitVote = submitVote;
window.toggleNotifications = toggleNotifications;
window.previousMonth = previousMonth;
window.nextMonth = nextMonth;
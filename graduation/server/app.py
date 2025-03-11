from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from auth import token_required
import hashlib
import pyotp
import qrcode
from models import Log
import dkim
import dns.resolver
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from flask import request, jsonify
from io import BytesIO
import re
import jwt
import base64
import binascii
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)
SECRET_KEY = app.config["SECRET_KEY"]
CORS(app, supports_credentials=True)  # ✅ حل المشكلة

from models import db, User, Email, Log, Notification, LoginLog  # استيراد `db` بعد تعريف `app`

db.init_app(app)  # ربط `db` بالتطبيق
migrate = Migrate(app, db)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pragmas': {'journal_mode': 'WAL'}
}

SECRET_KEY = "supersecretkey"

# دالة لتوليد الهاش
def generate_hash(content):
    """توليد هاش فريد للمحتوى"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

# دالة لتوليد secret_key
def generate_secret_key():
    return pyotp.random_base32()  # توليد مفتاح سر عشوائي للمستخدم

# توليد الـ secret_key للمستخدمين عند التسجيل
with app.app_context():
    users = User.query.all()
    for user in users:
        if not user.secret_key:
            user.secret_key = generate_secret_key()
            db.session.commit()

# التحقق من دومين البريد الإلكتروني
def check_domain(sender_email):
    domain = sender_email.split('@')[1]
    if domain != 'example.com':
        return False
    return True

# تحميل المفتاح العام
def load_public_key():
    with open("public.pem", "rb") as f:
        return RSA.import_key(f.read())

# دالة لتشفير المحتوى
def encrypt_message(message, pub_key):
    cipher = PKCS1_OAEP.new(pub_key)
    encrypted_message = cipher.encrypt(message.encode())
    return base64.b64encode(encrypted_message).decode()  # تحويل إلى Base64 لتخزينه

# دالة لفك تشفير المحتوى
def load_private_key():
    with open("private.pem", "rb") as f:
        return RSA.import_key(f.read())

# فك التشفير
def decrypt_message(encrypted_message, priv_key):
    try:
        decoded_message = base64.b64decode(encrypted_message)
        cipher = PKCS1_OAEP.new(priv_key)
        decrypted_message = cipher.decrypt(decoded_message)
        return decrypted_message.decode()
    except (binascii.Error, ValueError):
        return "Error in decryption"

# دالة لتوقيع الرسالة
def sign_message(message, private_key):
    h = SHA256.new(message.encode())  # تجزئة الرسالة
    signature = pkcs1_15.new(private_key).sign(h)
    return base64.b64encode(signature).decode()

# التحقق من التوقيع
def verify_signature(message, signature, public_key):
    h = SHA256.new(message.encode())
    signature = base64.b64decode(signature)
    try:
        pkcs1_15.new(public_key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False

# التحقق من قوة الباسوورد
def is_strong_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return "Password must contain at least one special character (!@#$%^&* etc.)"
    return None

# إشعار للمسؤول في حالة النشاط المشبوه
def notify_admin(user_email, ip_list):
    admin = User.query.filter_by(role="admin").first()
    if admin:
        notification = Notification(
            user_id=admin.id,
            message=f"Suspicious activity detected for user {user_email} from IP addresses: {', '.join(ip_list)}"
        )
        db.session.add(notification)
        db.session.commit()

from flask_cors import cross_origin

@app.route('/user_info', methods=['GET'])
@cross_origin()
@token_required
def get_user_info(current_user):
    return jsonify({
        "first_name": current_user.first_name,  # تأكدي أن هذا الحقل موجود في الموديل
        "last_name": current_user.last_name,  # تأكدي أن هذا الحقل موجود في الموديل
        "email": current_user.email,
        "role": current_user.role
    }), 200


# تسجيل مستخدم جديد
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    # ✅ التحقق من أن جميع البيانات المطلوبة متوفرة
    if not data or not data.get('email') or not data.get('password') or not data.get('first_name') or not data.get('last_name'):
        return jsonify({"error": "Missing first name, last name, email, or password"}), 400

    # ✅ التأكد من أن المستخدم غير موجود مسبقًا
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    # ✅ التحقق من قوة كلمة المرور
    password_strength_error = is_strong_password(data['password'])
    if password_strength_error:
        return jsonify({"error": password_strength_error}), 400

    # ✅ إنشاء المستخدم الجديد مع الاسم الأول والأخير
    new_user = User(
        first_name=data['first_name'],  # ✅ حفظ الاسم الأول
        last_name=data['last_name'],    # ✅ حفظ الاسم الأخير
        email=data['email']
    )
    new_user.set_password(data['password'])  # ✅ تعيين كلمة المرور بعد تشفيرها
    new_user.secret_key = generate_secret_key()  # ✅ إنشاء مفتاح 2FA للمستخدم الجديد

    db.session.add(new_user)
    db.session.commit()

    # ✅ إنشاء QR Code لتمكين 2FA
    totp = pyotp.TOTP(new_user.secret_key)
    uri = totp.provisioning_uri(name=new_user.email, issuer_name="email_integrity")
    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return jsonify({
        "message": "User registered successfully!",
        "user_id": new_user.id,
        "qr_code": f"data:image/png;base64,{qr_base64}"
    }), 201

# تسجيل دخول
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if user:
        # إذا كان الحساب مقفلًا بسبب محاولات فاشلة كثيرة
        if user.failed_attempts >= 5 and datetime.now() < user.lock_time:
            return jsonify({"error": "Account is temporarily locked. Please try again later."}), 403

        # تسجيل بيانات تسجيل الدخول
        login_log = LoginLog(user_id=user.id, user_agent=request.user_agent.string, ip_address=request.remote_addr)
        db.session.add(login_log)
        db.session.commit()

        if user.check_password(data['password']):
            user.failed_attempts = 0
            db.session.commit()

            # ✅ التحقق مما إذا كان المستخدم مفعلًا لـ 2FA
            if user.secret_key:
                return jsonify({
                    "message": "Enter your 2FA code",
                    "requires_2fa": True  # ✅ أضفنا هذه
                }), 200

            # ✅ إذا لم يكن عنده 2FA، أرسل توكن تسجيل دخول مباشرةً
            expiration_time = datetime.now() + timedelta(hours=24)
            token = jwt.encode({'user_id': user.id, 'exp': expiration_time}, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({
                "message": "Login successful!",
                "token": token,
                "requires_2fa": False  # ✅ أضفنا هذه
            }), 200

        # تحديث المحاولات الفاشلة وإقفال الحساب إذا تجاوز الحد
        user.failed_attempts += 1
        if user.failed_attempts >= 5:
            user.lock_time = datetime.now() + timedelta(minutes=10)
            notification = Notification(user_id=user.id, message="Too many failed login attempts. Your account is now locked for 10 minutes.")
            db.session.add(notification)
            db.session.commit()
        db.session.commit()

    return jsonify({"error": "Invalid credentials"}), 401

# التحقق من رمز 2FA
@app.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    email = request.json.get('email')
    token = request.json.get('token')

    user = User.query.filter_by(email=email).first()
    if user:
        if not user.secret_key:
            return jsonify({"error": "2FA not set up for this user."}), 400

        totp = pyotp.TOTP(user.secret_key)
        if totp.verify(token):
            expiration_time = datetime.now() + timedelta(hours=24)
            token = jwt.encode({'user_id': user.id, 'exp': expiration_time}, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({"message": "Login successful!", "token": token})

        return jsonify({"error": "Invalid 2FA token."}), 400
    return jsonify({"error": "User not found."}), 404

# إرسال البريد الإلكتروني
@app.route('/send_email', methods=['POST'])
@token_required
def send_email(current_user):
    data = request.json

    if not data.get('receiver_email') or not data.get('content') or not data.get('subject'):
        return jsonify({"error": "Receiver email, subject, and content are required!"}), 400

    email_content = data['content']
    email_subject = data['subject']  # ✅ استخراج العنوان
    receiver_email = data['receiver_email']

    if not check_domain(current_user.email):
        return jsonify({"error": "You are not allowed to send emails from an untrusted domain!"}), 403

    receiver = User.query.filter_by(email=receiver_email).first()
    if not receiver:
        return jsonify({"error": "Receiver not found"}), 404

    email_hash = generate_hash(email_content)
    public_key = load_public_key()
    encrypted_message = encrypt_message(email_content, public_key)

    private_key = load_private_key()
    signed_message = sign_message(encrypted_message, private_key)

    new_email = Email(
        sender_id=current_user.id, 
        receiver_id=receiver.id, 
        hash=email_hash, 
        hash_status="Valid", 
        content=encrypted_message, 
        signature=signed_message,
        subject=email_subject  # ✅ حفظ العنوان في قاعدة البيانات
    )
    db.session.add(new_email)
    db.session.commit()
 # ✅ إضافة إشعار للمستخدم المستقبل
    notification = Notification(
        user_id=receiver.id,
        message=f"You have a new email from {current_user.email} with subject: {email_subject}"
    )
    db.session.add(notification)
    db.session.commit()

    log = Log(email_id=new_email.id, status="Sent")
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "message": "Email sent successfully!", 
        "notification": "Your email has been successfully sent to " + receiver_email
    }), 200


# استلام البريد الإلكتروني
@app.route('/receive_email/<int:email_id>', methods=['GET'])
@token_required
def receive_email(current_user, email_id):
    email = Email.query.get_or_404(email_id)

    if email.receiver_id != current_user.id:
        return jsonify({"error": "Unauthorized access"}), 403

    if not check_domain(email.sender.email):
        return jsonify({"error": "Email is not from a trusted domain"}), 400

    public_key = load_public_key()

    if not verify_signature(email.content, email.signature, public_key):
        return jsonify({"error": "Email has been tampered with by signature"}), 400

    private_key = load_private_key()
    decrypted_message = decrypt_message(email.content, private_key)

    received_hash = generate_hash(decrypted_message)
    if received_hash != email.hash:
        email.hash_status = "Invalid"
        db.session.add(email)
        db.session.commit()

        log = Log(email_id=email.id, status="Tampered")
        db.session.add(log)
        db.session.commit()

        return jsonify({"error": "Email has been tampered with by content"}), 400

    log = Log(email_id=email.id, status="Received")
    db.session.add(log)
    db.session.commit()

    return jsonify({
        "sender": email.sender.email,
        "subject": email.subject,  # ✅ إرجاع العنوان مع باقي البيانات
        "content": decrypted_message,
        "Hash Status": email.hash_status
    }), 200


# طلب إعادة تعيين كلمة المرور
@app.route('/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    totp = pyotp.TOTP(user.secret_key)
    verification_message = "Enter the 2FA code from your authenticator app to reset your password."

    return jsonify({"message": verification_message, "email": email}), 200

# التحقق من رمز 2FA لإعادة تعيين كلمة المرور
@app.route('/verify_2fa_for_reset', methods=['POST'])
def verify_2fa_for_reset():
    data = request.json
    email = data.get('email')
    token = data.get('token')

    if not email or not token:
        return jsonify({"error": "Email and 2FA token are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    totp = pyotp.TOTP(user.secret_key)
    if not totp.verify(token):
        return jsonify({"error": "Invalid 2FA token"}), 400

    expiration_time = datetime.now() + timedelta(minutes=15)
    reset_token = jwt.encode({'user_id': user.id, 'exp': expiration_time}, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({"message": "2FA verified. Use this token to reset your password.", "reset_token": reset_token}), 200

# إعادة تعيين كلمة المرور
@app.route('/reset-password', methods=['POST'])
def reset_password():
    reset_token = request.headers.get("Authorization")

    if not reset_token:
        return jsonify({"error": "Missing token"}), 401

    try:
        payload = jwt.decode(reset_token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid token data"}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    if not data or "new_password" not in data or "confirm_password" not in data:
        return jsonify({"error": "Missing required fields"}), 400

    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    password_strength_error = is_strong_password(new_password)
    if password_strength_error:
        return jsonify({"error": password_strength_error}), 400

    user.set_password(new_password)
    db.session.commit()

    notification = Notification(user_id=user.id, message="Your password has been changed successfully.")
    db.session.add(notification)
    db.session.commit()

    return jsonify({"message": "Password reset successful!"}), 200


@app.route('/change-password', methods=['POST'])
def change_password():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "Missing token"}), 401

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            return jsonify({"error": "Invalid token data"}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    # ✅ التحقق من أن المستخدم أدخل كلمة المرور القديمة بشكل صحيح
    if not user.check_password(old_password):  
        return jsonify({"error": "Old password is incorrect"}), 400

    if not new_password or not confirm_password:
        return jsonify({"error": "Missing required fields"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    password_strength_error = is_strong_password(new_password)
    if password_strength_error:
        return jsonify({"error": password_strength_error}), 400

    # ✅ تحديث كلمة المرور
    user.set_password(new_password)
    db.session.commit()

    # ✅ إضافة إشعار بأن كلمة المرور تم تغييرها
    notification = Notification(user_id=user.id, message="Your password has been changed successfully.")
    db.session.add(notification)
    db.session.commit()

    return jsonify({"message": "Password changed successfully!"}), 200

@app.route('/inbox', methods=['GET'])
@token_required
def inbox(current_user):
    emails = Email.query.filter_by(receiver_id=current_user.id).all()  # ✅ فقط الإيميلات المستلمة لهذا اليوزر

    inbox_list = []
    for email in emails:
        decrypted_content = decrypt_message(email.content, load_private_key())  # فك التشفير
        inbox_list.append({
            "id": email.id,
            "sender": email.sender.email,
            "subject": email.subject,  # ✅ إضافة `subject`
            "content": decrypted_content,
            "created_at": email.created_at
        })

    return jsonify({"emails": inbox_list}), 200

# في دالة view_logs
@app.route('/logs', methods=['GET'])
@token_required
def view_logs(current_user):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403

    # جلب جميع السجلات
    emails = Email.query.all()

    # تحميل المفتاح الخاص لفك التشفير
    private_key = load_private_key()  # دالة لتحميل المفتاح الخاص
    
    email_list = []
    for email in emails:
        # فك تشفير المحتوى فقط إذا كان المسؤول يطلبه
       decrypted_content = decrypt_message(email.content, private_key)  # فك التشفير
        
        # إضافة السجل المفكوك
       email_list.append({
            "id": email.id,
            "sender": email.sender.email,
            "receiver": email.receiver.email,
            "content": decrypted_content,  # عرض المحتوى المفكوك
            "hash": email.hash,
            "created_at": email.created_at,
            "Hash Status": email.hash_status
        })
    
    return jsonify({"emails": email_list}), 200

@app.route('/sent_emails', methods=['GET'])
@token_required
def get_sent_emails(current_user):
    sent_emails = Email.query.filter_by(sender_id=current_user.id).order_by(Email.created_at.desc()).all()

    emails_data = []
    private_key = load_private_key()  # ✅ تحميل المفتاح الخاص لفك التشفير

    for email in sent_emails:
        try:
            decrypted_content = decrypt_message(email.content, private_key)  # ✅ فك التشفير
        except Exception as e:
            decrypted_content = "Error decrypting email"  # إذا كان هناك مشكلة في فك التشفير

        emails_data.append({
            "id": email.id,
            "receiver": email.receiver.email,
            "subject": email.subject if email.subject else "No Subject",
            "content": decrypted_content,  # ✅ إرجاع المحتوى المفكوك التشفير
            "created_at": email.created_at
        })

    return jsonify({"sent_emails": emails_data}), 200

@app.route('/update_name', methods=['PUT'])
@token_required
def update_name(current_user):
    data = request.json

    if not data.get('first_name') or not data.get('last_name'):
        return jsonify({"error": "First name and last name are required"}), 400

    # تحديث الاسم في قاعدة البيانات
    current_user.first_name = data['first_name']
    current_user.last_name = data['last_name']
    db.session.commit()

    return jsonify({"message": "Name updated successfully!"}), 200


@app.route('/suspicious_activity', methods=['GET'])
@token_required
def suspicious_activity(current_user):
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403
    # جلب آخر 5 محاولات دخول للمستخدم
    logs = LoginLog.query.filter_by(user_id=current_user.id).order_by(LoginLog.login_time.desc()).limit(5).all()
    
    # جمع عناوين الـ IP لجميع المحاولات
    ip_addresses = [log.ip_address for log in logs]
    
    # التحقق من أن المستخدم قد سجل الدخول من أكثر من 3 عناوين IP مختلفة في آخر 5 محاولات
    if len(set(ip_addresses)) > 2:  # إذا كانت هناك عدة عناوين IP مختلفة
        # إرسال إشعار للمسؤول عند اكتشاف نشاط مشبوه
        notify_admin(current_user.email, ip_addresses)
        return jsonify({"alert": "Suspicious activity detected! Multiple IP addresses."}), 403

    return jsonify({"message": "No suspicious activity detected."}), 200


@app.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
        # جلب الإشعارات الخاصة فقط بالمستخدم الحالي
        notifications = Notification.query.filter_by(user_id=current_user.id).all()

        notifications_list = [{
            "id": notification.id,
            "message": notification.message,
            "created_at": notification.created_at,
            "user_name": notification.user.email
        } for notification in notifications]

        return jsonify({"notifications": notifications_list}), 200

    

@app.route('/all_notifications', methods=['GET'])
@token_required
def get_all_notifications(current_user):
    if current_user.role != "admin":  # ✅ تعديل طريقة الوصول إلى الـ role
        return jsonify({"message": "Unauthorized"}), 403
    
    notifications = Notification.query.all()  # ✅ جلب كل الإشعارات من قاعدة البيانات
    return jsonify({
        "notifications": [
            {
                "username": notif.user.email,  # ✅ جلب اسم المستخدم المرتبط بالإشعار
                "message": notif.message,
                "created_at": notif.created_at
            } for notif in notifications
        ]
    })


@app.route('/')
def home():
    return "Backend is running!"

if __name__ == '__main__':
    with app.app_context():
        print(" Database path:", app.config["SQLALCHEMY_DATABASE_URI"])
        db.create_all()
        print(" Tables created successfully!")
    app.run(debug=True)

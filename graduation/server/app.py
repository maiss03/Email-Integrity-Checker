from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from auth import token_required 
import hashlib
import pyotp
import qrcode
from models import Log

app = Flask(__name__)
app.config.from_object(Config)
SECRET_KEY = app.config["SECRET_KEY"]

from models import db, User, Email  # استيراد `db` بعد تعريف `app`

db.init_app(app)  #  ربط `db` بالتطبيق
migrate = Migrate(app, db)

def generate_hash(content):
    """توليد هاش فريد للمحتوى"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def generate_secret_key():
    return pyotp.random_base32()  # توليد مفتاح سر عشوائي للمستخدم

with app.app_context():
    users = User.query.all()  # الآن يمكننا استعلام البيانات
    for user in users:
        if not user.secret_key:
            user.secret_key = generate_secret_key()  # توليد secret_key عشوائي
            db.session.commit()  # حفظ التغييرات

def generate_qr_code(user_email, secret_key):
    totp = pyotp.TOTP(secret_key)
    uri = totp.provisioning_uri(user_email, issuer_name="MyApp")
    img = qrcode.make(uri)  # توليد صورة QR
    img.show()  # عرض صورة الـ QR مباشرة للمستخد

from flask import request, jsonify

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing email or password"}), 400

    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    # إنشاء مستخدم جديد مع تشفير كلمة المرور
    new_user = User(email=data['email'])
    new_user.set_password(data['password'])  # تشفير كلمة المرور

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!", "user_id": new_user.id}), 201


import jwt
import datetime
SECRET_KEY = "supersecretkey"
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if user and user.check_password(data['password']):  # استخدام check_password  
        # إذا كانت كلمة المرور صحيحة، نطلب منه إدخال رمز 2FA
        return jsonify({"message": "Enter your 2FA code"}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    email = request.json['email']
    token = request.json['token']  # الرمز الذي أرسله المستخدم عبر التطبيق

    user = User.query.filter_by(email=email).first()
    if user:
        totp = pyotp.TOTP(user.secret_key)
        if totp.verify(token):  # التحقق من صحة الرمز
            # توليد توكن JWT للمستخدم بعد التحقق من 2FA
            expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            token = jwt.encode({'user_id': user.id, 'exp': expiration_time}, app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({"message": "Login successful!", "token": token})
    
        else:
            return jsonify({"error": "Invalid 2FA token."}), 400
    return jsonify({"error": "User not found."}), 404

@app.route('/send_email', methods=['POST'])
@token_required  # التأكد من وجود التوكن
def send_email(current_user):
    data = request.json
    if not data.get('receiver_id') or not data.get('content'):
        return jsonify({"error": "Receiver ID and content are required!"}), 400
    content = data['content']
    email_hash = generate_hash(content)  # توليد الهاش للمحتوى
    # إنشاء الإيميل
    new_email = Email(sender_id=current_user.id, receiver_id=data['receiver_id'], content=data['content'], hash=email_hash)
    db.session.add(new_email)
    db.session.commit()

    # إضافة السجل في جدول Logs
    log = Log(email_id=new_email.id, status="Sent")
    db.session.add(log)
    db.session.commit()
    return jsonify({"message": "Email sent successfully!"}), 200

@app.route('/receive_email/<int:email_id>', methods=['GET'])
@token_required
def receive_email(current_user, email_id):
    email = Email.query.get_or_404(email_id)
    
    if email.receiver_id != current_user.id:
        return jsonify({"error": "Unauthorized access"}), 403
    
    received_hash = generate_hash(email.content)
    if received_hash != email.hash:
        return jsonify({"error": "Email has been tampered with"}), 400
    
    log = Log(email_id=email.id, status="Received")
    db.session.add(log)
    db.session.commit()

    return jsonify({"sender": email.sender.email, "content": email.content}), 200

    
@app.route('/logs', methods=['GET'])
@token_required  # التأكد من وجود التوكن
def view_logs(current_user):
    print(f"Current user: {current_user.email}")  # طباعة بيانات المستخدم
    print(f"User role: {current_user.role}")  # طباعة الـ role للمستخدم

    # التحقق من أن المستخدم هو المسؤول (Admin)
    if current_user.role != 'admin':  # تأكد من أن المستخدم هو مسؤول
        return jsonify({"error": "Unauthorized access"}), 403

    # جلب جميع السجلات (مثال: جلب جميع الإيميلات المرسلة)
    emails = Email.query.all()

    # تحويل السجلات إلى JSON لتكون قابلة للعرض في Postman
    email_list = [{"id": email.id, "sender": email.sender.email, "receiver": email.receiver.email, "content": email.content,"hash":email.hash, "created_at": email.created_at} for email in emails]
    
    return jsonify({"emails": email_list}), 200

@app.route('/')
def home():
    return "Backend is running!"

if __name__ == '__main__':
    with app.app_context():
        print(" Database path:", app.config["SQLALCHEMY_DATABASE_URI"])
        db.create_all()
        print(" Tables created successfully!")
    app.run(debug=True)

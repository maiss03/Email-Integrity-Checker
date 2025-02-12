from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    role = db.Column(db.String(50), default='user')  # إضافة حقل الدور (admin أو user)
    secret_key = db.Column(db.String(16), nullable=True)  # إضافة الحقل لتخزين سر المستخدم
    failed_attempts = db.Column(db.Integer, default=0)  # عدد المحاولات الفاشلة
    lock_time = db.Column(db.DateTime, nullable=True)  # الوقت الذي يتم حظر الحساب فيه

    # الطريقة لتشفير كلمة المرور
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # الطريقة للتحقق من كلمة المرور
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)



class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    hash = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    hash_status = db.Column(db.String(50), nullable=True) 
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())  # تاريخ ووقت السجل
    status = db.Column(db.String(50))  # حالة الإيميل (تم التلاعب أم لا)
    email = db.relationship('Email', backref=db.backref('logs', lazy=True))

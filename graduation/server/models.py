from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    

    sender_id = db.Column(db.Integer, db.ForeignKey('user_ad.id'), nullable=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user_ad.id'), nullable=True)


    sender_email = db.Column(db.String(120), nullable=False)      
    receiver_email = db.Column(db.String(120), nullable=False)    

    subject = db.Column(db.String(255), nullable=False, default="No Subject")
    content = db.Column(db.Text, nullable=False)
    hash = db.Column(db.String(100), nullable=True)  
    hash_status = db.Column(db.String(50), nullable=True)
    signature = db.Column(db.String(500))  

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    sender = db.relationship('UserAD', foreign_keys=[sender_id])
    receiver = db.relationship('UserAD', foreign_keys=[receiver_id])



def __repr__(self):
    return f'<Email {self.id} from {self.sender.email} to {self.receiver.email}>'

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())  
    status = db.Column(db.String(50))  
    email = db.relationship('Email', backref=db.backref('logs', lazy=True))

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_ad.id'))  
    user = db.relationship('UserAD', backref=db.backref('notifications', lazy=True))
    message = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_read = db.Column(db.Boolean, default=False)
    is_read_alert = db.Column(db.Boolean, default=False)  
    is_deleted = db.Column(db.Boolean, default=False)

    email_id = db.Column(db.Integer, nullable=True)  
    source = db.Column(db.String(50), default='email')  

    

class LoginLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_ad.id'))  
    user_agent = db.Column(db.String(255))  
    ip_address = db.Column(db.String(255))  
    login_time = db.Column(db.DateTime, default=db.func.current_timestamp())  

from sqlalchemy import LargeBinary
from sqlalchemy import Boolean, Column

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255))
    encrypted_message = db.Column(LargeBinary, nullable=False)  
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_handled = db.Column(db.Boolean, default=False)  


class UserAD(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role = db.Column(db.String(20), default="user")
    secret_key = db.Column(db.String(64))
    first_login = db.Column(db.Boolean, default=True)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)



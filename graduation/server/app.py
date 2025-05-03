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
from sqlalchemy import or_, and_
import re
import jwt
import base64
import binascii
from datetime import datetime, timedelta
import ldap3
from ldap3.core.exceptions import LDAPBindError
from flask_cors import CORS
import requests
import html
from markupsafe import escape
from sqlalchemy import func
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.config.from_object(Config)
SECRET_KEY = app.config["SECRET_KEY"]
CORS(app, origins=["http://localhost:5500"], supports_credentials=True)


from models import db, Email, Log, Notification, LoginLog, ContactMessage, UserAD  

db.init_app(app)  
migrate = Migrate(app, db)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pragmas': {'journal_mode': 'WAL'}
}


SECRET_KEY = app.config["SECRET_KEY"]
MAILGUN_API_KEY = app.config["MAILGUN_API_KEY"]
MAILGUN_DOMAIN = app.config["MAILGUN_DOMAIN"]
MAILGUN_BASE_URL = app.config["MAILGUN_BASE_URL"]

LDAP_SERVER = app.config["LDAP_SERVER"]
LDAP_PORT = app.config["LDAP_PORT"]
LDAP_BASE_DN = app.config["LDAP_BASE_DN"]
LDAP_USER_DN = app.config["LDAP_USER_DN"]


#generate hash
def generate_hash(content):
   
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

# generate secret_key
def generate_secret_key():
    return pyotp.random_base32()  



def check_domain(sender_email):
    domain = sender_email.split('@')[1]
    if domain != 'emailchecker4u.com':
        return False
    return True

# load PU
def load_public_key():
    with open("public.pem", "rb") as f:
        return RSA.import_key(f.read())


def encrypt_message(message, pub_key):
    cipher = PKCS1_OAEP.new(pub_key)
    encrypted_message = cipher.encrypt(message.encode())
    return base64.b64encode(encrypted_message).decode()  

#load PR
def load_private_key():
    with open("private.pem", "rb") as f:
        return RSA.import_key(f.read())


def decrypt_message(encrypted_message, priv_key):
    try:
        decoded_message = base64.b64decode(encrypted_message)
        cipher = PKCS1_OAEP.new(priv_key)
        decrypted_message = cipher.decrypt(decoded_message)
        return decrypted_message.decode()
    except (binascii.Error, ValueError):
        return "Error in decryption"


def sign_message(message, private_key):
    h = SHA256.new(message.encode())  
    signature = pkcs1_15.new(private_key).sign(h)
    return base64.b64encode(signature).decode()


def verify_signature(message, signature, public_key):
    h = SHA256.new(message.encode())
    signature = base64.b64decode(signature)
    try:
        pkcs1_15.new(public_key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        return False


def is_strong_password(password, username):
    if len(password) < 7:
        return "Password must be at least 7 characters long."

    types = 0
    if re.search(r"[A-Z]", password): types += 1
    if re.search(r"[a-z]", password): types += 1
    if re.search(r"[0-9]", password): types += 1
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): types += 1

    if types < 3:
        return "Password must include at least 3 of the following: uppercase letters, lowercase letters, digits, special characters."

    if username.lower() in password.lower():
        return "Password must not contain your username."

    return None  


from flask_cors import cross_origin



@app.route('/user_info', methods=['GET'])
@cross_origin()
@token_required
def get_user_info(current_user):
    return jsonify({
        "first_name": html.escape(current_user.first_name.strip()),
        "last_name": html.escape((current_user.last_name or "").strip()),
        "email": html.escape(current_user.email.strip()),
        "role": html.escape(current_user.role.strip())
    }), 200




@app.route('/register_user', methods=['POST'])
@token_required
def register_user(current_user):
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized. Admins only."}), 403

    data = request.get_json()
    first_name = html.escape(data.get("first_name", "").strip())
    last_name = html.escape(data.get("last_name", "").strip())
    username = html.escape(data.get("username", "").strip())
    password = data.get("password", "").strip()


    if not all([first_name, last_name, username, password]):
        return jsonify({"error": "Missing required fields"}), 400


    if len(first_name) > 50 or len(last_name) > 50:
        return jsonify({"error": "First name or last name too long."}), 400
    if len(username) > 30:
        return jsonify({"error": "Username too long."}), 400


    from models import UserAD
    if UserAD.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    full_name = f"{first_name} {last_name}"
    user_dn = f"CN={full_name},CN=Users,{LDAP_BASE_DN}"

    try:
        server = ldap3.Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True, get_info=ldap3.ALL)
        conn = ldap3.Connection(
             server,
            user=f"CN={app.config['LDAP_ADMIN_USER']},CN=Users,{LDAP_BASE_DN}",
            password=app.config['LDAP_ADMIN_PASSWORD'],
            auto_bind=True
             )


        conn.add(user_dn, ['top', 'person', 'organizationalPerson', 'user'], {
            'cn': full_name,
            'givenName': first_name,
            'sn': last_name,
            'displayName': full_name,
            'userPrincipalName': f"{username}@emailchecker4u.com",
            'sAMAccountName': username
        })

        if not conn.result['description'] == 'success':
            return jsonify({"error": "Failed to create user", "details": conn.result}), 500

        conn.extend.microsoft.modify_password(user_dn, password)

        conn.modify(user_dn, {
            'userAccountControl': [(ldap3.MODIFY_REPLACE, [512])]
        })

        return jsonify({"message": f"User '{username}' has been registered successfully in Active Directory."}), 200

    except Exception as e:
        return jsonify({"error": "LDAP error", "details": str(e)}), 500


def generate_token(username):
    payload = {
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token







limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = html.escape(data.get('email'))
    password = html.escape(data.get('password'))

    if not username or not password:
        return jsonify({'error': 'Email and password are required'}), 400

    user = UserAD.query.filter_by(username=username).first()


    if user and user.locked_until and user.locked_until > datetime.utcnow():
        return jsonify({'error': 'Account is locked. Try again later.'}), 403

    try:
        server = ldap3.Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True, get_info=ldap3.ALL)
        user_dn = f'CN={username},CN=Users,{LDAP_BASE_DN}'
        conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)

        if conn.bind():
            if user:
                user.failed_attempts = 0
                user.locked_until = None
                db.session.commit()

            conn.search(LDAP_USER_DN, f'(cn={username})', attributes=['mail', 'givenName', 'sn', 'userPrincipalName'])
            entry = conn.entries[0]

            ldap_email = str(entry.userPrincipalName.value) if 'userPrincipalName' in entry else f"{username}@emailchecker4u.com"
            first_name = entry.givenName.value if 'givenName' in entry else ''
            last_name = entry.sn.value if 'sn' in entry else ''

            if not user:
                secret = pyotp.random_base32()
                user = UserAD(
                    username=username,
                    email=ldap_email,
                    first_name=first_name,
                    last_name=last_name,
                    role="admin" if check_admin(username) else "user",
                    secret_key=secret,
                    first_login=True,
                    failed_attempts=0,
                    locked_until=None
                )
                db.session.add(user)
                db.session.commit()

                otp_uri = pyotp.TOTP(secret).provisioning_uri(name=username, issuer_name="IntegriMail")
                return jsonify({
                    'message': 'First login, please scan the QR code',
                    'otp_uri': otp_uri,
                    'requires_2fa': True
                }), 200

            if user.first_login:
                otp_uri = pyotp.TOTP(user.secret_key).provisioning_uri(name=username, issuer_name="IntegriMail")
                return jsonify({
                    'message': 'First login, please scan the QR code',
                    'otp_uri': otp_uri,
                    'requires_2fa': True
                }), 200

            return jsonify({
                'message': 'Enter your 2FA code',
                'requires_2fa': True
            }), 200

        else:
            raise LDAPBindError("Invalid bind")

    except LDAPBindError:
        if user:
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)


                admins = UserAD.query.filter_by(role='admin').all()
                for admin in admins:
                    db.session.add(Notification(
                        user_id=admin.id,
                        message=f"🚫 User '{username}' has been locked due to failed login attempts."
                    ))

            db.session.commit()

        return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'error': 'LDAP error', 'details': str(e)}), 500

# ========= Route: Verify 2FA =========
@app.route('/verify_2fa', methods=['POST'])
def verify_2fa():
    import html
    def clean_xss(val): return html.escape(val.strip()) if isinstance(val, str) else val

    data = request.get_json()
    username = clean_xss(data.get('email'))
    token_input = clean_xss(data.get('token'))

    if not username or not token_input:
        return jsonify({'error': 'Email and token are required'}), 400

    user = UserAD.query.filter_by(username=username).first()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    totp = pyotp.TOTP(user.secret_key)
    if totp.verify(token_input):
        user.first_login = False
        db.session.commit()

        login_log = LoginLog(
            user_id=user.id,
            user_agent=request.user_agent.string,
            ip_address=request.remote_addr
        )
        db.session.add(login_log)
        db.session.commit()

        token = generate_token(username)

        return jsonify({
            'message': 'Login successful!',
            'token': token,
            'role': 'admin' if check_admin(username) else 'user',
            'requires_2fa': False
        }), 200
    else:

        return jsonify({'error': 'Invalid 2FA token'}), 401


# ========= Helper: Check if Admin =========
def check_admin(username):
    try:
        server = ldap3.Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True, get_info=ldap3.ALL)
        user_dn = f'CN={username},CN=Users,{LDAP_BASE_DN}'


        conn = ldap3.Connection(
            server,
            user=f"CN={app.config['LDAP_ADMIN_USER']},CN=Users,{LDAP_BASE_DN}",
            password=app.config['LDAP_ADMIN_PASSWORD'],
            auto_bind=True
        )

        if conn.bind():
            conn.search(LDAP_USER_DN, f'(cn={username})', attributes=['memberOf'])
            if conn.entries:
                user_entry = conn.entries[0]
                member_of = user_entry.memberOf.values if 'memberOf' in user_entry else []
                for group in member_of:
                    if 'Domain Admins' in group:
                        return True
        return False

    except Exception as e:
        print(f"Error checking admin status: {e}")
        return False






def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@app.route('/send_email', methods=['POST'])
@token_required
def send_email(current_user):
    data = request.get_json()
    
    #  XSS + Empty check
    receiver_email = escape(data.get('receiver_email', '')).strip()
    subject = escape(data.get('subject', 'No Subject')).strip()
    content = escape(data.get('content', '')).strip()

    # Validation
    if not receiver_email or not content:
        return jsonify({'error': 'Missing fields'}), 400
    if len(content) > 5000:
        return jsonify({'error': 'Email content too long'}), 400
    if not is_valid_email(receiver_email):
        return jsonify({'error': 'Invalid receiver email format'}), 400
    if receiver_email == current_user.email:
        return jsonify({'error': 'You cannot send an email to yourself'}), 400


    mailgun_url = app.config["MAILGUN_BASE_URL"]
    mailgun_api_key = app.config["MAILGUN_API_KEY"]


    response = requests.post(
        mailgun_url,
        auth=("api", mailgun_api_key),
        data={
            "from": current_user.email,
            "to": receiver_email,
            "subject": subject,
            "text": content
        }
    )

    if response.status_code != 200:
        return jsonify({'error': 'Failed to send email'}), 500

    is_internal = (
        current_user.email.endswith('@emailchecker4u.com') and
        receiver_email.endswith('@emailchecker4u.com')
    )

    if is_internal:
        email_hash = generate_hash(content)
        public_key = load_public_key()
        private_key = load_private_key()
        encrypted_content = encrypt_message(content, public_key)
        signature = sign_message(encrypted_content, private_key)

        receiver = UserAD.query.filter_by(email=receiver_email).first()
        if not receiver:
            return jsonify({'error': 'Receiver not found'}), 404

        new_email = Email(
            sender_id=current_user.id,
            receiver_id=receiver.id,
            sender_email=current_user.email,
            receiver_email=receiver_email,
            subject=subject,
            content=encrypted_content,
            hash=email_hash,
            signature=signature,
            hash_status="Valid"
        )
        db.session.add(new_email)
        db.session.commit()


        notification = Notification(
            user_id=receiver.id,
            message=f"📩 New internal email received from {current_user.email}",
            email_id=new_email.id,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()

        log = Log(email_id=new_email.id, status="Sent")
        db.session.add(log)
        db.session.commit()

    else:
        new_email = Email(
            sender_id=current_user.id,
            receiver_id=None,
            sender_email=current_user.email,
            receiver_email=receiver_email,
            subject=subject,
            content=content,
            hash=None,
            signature=None,
            hash_status="External"
        )
        db.session.add(new_email)
        db.session.commit()

        log = Log(email_id=new_email.id, status="Sent (External)")
        db.session.add(log)
        db.session.commit()

    print("✅ Current User Email:", current_user.email)

    return jsonify({'message': 'Email sent and stored successfully'}), 200

@app.route('/mailgun/inbound', methods=['POST'])
def receive_from_mailgun():
    sender_email = escape(request.form.get('sender', '').strip())
    recipient_email = escape(request.form.get('recipient', '').strip())
    subject = escape(request.form.get('subject', 'No Subject').strip())
    content = escape(request.form.get('body-plain', '').strip())

    # ✅ Checks
    if not sender_email or not recipient_email or not content:
        return jsonify({"error": "Missing data from Mailgun"}), 400
    if len(content) > 5000:
        return jsonify({"error": "Content too long"}), 400
    if not is_valid_email(sender_email) or not is_valid_email(recipient_email):
        return jsonify({"error": "Invalid email format"}), 400

    is_internal = (
        sender_email.endswith('@emailchecker4u.com') and
        recipient_email.endswith('@emailchecker4u.com')
    )

    try:
        if is_internal:
            email_hash = generate_hash(content)
            public_key = load_public_key()
            private_key = load_private_key()
            encrypted_content = encrypt_message(content, public_key)
            signature = sign_message(encrypted_content, private_key)

            sender = UserAD.query.filter_by(email=sender_email).first()
            receiver = UserAD.query.filter_by(email=recipient_email).first()

            if not sender or not receiver:
                return jsonify({"error": "Sender or receiver not found"}), 404

            existing_email = Email.query.filter_by(
                sender_email=sender_email,
                receiver_email=recipient_email,
                subject=subject,
                hash=email_hash
            ).first()
            if existing_email:
                return jsonify({"message": "Duplicate internal email skipped."}), 200

            new_email = Email(
                sender_id=sender.id,
                receiver_id=receiver.id,
                sender_email=sender_email,
                receiver_email=recipient_email,
                subject=subject,
                content=encrypted_content,
                hash=email_hash,
                signature=signature,
                hash_status="Valid"
            )

        else:
            new_email = Email(
                sender_id=None,
                receiver_id=None,
                sender_email=sender_email,
                receiver_email=recipient_email,
                subject=subject,
                content=content,
                hash=None,
                signature=None,
                hash_status="External"
            )

        db.session.add(new_email)
        db.session.commit()

        # ✅ Notification
        receiver = UserAD.query.filter_by(email=recipient_email).first()
        if receiver:
            message_type = "internal" if is_internal else "external"
            notif = Notification(
                user_id=receiver.id,
                message=f"📩 New {message_type} email received from {sender_email}",
                is_read=False,
                email_id=new_email.id
            )
            db.session.add(notif)

            if is_internal:
                log = Log(email_id=new_email.id, status="Received")
                db.session.add(log)

            db.session.commit()

        return jsonify({"message": "Email received successfully"}), 200

    except Exception as e:
        print("Error receiving email:", e)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/user/dashboard', methods=['GET'])
@token_required
def user_dashboard(current_user):
    inbox_count = Email.query.filter_by(receiver_email=current_user.email).count()
    sent_count = Email.query.filter_by(sender_email=current_user.email).count()

    tampered_count = Email.query.filter_by(receiver_email=current_user.email, hash_status="Tampered").count()
    verified_count = Email.query.filter_by(receiver_email=current_user.email, hash_status="Valid").count()
    external_count = Email.query.filter_by(receiver_email=current_user.email, hash_status="External").count()

    internal_verified_count = Email.query.filter_by(receiver_email=current_user.email, hash_status="Valid").count()
    internal_tampered_count = Email.query.filter_by(receiver_email=current_user.email, hash_status="Tampered").count()

    return jsonify({
        "inbox_count": inbox_count,
        "sent_count": sent_count,
        "tampered_count": tampered_count,
        "verified_count": verified_count,
        "external_count": external_count,
        "internal_verified_count": internal_verified_count,
        "internal_tampered_count": internal_tampered_count,
    }), 200




@app.route('/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = UserAD.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    totp = pyotp.TOTP(user.secret_key)
    verification_message = "Enter the 2FA code from your authenticator app to reset your password."

    return jsonify({"message": verification_message, "email": email}), 200


@app.route('/verify_2fa_for_reset', methods=['POST'])
def verify_2fa_for_reset():
    data = request.json
    email = data.get('email')
    token = data.get('token')

    if not email or not token:
        return jsonify({"error": "Email and 2FA token are required"}), 400

    user = UserAD.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    totp = pyotp.TOTP(user.secret_key)
    if not totp.verify(token):
        return jsonify({"error": "Invalid 2FA token"}), 400

    expiration_time = datetime.now() + timedelta(minutes=15)
    reset_token = jwt.encode({'user_id': user.id, 'exp': expiration_time}, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({"message": "2FA verified. Use this token to reset your password.", "reset_token": reset_token}), 200


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

    user = UserAD.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not new_password or not confirm_password:
        return jsonify({"error": "Missing required fields"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    password_strength_error = is_strong_password(new_password, user.username)
    if password_strength_error:
        return jsonify({"error": password_strength_error}), 400


    try:
        user_dn = f"CN={user.username},CN=Users,{LDAP_BASE_DN}"
        server = ldap3.Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True, get_info=ldap3.ALL)
        conn = ldap3.Connection(server, user=f"CN={app.config['LDAP_ADMIN_USER']},CN=Users,{LDAP_BASE_DN}",
    password=app.config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

        if not conn.bind():
            return jsonify({"error": "Failed to bind to LDAP server"}), 500


        success = conn.extend.microsoft.modify_password(user_dn, new_password)
        if not success:
            return jsonify({"error": "Failed to update password in Active Directory"}), 500

    except Exception as e:
        return jsonify({"error": "LDAP error", "details": str(e)}), 500


    notification = Notification(user_id=user.id, message="Your password has been reset successfully.", is_read=False)
    db.session.add(notification)
    db.session.commit()

    return jsonify({"message": "Password reset successful!"}), 200


@app.route('/change-password', methods=['POST'])
@cross_origin()
def change_password():
    token = request.headers.get("Authorization")

    if not token:
        return jsonify({"error": "Missing token"}), 401

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        username = payload.get("username")  
        if not username:
            return jsonify({"error": "Invalid token data"}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    user = UserAD.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    confirm_password = data.get("confirm_password")

    if not old_password or not new_password or not confirm_password:
        return jsonify({"error": "Missing required fields"}), 400

    if new_password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    password_strength_error = is_strong_password(new_password, username)
    if password_strength_error:
        return jsonify({"error": password_strength_error}), 400

    try:

        user_dn = f"CN={username},CN=Users,{LDAP_BASE_DN}"
        test_conn = ldap3.Connection(
            ldap3.Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True),
            user=user_dn,
            password=old_password,
            auto_bind=True
        )
    except Exception:
        return jsonify({"error": "Old password is incorrect"}), 400

    try:
        
        admin_cn = app.config["LDAP_ADMIN_CN"]
        admin_password = app.config["LDAP_ADMIN_PASSWORD"]
        admin_dn = f"CN={admin_cn},CN=Users,{LDAP_BASE_DN}"

        conn = ldap3.Connection(
    ldap3.Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True),
    user=admin_dn,
    password=admin_password,
    auto_bind=True
)


        
        success = conn.extend.microsoft.modify_password(user_dn, new_password)
        if not success:
            return jsonify({"error": "Failed to update password in Active Directory"}), 500
            print("🔴 Modify error:", conn.result)

    except Exception as e:
        return jsonify({"error": "LDAP error", "details": str(e)}), 500

    
    notification = Notification(user_id=user.id, message="Your password has been changed successfully.", is_read=False)
    db.session.add(notification)
    db.session.commit()

    return jsonify({"message": "Password changed successfully!"}), 200

@app.route('/inbox', methods=['GET'])
@cross_origin()
@token_required
def get_user_inbox(current_user):
    emails = Email.query.filter_by(receiver_email=current_user.email).order_by(Email.created_at.desc()).all()

    def clean_email_thread(content):
        if "wrote:" in content:
            content = content.split("wrote:")[0].strip()
        if "On " in content:
            content = content.split("On ")[0].strip()
        return content

    private_key = load_private_key()

    inbox = []
    for email in emails:
        try:
            content = decrypt_message(email.content, private_key) if email.hash_status == "Valid" else clean_email_thread(email.content)
        except Exception:
            content = "Error decrypting email"

        inbox.append({
            "id": email.id,
            "from": email.sender_email,
            "to": email.receiver_email,
            "subject": html.escape(email.subject or "No Subject"),
            "content": html.escape(clean_email_thread(content)),
            "received_at": email.created_at.strftime("%Y-%m-%d %H:%M"),
            "integrity": email.hash_status
        })

    return jsonify({"inbox": inbox})

def clean_email_thread(content):

        if "wrote:" in content:
            content = content.split("wrote:")[0].strip()
        if "On " in content:
            content = content.split("On ")[0].strip()
        return content


@app.route('/email/<int:email_id>', methods=['GET'])
@token_required
def get_email_detail(current_user, email_id):
    email = Email.query.filter_by(id=email_id, receiver_email=current_user.email).first()

    if not email:
        return jsonify({"error": "Email not found"}), 404

    private_key = load_private_key()
    try:
        content = decrypt_message(email.content, private_key) if email.hash_status == "Valid" else email.content
    except Exception:
        content = "Error decrypting email"

    return jsonify({
        "from": email.sender_email,
        "to": email.receiver_email,
        "subject": html.escape(email.subject),
        "date": email.created_at.strftime("%Y-%m-%d %H:%M"),
        "integrity": email.hash_status,
        "content": html.escape(clean_email_thread(content)),
    }), 200


# view_logs
@app.route('/logs', methods=['GET'])
@token_required
def view_logs(current_user):
    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403

    emails = Email.query.order_by(Email.created_at.desc()).all()
    private_key = load_private_key()

    email_list = []
    for email in emails:
        try:
            content = decrypt_message(email.content, private_key) if email.hash_status == "Valid" else clean_email_thread(email.content)
        except Exception:
            content = "Error decrypting email"

        email_list.append({
    "id": email.id,
    "from": html.escape(email.sender_email),
    "to": html.escape(email.receiver_email),
    "subject": html.escape(email.subject),
    "content": html.escape(clean_email_thread(content)),
    "hash": email.hash,
    "integrity": email.hash_status,
    "created_at": email.created_at.strftime("%Y-%m-%d %H:%M")
})


    return jsonify({"emails": email_list}), 200



@app.route('/sent_emails', methods=['GET'])
@token_required
def get_sent_emails(current_user):
    sent_emails = Email.query.filter_by(sender_email=current_user.email).order_by(Email.created_at.desc()).all()

    emails_data = []
    private_key = load_private_key()

    for email in sent_emails:
        try:
            content = decrypt_message(email.content, private_key) if email.hash_status == "Valid" else clean_email_thread(email.content)
        except Exception:
            content = "Error decrypting email"

        emails_data.append({
    "id": email.id,
    "from": html.escape(email.sender_email),
    "to": html.escape(email.receiver_email),
    "subject": html.escape(email.subject or "No Subject"),
    "content": html.escape(content),
    "created_at": email.created_at.strftime("%Y-%m-%d %H:%M"),
    "integrity": email.hash_status
})


    return jsonify({"sent_emails": emails_data}), 200



@app.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
#notification for admin
    if current_user.role == 'admin':
        notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    else:

        notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).filter(
            (Notification.source != 'contact') | (Notification.source.is_(None))
        ).all()

    notifications_list = []
    for notification in notifications:
        safe_message = html.escape(notification.message) if notification.message else ''
        user_email = html.escape(notification.user.email) if notification.user and notification.user.email else ''

        notifications_list.append({
            "id": notification.id,
            "message": safe_message,
            "created_at": notification.created_at,
            "user_name": user_email,
            "is_read": notification.is_read
        })

    unread_count = len(notifications_list)

    return jsonify({
        "notifications": notifications_list,
        "new_notifications_count": unread_count
    }), 200

@app.route('/notifications/mark_as_read', methods=['POST'])
@token_required
def mark_notifications_as_read(current_user):

    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()

    return jsonify({"message": "Notifications marked as read"}), 200




@app.route('/alerts', methods=['GET'])
@token_required
def get_alerts(current_user):
    alerts = Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.is_deleted == False,
        or_(
            Notification.source == None,
            Notification.source != 'contact'
        )
    ).order_by(Notification.id.desc()).all()

    result = []
    for alert in alerts:
        email = Email.query.filter_by(id=alert.email_id).first() if alert.email_id else None
        result.append({
            'id': alert.id,
            'message': html.escape(alert.message) if alert.message else '',
            'is_read_alert': alert.is_read_alert,
            'email_id': alert.email_id,
            'subject': html.escape(email.subject) if email and email.subject else 'No Subject'
        })

    return jsonify(result), 200

@app.route('/alerts/read/<int:id>', methods=['PUT'])
@token_required
def mark_alert_as_read(current_user, id):
    alert = Notification.query.filter_by(id=id, user_id=current_user.id).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404


    alert.is_read_alert = True


    duplicates = Notification.query.filter(
        Notification.message == alert.message,
        Notification.user_id != current_user.id,
        Notification.is_read_alert == False
    ).all()

    for dup in duplicates:
        dup.is_read_alert = True

    db.session.commit()

    return jsonify({'message': 'Alert marked as read for all admins'}), 200


@app.route('/alerts/delete/<int:id>', methods=['DELETE'])
@token_required
def delete_alert(current_user, id):
    alert = Notification.query.filter_by(id=id, user_id=current_user.id).first()
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404

    alert.is_deleted = True
    db.session.commit()

    return jsonify({'message': 'Alert deleted'}), 200



@app.route('/contact', methods=['POST'])
def submit_contact():
    data = request.json
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()


    if not name or not email or not message:
        return jsonify({"error": "Missing required fields"}), 400


    if len(name) > 100 or len(subject) > 150 or len(message) > 5000:
        return jsonify({"error": "Input too long"}), 400


    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        return jsonify({"error": "Invalid email format"}), 400

    try:

        public_key = load_public_key()
        encrypted_message = encrypt_message(message, public_key)


        contact_message = ContactMessage(
            name=html.escape(name),
            email=html.escape(email),
            subject=html.escape(subject),
            encrypted_message=encrypted_message.encode() if isinstance(encrypted_message, str) else encrypted_message
        )
        db.session.add(contact_message)
        db.session.commit()


        admins = UserAD.query.filter_by(role='admin').all()
        for admin in admins:
            notif = Notification(
                user_id=admin.id,
                message=html.escape(f"📩 New Contact Message from {email}"),
                is_read=False,
                source='contact'
            )
            db.session.add(notif)

        db.session.commit()
        return jsonify({"message": "Contact message sent successfully!"}), 200

    except Exception as e:
        print("Error while submitting contact message:", e)
        return jsonify({"error": "Internal server error"}), 500



@app.route('/admin/login_logs', methods=['GET'])
@token_required
def get_login_logs(current_user):
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized. Admins only."}), 403

    logs = LoginLog.query.order_by(LoginLog.login_time.desc()).all()

    all_logs = []
    for log in logs:
        user = UserAD.query.get(log.user_id)
        all_logs.append({
            "user_email": escape(user.email) if user else "Unknown",
            "ip_address": escape(log.ip_address),
            "user_agent": escape(log.user_agent),
            "login_time": log.login_time.strftime("%Y-%m-%d %H:%M")
        })

    return jsonify({"logs": all_logs}), 200


@app.route('/admin/contact_messages', methods=['GET'])
@token_required
def get_contact_messages(current_user):
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized. Admins only."}), 403

    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    private_key = load_private_key()

    all_messages = []
    for msg in messages:
        try:
            decrypted_message = decrypt_message(msg.encrypted_message, private_key)
            decrypted_message = html.escape(decrypted_message)
        except Exception:
            decrypted_message = "Error decrypting message"

        all_messages.append({
            "id": msg.id,
            "name": html.escape(msg.name),
            "email": html.escape(msg.email),
            "subject": html.escape(msg.subject),
            "message": decrypted_message,
            "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_handled": msg.is_handled
        })

    return jsonify({"messages": all_messages}), 200


@app.route('/admin/contact/mark_done/<int:message_id>', methods=['POST'])
@token_required
def mark_contact_done(current_user, message_id):
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized. Admins only."}), 403

    contact_message = ContactMessage.query.get(message_id)
    if not contact_message:
        return jsonify({'error': 'Message not found'}), 404

    contact_message.is_handled = True
    db.session.commit()

    return jsonify({'message': 'Message marked as done.'}), 200



@app.route('/admin/users', methods=['GET'])
@token_required
def list_ad_users(current_user):
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized. Admins only."}), 403

    try:
        server = ldap3.Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True, get_info=ldap3.ALL)
        conn = ldap3.Connection(
            server,
            user=f"CN={app.config['LDAP_ADMIN_USER']},CN=Users,{LDAP_BASE_DN}",
            password=app.config['LDAP_ADMIN_PASSWORD'],
            auto_bind=True
        )

        conn.search(
            search_base=f"CN=Users,{LDAP_BASE_DN}",
            search_filter='(objectClass=user)',
            attributes=['cn', 'sAMAccountName', 'userPrincipalName', 'memberOf']
        )

        users = []
        for entry in conn.entries:
            username = str(entry.sAMAccountName)
            full_name = str(entry.cn)
            email = str(entry.userPrincipalName) if 'userPrincipalName' in entry else f"{username}@emailchecker4u.com"
            member_of = entry.memberOf.values if 'memberOf' in entry else []
            is_admin = any('Domain Admins' in group for group in member_of)

            users.append({
                "full_name": full_name,
                "username": username,
                "email": email,
                "role": "admin" if is_admin else "user"
            })

        return jsonify({"users": users}), 200

    except Exception as e:
        return jsonify({"error": "LDAP error", "details": str(e)}), 500




@app.route('/admin/delete_user', methods=['DELETE'])
@token_required
def delete_ad_user(current_user):
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized. Admins only."}), 403

    data = request.get_json()
    cn = data.get("cn")
    if not cn:
        return jsonify({"error": "Missing CN"}), 400

    try:

        server = ldap3.Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True)
        conn = ldap3.Connection(server, user=f"CN={app.config['LDAP_ADMIN_USER']},CN=Users,{LDAP_BASE_DN}",
            password=app.config['LDAP_ADMIN_PASSWORD'], auto_bind=True)

        conn.search(
            search_base=f"CN=Users,{LDAP_BASE_DN}",
            search_filter=f"(cn={cn})",
            attributes=['distinguishedName']
        )

        if not conn.entries:
            return jsonify({"error": "User not found in Active Directory"}), 404

        user_dn = conn.entries[0].distinguishedName.value
        conn.delete(user_dn)


        from models import UserAD
        user_in_db = UserAD.query.filter(UserAD.first_name == cn.split()[0], UserAD.last_name == ' '.join(cn.split()[1:])).first()
        if user_in_db:
            db.session.delete(user_in_db)
            db.session.commit()

        return jsonify({"message": f"User '{cn}' has been deleted from AD and DB."}), 200

    except Exception as e:
        return jsonify({"error": "LDAP error", "details": str(e)}), 500




@app.route('/admin/change_role/<username>', methods=['PUT'])
@token_required
def change_ad_user_role(current_user, username):
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized. Admins only."}), 403

    data = request.get_json()
    action = data.get("action")  # "upgrade" or "downgrade"

    try:
        server = ldap3.Server(LDAP_SERVER, port=LDAP_PORT, use_ssl=True)
        conn = ldap3.Connection(
            server,
            user=f"CN={app.config['LDAP_ADMIN_USER']},CN=Users,{LDAP_BASE_DN}",
            password=app.config['LDAP_ADMIN_PASSWORD'],
            auto_bind=True
        )


        conn.search(
            search_base=f"CN=Users,{LDAP_BASE_DN}",
            search_filter=f"(sAMAccountName={username})",
            attributes=['distinguishedName']
        )

        if not conn.entries:
            return jsonify({"error": "User not found in Active Directory"}), 404

        user_dn = conn.entries[0].distinguishedName.value
        admin_group_dn = f"CN=Domain Admins,CN=Users,{LDAP_BASE_DN}"


        if action == "upgrade":
            conn.modify(admin_group_dn, {'member': [(ldap3.MODIFY_ADD, [user_dn])]})
        elif action == "downgrade":
            conn.modify(admin_group_dn, {'member': [(ldap3.MODIFY_DELETE, [user_dn])]})
        else:
            return jsonify({"error": "Invalid action."}), 400


        user = UserAD.query.filter(func.replace(UserAD.username, " ", "") == username).first()
        if user:
            user.role = "admin" if action == "upgrade" else "user"
            db.session.commit()

        return jsonify({"message": f"User '{username}' role changed to {action} successfully."}), 200

    except Exception as e:
        return jsonify({"error": "LDAP error", "details": str(e)}), 500 

@app.route('/admin/all_emails', methods=['GET'])
@token_required
def get_all_emails(current_user):
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized. Admins only."}), 403

    try:
        emails = Email.query.order_by(Email.created_at.desc()).all()

        def clean_email_thread(content):
            if "wrote:" in content:
                content = content.split("wrote:")[0].strip()
            if "On " in content:
                content = content.split("On ")[0].strip()
            return content

        private_key = load_private_key()

        all_emails = []
        for email in emails:
            try:
                if email.hash_status == "Valid":
                    content = decrypt_message(email.content, private_key)
                else:
                    content = clean_email_thread(email.content)
            except Exception:
                content = "Error decrypting email"

            all_emails.append({
                "id": email.id,
                "sender_email": html.escape(email.sender_email),
                "receiver_email": html.escape(email.receiver_email),
                "subject": html.escape(email.subject or "No Subject"),
                "content": html.escape(clean_email_thread(content)),
                "hash_status": email.hash_status,
                "created_at": email.created_at.strftime("%Y-%m-%d %H:%M")
            })

        return jsonify({"emails": all_emails}), 200

    except Exception as e:
        print("🔥 Error fetching emails:", e)
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
    


if __name__ == '__main__':
    with app.app_context():
        print(" Database path:", app.config["SQLALCHEMY_DATABASE_URI"])
        db.create_all()
        print(" Tables created successfully!")
    app.run(debug=True)

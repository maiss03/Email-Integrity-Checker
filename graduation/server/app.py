from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from auth import token_required 

app = Flask(__name__)
app.config.from_object(Config)

from models import db, User, Email  # استيراد `db` بعد تعريف `app`

db.init_app(app)  #  ربط `db` بالتطبيق
migrate = Migrate(app, db)

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
        # إنشاء التوكن مع مدة صلاحية 24 ساعة
        expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        token = jwt.encode({'user_id': user.id, 'exp': expiration_time}, SECRET_KEY, algorithm='HS256')

        return jsonify({"message": "Login successful!", "token": token})

    return jsonify({"error": "Invalid email or password!"}), 401


@app.route('/send_email', methods=['POST'])
@token_required  # التأكد من وجود التوكن
def send_email(current_user):
    data = request.json
    if not data.get('receiver_id') or not data.get('content'):
        return jsonify({"error": "Receiver ID and content are required!"}), 400

    # إنشاء الإيميل
    new_email = Email(sender_id=current_user.id, receiver_id=data['receiver_id'], content=data['content'], hash="somehash")
    db.session.add(new_email)
    db.session.commit()

    return jsonify({"message": "Email sent successfully!"}), 200

@app.route('/')
def home():
    return "Backend is running!"

if __name__ == '__main__':
    with app.app_context():
        print(" Database path:", app.config["SQLALCHEMY_DATABASE_URI"])
        db.create_all()
        print(" Tables created successfully!")
    app.run(debug=True)

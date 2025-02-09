import jwt
from functools import wraps
from flask import request, jsonify
from models import User  # لازم نستورد `User` عشان نتحقق من المستخدم

SECRET_KEY = "supersecretkey"  # استخدمي نفس الـ SECRET_KEY الموجود في `app.py`

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")  # الحصول على التوكن من الـ header

        if not token:
            return jsonify({"error": "Token is missing!"}), 401  # رفض الدخول

        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  # فك التشفير والتحقق
            current_user = User.query.get(decoded["user_id"])  # جلب المستخدم من قاعدة البيانات
        except:
            return jsonify({"error": "Token is invalid or expired!"}), 401  # رفض الدخول

        return f(current_user, *args, **kwargs)  # تمرير المستخدم للـ API المحمي

    return decorated

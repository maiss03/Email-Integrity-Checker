from app import db, app
from models import User, Email

with app.app_context():
    new_user = User(email="test@example.com", password="12345")
    db.session.add(new_user)
    db.session.commit()

    print("✅ User added successfully!")

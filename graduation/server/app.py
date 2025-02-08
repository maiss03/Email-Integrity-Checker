from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///email_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.route('/')
def home():
    return jsonify({"message": "Backend is running!"})

if __name__ == '__main__':
    with app.app_context():  # Fix: Use application context before creating the database
        db.create_all()  # Create the database tables
    app.run(debug=True)

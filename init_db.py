from config import app, db
from models import User, Issue

with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
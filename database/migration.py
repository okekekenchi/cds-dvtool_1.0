# migrations.py
from database.database import engine, Base
from models.user import User
from models.session import Session
from models.validation_checklist import ValidationChecklist

def init_db():
    """Initialize the database, creating all tables"""
    Base.metadata.create_all(bind=engine)
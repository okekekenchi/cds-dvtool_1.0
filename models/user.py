from sqlalchemy import Column, String, JSON, Boolean, Integer
from models.base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    full_name = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    active = Column(Boolean, default=True, index=True)
    role = Column(String(50), default="user", nullable=False)
    created_by = Column(Integer)

    @classmethod
    def findByEmail(cls, db, email):
        return cls.where(db, email=email).first()
    
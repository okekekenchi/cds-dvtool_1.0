# models/post.py
from sqlalchemy import Column, String, Text, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from models.base import BaseModel

class ValidationChecklist(BaseModel):
    __tablename__ = "validation_checklists"
    
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    config = Column(JSON, default={})
    active = Column(Boolean, default=True)
    created_by = Column(Integer, nullable=False)
    
    # author = relationship("User", backref="posts")
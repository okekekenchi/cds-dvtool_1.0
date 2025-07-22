from sqlalchemy import Column, String, Text, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel

class ValidationChecklist(BaseModel):
    """Stores validation checklists with configurable tags and settings"""
    __tablename__ = "validation_checklists"
    
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    config = Column(JSON, default={"sheets": [], "joins": [], "conditions": []})
    active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    _default = {}
    
    # creator = relationship("User", backref="checklists")
    
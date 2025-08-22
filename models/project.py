from sqlalchemy import Column, String, Text, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Project(BaseModel):
    """Stores validation checklists with configurable tags and settings"""
    __tablename__ = "validation_checklists"
    extend_existing=True
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    file_name = Column(String(100), unique=True, nullable=False, index=True)
    rule_ids = Column(JSON, default=[])
    data = Column(JSON, default={})
    created_by = Column(Integer, ForeignKey('users.id'))
    
    _default = {}
    
    # creator = relationship("User", backref="checklists")
    
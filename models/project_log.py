from sqlalchemy import Column, String, Text, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel

class ProjectLog(BaseModel):
    """Stores validation checklists with configurable tags and settings"""
    __tablename__ = "project_logs"
    extend_existing=True
    
    name = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    file_name = Column(String(100), nullable=False)
    file_type = Column(String(100), nullable=False)
    version = Column(String(10), nullable=False, index=True)
    data = Column(JSON, default={})
    created_by = Column(Integer, ForeignKey('users.id'))
    
    _default = {}
    
    # creator = relationship("User", backref="checklists")
    
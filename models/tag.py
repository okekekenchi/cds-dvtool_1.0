from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Tag(BaseModel):
    __tablename__ = "tags"
    
    name = Column(String(50), unique=True, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    _default = {}
    
    creator = relationship("User", backref="tags")
    
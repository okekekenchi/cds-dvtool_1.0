from sqlalchemy import Column, String, Integer, ForeignKey
from models.base import BaseModel

class Tag(BaseModel):
    __tablename__ = "tags"
    
    name = Column(String(50), unique=True, nullable=False)
    created_by = Column(Integer)
    
    _default = {}
    
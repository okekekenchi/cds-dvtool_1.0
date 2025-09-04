from sqlalchemy import Column, String, Integer, Text
from models.base import BaseModel

class Tag(BaseModel):
    __tablename__ = "tags"
    
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_by = Column(Integer)
    
    _default = {}
    
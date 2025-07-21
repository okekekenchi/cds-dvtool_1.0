from sqlalchemy import Column, String, Text, Integer, Boolean
from models.base import BaseModel

class BhTaskType(BaseModel):
    __tablename__ = "bh_task_types"
    
    task_type = Column(String, unique=True, nullable=False)
    desc = Column(Text, unique=True)
    active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer)
    
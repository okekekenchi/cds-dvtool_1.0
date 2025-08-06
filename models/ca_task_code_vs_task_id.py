from sqlalchemy import Column, String, Integer, Boolean, Text
from models.base import BaseModel

class CaTaskCodeVsTaskId(BaseModel):
    __tablename__ = "ca_task_code_vs_task_ids"
    extend_existing=True
    
    task_code = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=False)
    active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer)
    
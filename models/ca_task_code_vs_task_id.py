from sqlalchemy import Column, String, Integer, Boolean
from models.base import BaseModel

class CaTaskCodeVsTaskId(BaseModel):
    __tablename__ = "ca_task_code_vs_task_ids"
    
    task_code = Column(String, unique=True, nullable=False)
    desc_1 = Column(String, nullable=False)
    desc_2 = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_by = Column(Integer)
    
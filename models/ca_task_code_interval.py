from sqlalchemy import Column, String, Text, Integer, Boolean
from models.base import BaseModel

class CaTaskCodeInterval(BaseModel):
    __tablename__ = "ca_task_code_intervals"
    
    task_code_interval = Column(String, unique=True, nullable=False)
    task_code_interval_desc = Column(Text, unique=True, nullable=False)
    bh_freq = Column(Integer, nullable=False)
    bh_freq_mb = Column(String, default={})
    active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer)
    
from sqlalchemy import Column, String, Integer, Boolean, Text
from models.base import BaseModel

class BhTaskTypeVsMb(BaseModel):
    __tablename__ = "bh_task_type_vs_mbs"
    
    task_type = Column(String, unique=True, nullable=False)
    desc = Column(Text)
    meas_base = Column(Text, unique=True, nullable=False)
    mb_desc = Column(Text, nullable=False)
    active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer)
    
from sqlalchemy import Column, String, Integer, Boolean
from models.base import BaseModel

class BhTaskTypeVsMb(BaseModel):
    __tablename__ = "bh_task_type_vs_mbs"
    
    task_type_id = Column(Integer, nullable=False)
    meas_base = Column(String, unique=True, nullable=False)
    mb_desc = Column(String, nullable=False)
    active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer)
    
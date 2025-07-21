from sqlalchemy import Column, String, Integer, Boolean
from models.base import BaseModel

class CaTaskCodeVsHgSmrCode(BaseModel):
    __tablename__ = "ca_task_code_vs_hg_smr_codes"
    
    taskcdca = Column(String, unique=True, nullable=False)
    smrcodhg = Column(String, unique=True, nullable=False)
    active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer)
    
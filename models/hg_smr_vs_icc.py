from sqlalchemy import Column, String, Integer, Boolean
from models.base import BaseModel

class HgSmrVsIcc(BaseModel):
    __tablename__ = "hg_smr_vs_iccs"
    
    smrcodhg = Column(String(10), unique=True, nullable=False)
    itmcathg = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer)
    
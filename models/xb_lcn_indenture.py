from sqlalchemy import Column, String, Text, Integer, Boolean
from models.base import BaseModel

class XbLcnIndenture(BaseModel):
    __tablename__ = "xb_lcn_indentures"
    
    lsaconxb_char_length = Column(Integer, nullable=False)
    lcnindxb = Column(String(50), unique=True, nullable=False)
    desc = Column(Text, unique=True)
    active = Column(Boolean, default=True)
    created_by = Column(Integer)
    
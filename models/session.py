from sqlalchemy import Column, String, Text, Integer, JSON, DateTime
from models.base import BaseModel

class Session(BaseModel):
    __tablename__ = "sessions"
    
    id = Column(String(100), primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    ip_address = Column(String(18), nullable=False)
    user_agent = Column(Text, nullable=True)
    payload = Column(JSON, default={})
    expires_at = Column(DateTime, default=True)
    
from sqlalchemy import Column, String, Text, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from models.base import BaseModel

class CaScheduledTask(BaseModel):
    __tablename__ = "ca_scheduled_tasks"
    
    taskcdca_2nd_char = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True, index=True)
    created_by = Column(Integer)
    
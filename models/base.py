from sqlalchemy import Column, Integer, DateTime, event, text
from datetime import datetime
from database.database import Base, engine
import pytz

class BaseModel(Base):
  __abstract__ = True
  
  id = Column(Integer, primary_key=True, index=True)
  created_at = Column(DateTime, default=lambda: datetime.now(pytz.utc))
  updated_at = Column(DateTime, default=lambda: datetime.now(pytz.utc), 
                      onupdate=lambda: datetime.now(pytz.utc))

  @classmethod
  def create(cls, db, **kwargs):
    """Create new record"""
    instance = cls(**kwargs)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance
    
  @classmethod
  def all(cls, db):
    """Get all records"""
    return db.query(cls).all()
  
  @classmethod
  def find(cls, db, id):
    """Find by primary key"""
    return db.query(cls).get(id)
  
  @classmethod
  def where(cls, db, **filters):
    """Filter records"""
    return db.query(cls).filter_by(**filters)
  
  @classmethod
  def first_or_create(cls, db, defaults=None, **kwargs):
    """Find first or create with defaults"""
    instance = db.query(cls).filter_by(**kwargs).first()
    if instance:
      return instance, False
    
    params = {**kwargs, **(defaults or {})}
    instance = cls.create(db, **params)
    return instance, True
  
  def save(self, db):
    """Save changes to the current instance"""
    db.add(self)
    db.commit()
    db.refresh(self)
    return self
  
  def delete(self, db):
    """Delete the current instance"""
    db.delete(self)
    db.commit()
    
  def to_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
@event.listens_for(engine, "connect")
def enable_sqlite_fks(dbapi_connection, connection_record):
  """Enables foreign key constraints for SQLite"""
  if engine.dialect.name == "sqlite":
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
from sqlalchemy import Column, Integer, DateTime, event
from datetime import datetime
from database.database import Base, engine
import pytz
import pandas as pd

class BaseModel(Base):
  __abstract__ = True
  
  id = Column(Integer, primary_key=True, index=True)
  created_at = Column(DateTime, default=lambda: datetime.now(pytz.utc))
  updated_at = Column(DateTime, default=lambda: datetime.now(pytz.utc), 
                      onupdate=lambda: datetime.now(pytz.utc))
  
  _default = {}

  @classmethod
  def create(cls, db, **kwargs):
    """Create new record"""
    merged = {**cls._default, **kwargs}
    instance = cls(**merged)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance
    
  @classmethod
  def all(cls, db, columns=None):
    """Get all records with selected columns"""
    if columns is None:
        columns = [cls]  # Default: All columns
    return db.query(*columns).all()
    
  @classmethod
  def all_df(cls, db, columns=None):
    """
    Fetches all data or selected columns from the database table represented by the SQLAlchemy model cls
    and returns it as a Pandas DataFrame.

    Args:
        db: The SQLAlchemy session object.
        columns (list, optional): A list of column names (strings) or SQLAlchemy instrumented attributes
                                  to select. If None, all columns are selected.

    Returns:
        pd.DataFrame: A Pandas DataFrame containing the fetched data.
                      Returns an empty DataFrame if no data is found or an error occurs (if handled).
    """
    query = db.query(cls)
    if columns:
        # Ensure columns are SQLAlchemy instrumented attributes (not strings)
        column_refs = [getattr(cls, col) if isinstance(col, str) else col for col in columns]
        query = query.with_entities(*column_refs)
    return pd.read_sql(query.statement, db.bind)
  
  @classmethod
  def find(cls, db, id):
    """Find by primary key"""
    return db.query(cls).get(id)
  
  @classmethod
  def where(cls, db, columns=None, **filters):
    """
    Filter records with optional column selection
    
    Args:
        db: SQLAlchemy session
        columns: List of columns to select (None returns full objects)
        filters: Key-value pairs for filtering
    
    Returns:
      SQLAlchemy session
    """
    query = db.query(cls)
    
    if columns:
        if isinstance(columns, str):
            columns = [columns]  # Convert single string to list
        
        selected = [getattr(cls, col) for col in columns]
        query = query.with_entities(*selected)
        
        # Convert to list of dicts
        result = query.filter_by(**filters).all()
        return [dict(zip(columns, row)) for row in result]
    
    # Apply filters if any
    if filters:
        query = query.filter_by(**filters)
        
    return query
  
  @classmethod
  def datatable(cls, db, **filters):
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
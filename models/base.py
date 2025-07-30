from sqlalchemy import Column, Integer, DateTime, event, text
from database.database import Base, engine
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import pytz
import pandas as pd
import json
from typing import List, Union, Optional
from sqlalchemy.orm import Query

class BaseModel(Base):
  __abstract__ = True
  
  id = Column(Integer, primary_key=True, index=True)
  created_at = Column(DateTime, default=lambda: datetime.now(pytz.utc))
  updated_at = Column(DateTime, default=lambda: datetime.now(pytz.utc), 
                      onupdate=lambda: datetime.now(pytz.utc))
  
  _default = {}
  
  @classmethod
  def truncate(cls, db, restart_identity=True, cascade=False):
    """
    Truncate the table (delete all records) with database-specific optimizations.
    
    Args:
        db: SQLAlchemy session
        restart_identity: Reset auto-increment counters (where supported)
        cascade: Include referenced tables (where supported)
    """
    table_name = cls.__tablename__
    
    try:
      db.execute(text(f'DELETE FROM {table_name}'))
      if restart_identity:
        db.execute(text(f'DELETE FROM sqlite_sequence WHERE name="{table_name}"'))
      db.commit()
      return True
    except Exception as e:
      db.rollback()
      raise Exception(f"Truncate failed: {str(e)}")

  @classmethod
  def clear_all(cls, db):
    """
    Safe alternative to truncate that works across all databases.
    Uses delete() but performs in batches for large tables.
    """
    try:
      # First try the optimized truncate
      return cls.truncate(db)
    except:
      # Fallback to batch deletion if truncate fails
      try:
        while db.query(cls).count() > 0:
            db.query(cls).limit(10000).delete(synchronize_session=False)
            db.commit()
        return True
      except Exception as e:
        db.rollback()
        raise Exception(f"Failed to clear table: {str(e)}")


  @classmethod
  def create(cls, db, **kwargs):
    """Create new record"""
    table_columns = {column.name for column in cls.__table__.columns}
        
    # Filter kwargs to only include existing columns
    filtered_kwargs = {
        key: value 
        for key, value in {**cls._default, **kwargs}.items()
        if key in table_columns
    }
    
    instance = cls(**filtered_kwargs)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance
    
  class BaseModel(Base):
    __abstract__ = True
    
    # ... (your existing columns and methods)
    
  @classmethod
  def all(
      cls,
      db,
      columns: Optional[Union[str, List[str]]] = None,
      as_dict: bool = False,
      chunk_size: Optional[int] = None
  ) -> Union[List['BaseModel'], List[dict]]:
    """
    Get all records with flexible return formats.
    
    Args:
        db: SQLAlchemy session
        columns: Either:
            - None (get all columns)
            - String of comma-separated column names ('id,name')
            - List of column names (['id', 'name'])
        as_dict: If True, returns dictionaries instead of model instances
        chunk_size: If specified, yields chunks of records
        
    Returns:
        List of model instances, dictionaries, or chunks based on parameters
    """
    # Prepare the base query
    query = db.query(cls)
    
    # Handle column selection
    selected_columns = None
    if columns is not None:
        if isinstance(columns, str):
            columns = [col.strip() for col in columns.split(',') if col.strip()]
        
        # Validate columns and get SQLAlchemy column objects
        selected_columns = []
        for col_name in columns:
            if not hasattr(cls, col_name):
                raise AttributeError(f"Column '{col_name}' doesn't exist on {cls.__name__}")
            selected_columns.append(getattr(cls, col_name))
        
        query = query.with_entities(*selected_columns)
    
    # Handle chunking
    if chunk_size:
        return cls._yield_in_chunks(query, chunk_size, as_dict, selected_columns)
    
    # Execute query and format results
    results = query.all()
    
    if as_dict or selected_columns is not None:
        column_names = columns if columns else [col.name for col in cls.__table__.columns]
        return [cls._row_to_dict(row, column_names) for row in results]
    
    return results

  @classmethod
  def _yield_in_chunks(
      cls, 
      query: Query, 
      chunk_size: int, 
      as_dict: bool,
      selected_columns: Optional[List] = None
  ):
      """Yield results in chunks for memory efficiency"""
      offset = 0
      column_names = None
      
      if as_dict:
          column_names = (
              [col.name for col in cls.__table__.columns] 
              if selected_columns is None
              else [col.key for col in selected_columns]
          )
      
      while True:
          chunk = query.offset(offset).limit(chunk_size).all()
          if not chunk:
              break
          
          if as_dict:
              yield [cls._row_to_dict(row, column_names) for row in chunk]
          else:
              yield chunk
          
          offset += chunk_size

  @staticmethod
  def _row_to_dict(row, column_names: List[str]) -> dict:
      """Convert a row result to dictionary"""
      if hasattr(row, '_asdict'):  # Handle model instances
          return row._asdict()
      return dict(zip(column_names, row))  # Handle tuple results


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
  def first_or_create(cls, db, find_by: str = "id", defaults: dict = None, **kwargs):
    """
    Find first record matching criteria or create new record.
    
    Args:
      db: Database session
      find_by: Column name to use as unique finder (e.g., 'code')
      defaults: Default values for creation if record doesn't exist
      **kwargs: Filter conditions
        
    Returns:
      tuple: (instance, created) where created is boolean indicating if new record was created
        instance, created = Model.first_or_create(
          db,
          code="ABC123",
          name="Test Item",
          defaults={"active": True}
        )
    Example:

    """
    # If find_by specified, use just that column for lookup
    if find_by and find_by in kwargs:
        lookup = {find_by: kwargs[find_by]}
        instance = db.query(cls).filter_by(**lookup).first()
    else:
        # Otherwise use all kwargs for lookup
        instance = db.query(cls).filter_by(**kwargs).first()
    
    if instance:
        return instance, False
    
    try:
        # Combine kwargs and defaults for creation
        params = {**kwargs, **(defaults or {})}
        instance = cls.create(db, **params)
        db.commit()
        return instance, True
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Creation failed due to integrity error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise Exception(f"Error in first_or_create: {str(e)}")  

  def clone(self, db, attr=None, key="id"):
    """
    Create a clone of the current instance with modified attributes.
    
    Args:
        db: SQLAlchemy session
        attr: Dictionary of attributes to modify in the clone
        key: Attribute name to exclude from cloning (default is "id")
    
    Returns:
        Cloned instance
        
    Example:
      original = SomeModel.find(db, 1)
      clone = original.clone(db, attr={'name': 'New Name'})
    """
    if attr is None: attr = {}
    
    # Get all column names except the key attribute
    # Create dictionary of current attributes
    # Update with any modified attributes
    # Create and return new instance
    columns = [c.name for c in self.__table__.columns if c.name != key]
    values = {column: getattr(self, column) for column in columns}
    values.update(attr)
    return self.__class__.create(db, **values)
  
  @classmethod
  def update(cls, db, id, updates):
    """
    Update a record by ID with the provided attributes object
    
    Args:
        db: SQLAlchemy session
        id: Primary key of the record to update
        updates: Dictionary/object of attributes to update
        
    Returns:
        Updated instance or None if not found
        
    Example:
        updates = {
            'name': 'New Name',
            'config': {'key': 'value'},  # SQLAlchemy will handle JSON conversion
            'tags': [1, 2, 3]           # SQLAlchemy will handle JSON conversion
        }
        updated = SomeModel.update(db, 1, updates)
    """
    instance = db.query(cls).get(id)
    if not instance:
      return None
    
    table_columns = {column.name for column in cls.__table__.columns}
        
    for key, value in updates.items():
      if key.startswith('_') or key not in table_columns or key == 'id':
          continue
            
      setattr(instance, key, value)
        
    instance.updated_at = datetime.now(pytz.utc)
    db.commit()
    db.refresh(instance)
    return instance
  
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
    
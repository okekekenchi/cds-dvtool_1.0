from database.database import engine
from sqlalchemy import inspect, text
import pandas as pd
from typing import Optional, Dict, Any
import streamlit as st
from models.base import BaseModel
from typing import List, Optional, Union
from utils import system_tables

@st.cache_data
def get_table_names() -> list:
    """Get list of table names in the database"""
    inspector = inspect(engine)
    return [ name for name in inspector.get_table_names() if name not in system_tables]

def get_table_data(
      table_name: str,
      search_term: str = "",
      columns: Optional[Union[str, List[str]]] = None,
      limit: Optional[int] = None,
      **filters
  ) -> pd.DataFrame:
  """
  Get data from a table with optional search and column selection
  
  Args:
      table_name: Name of the table to query
      search_term: Optional term to search across all string columns
      columns: Optional list of columns to select (None for all columns)
      limit: Optional maximum number of rows to return
      
  Returns:
      DataFrame containing the query results
  """
  inspector = inspect(engine)
  if table_name not in inspector.get_table_names():
      raise ValueError(f"Table '{table_name}' does not exist")
  
  if columns:
    if isinstance(columns, str):
      columns = [columns]
    
    # Validate columns exist in table
    table_columns = [col['name'] for col in inspector.get_columns(table_name)]
    invalid_cols = set(columns) - set(table_columns)
    if invalid_cols:
      raise ValueError(f"Invalid columns: {invalid_cols}")
    
    col_list = ", ".join([f'"{col}"' for col in columns])
  else:
    col_list = "*"
      
  query = f'SELECT {col_list} FROM "{table_name}"'
  conditions = []
  params = {}
  
  # Add search term
  if search_term:
    search_conditions = []
    for col in inspector.get_columns(table_name):
      if col['type'].python_type == str:
        search_conditions.append(f'"{col["name"]}" LIKE :search_term')
    if search_conditions:
      conditions.append("(" + " OR ".join(search_conditions) + ")")
      params['search_term'] = f'%{search_term}%'
  
  # Add all filters
  for col, value in filters.items():
    col_exists = any(c['name'] == col for c in inspector.get_columns(table_name))
    if not col_exists:
      continue
        
    if value is None:
      conditions.append(f'"{col}" IS NULL')
    else:
      conditions.append(f'"{col}" = :{col}')
      params[col] = value
  
  # Combine conditions
  if conditions:
    query += " WHERE " + " AND ".join(conditions)
  
  if limit:
    query += f" LIMIT {limit}"
  
  # Execute query
  with engine.connect() as conn:
    return pd.read_sql(text(query), conn, params=params)
  
@st.cache_data
def get_table_columns(table_name: str) -> list:  
    """
    Get column names a table.

    Args:
        table_name: The name of the table.

    Returns:
        A list of string names.
        Example: ['name', 'type'] 
    """
    inspector = inspect(engine)
    return [col['name'] for col in inspector.get_columns(table_name)]

def delete_record(table_name: str, record_id: int, id_column: str = "id") -> None:
    """Delete a record from a table"""
    with engine.connect() as conn:
        conn.execute(text(f"DELETE FROM {table_name} WHERE {id_column} = :id"), {"id": record_id})
        conn.commit()

# def update_record(table_name: str, record_id: int, data: Dict[str, Any], id_column: str = "id") -> None:
#     """Update a record in a table"""
#     set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
#     params = data.copy()
#     params["id"] = record_id
#     with engine.connect() as conn:
#         conn.execute(
#             text(f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = :id"),
#             params
#         )
#         conn.commit()

# def create_record(table_name: str, data: Dict[str, Any]) -> None:
#     """Create a new record in a table"""
#     columns = ", ".join(data.keys())
#     placeholders = ", ".join([f":{k}" for k in data.keys()])
#     with engine.connect() as conn:
#         conn.execute(
#             text(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"),
#             data
#         )
#         conn.commit()
        
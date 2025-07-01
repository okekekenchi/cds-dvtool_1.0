# -*- coding: utf-8 -*-
"""
Created on Sat Jun 21 02:57:44 2025

@author: Kenneth Okeke
@email: okekekenchi0802@gmail.com
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os
from loader.config_loader import config

# Configure SQLite database path (in Streamlit's preferred location)
DB_PATH = os.path.join(os.getcwd(), config('database.name'))
DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLite-specific engine configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo= True if config('app.debug') else False  # Set to True for debugging
    # pool_size=5,
    # max_overflow=10,
    # pool_recycle=3600
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

@contextmanager
def get_db():
    """Provide a database session that automatically handles commits and rollbacks"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
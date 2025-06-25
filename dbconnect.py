# -*- coding: utf-8 -*-
"""
Created on Sat Jun 21 02:57:44 2025

@author: Kenneth Okeke
@email: okekekenchi0802@gmail.com
"""

import sqlite3
import config
import dbquery


# Database setup
def init_db():
    conn = set_connection()
    c = conn.cursor()
    
    # Create users table if not exists
    c.execute(dbquery.create_user())
    
    close_connection(conn)


# Database setup
def clear_db():
    conn = set_connection()
    c = conn.cursor()
    
    # Create users, and session tables if not exists
    c.execute(dbquery.truncate("users"))
    c.execute(dbquery.truncate("sessions"))
    
    close_connection(conn)
    
    
# Establish connection
def set_connection():
    return sqlite3.connect(config.DATABASE_NAME)

# Close connection
def close_connection(connection):
    connection.commit()
    connection.close()

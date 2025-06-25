# -*- coding: utf-8 -*-
"""
Created on Sat Jun 21 04:32:56 2025

@author: Okeke Kenneth
@email: okekeknchi0802@gmail.com
"""

def create_user():
    return '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
                 

def create_session():
    return '''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            ip_address TEXT NOT NULL,
            user_agent TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            session_token TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id))
    '''
    

def clear_expired_session():
    return "DELETE FROM sessions WHERE expires_at < datetime('now')"

def truncate(table:str):
    """
    Clear table records

    Parameters
    ----------
    table: String.

    Returns
    -------
    TYPE: NONE.
    """
    return "DELETE FROM " + table
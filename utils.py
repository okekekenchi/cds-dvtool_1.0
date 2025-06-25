import sqlite3
import bcrypt
import secrets
import time
import streamlit as st
from functools import wraps
from datetime import datetime, timedelta
import config
import dbquery

def get_active_session(request):
    """Get session from browser cookie AND verify against database"""
    from streamlit.web.server.websocket_headers import _get_websocket_headers
    
    try:
        headers = _get_websocket_headers()
        cookies = headers.get("Cookie", "")
        
        # Extract session cookie
        session_cookie = next(
            (c.split("=")[1] for c in cookies.split("; ") 
             if c.startswith("_streamlit_session_id=")),
            None
        )
        
        if session_cookie:
            conn = sqlite3.connect(config.DATABASE_NAME)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.id, u.email, u.full_name 
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_id = ? AND s.expires_at > datetime('now')
            ''', (session_cookie,))
            return cursor.fetchone()
    except:
        return None

# Setup sessions
def init_sessions():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state['page'] = 'login'
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
        
def set_session_state(user, session_id=None):
    st.session_state.update({
        'authenticated': True,
        'user_id': user[0],
        'user_email': user[1],
        'user_name': user[2],
        'session_id': session_id or headers["Cookie"].split("_streamlit_session_id=")[1].split(";")[0]
    })
        
# Database initialization
def init_db():
    conn = sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(dbquery.create_user())
    cursor.execute(dbquery.create_session())
    cursor.execute(dbquery.clear_expired_session())
    
    conn.commit()
    conn.close()

# Session management
def create_session(user_id):
    conn = sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)
    cursor = conn.cursor()
    
    # Generate secure session token
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=12)
    
    cursor.execute(
        "INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)",
        (session_id, user_id, expires_at)
    )
    conn.commit()
    conn.close()
    return session_id

# Session management
def clear_db():
    conn = sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("DELETE TABLE users")
    cursor.execute("DELETE TABLE session")
    
    conn.commit()
    conn.close()

def valid_session(session_id):
    """Check if user session is valid"""
    if not session_id:
        return None
    
    conn = sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.email, u.full_name 
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.session_id = ? AND s.expires_at > datetime('now')
    ''', (session_id,))
    
    user = cursor.fetchone()
    conn.close()
    return user

def delete_session(session_id):
    conn = sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

# Password hashing
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# User management
def create_user(full_name, email, password):
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)',
                       (full_name, email, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()        

def get_user(email):
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

# Authentication decorator
def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session_id = st.session_state.get('session_id')
        user = valid_session(session_id) if session_id else None
        
        if not user:
            st.session_state.clear()
            st.warning("Please login to access this page.")
            st.switch_page("pages/1_login.py")
            return
        
        # Update session in state
        st.session_state.user_id = user[0]
        st.session_state.user_email = user[1]
        st.session_state.user_name = user[2]
        st.session_state.authenticated = True
        
        return func(*args, **kwargs)
    return wrapper

# Password strength check
def is_password_strong(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    return True, "Password is strong"

# Set page configuration
def set_page_config():
    st.set_page_config(
        # page_title= st.session_state['page_title'],
        page_icon="🔐",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
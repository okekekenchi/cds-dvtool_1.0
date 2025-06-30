import sqlite3
import bcrypt
import time
import streamlit as st
from functools import wraps
import config
import dbquery
from SessionManager import SessionManager
from streamlit_cookies_manager import EncryptedCookieManager
import uuid

def init_session_cookie():
    st.session_state.current_page = None
    sessions = SessionManager()
    cookies = EncryptedCookieManager(
        prefix = "cds_", 
        password = "38#$@__!@#$%^&*()_81~!!@",
    )
    
    if not cookies.ready():
        st.markdown(
            "<h5 style='text-align:center;'>🔄 Loading, please wait...</h5>",
            unsafe_allow_html=True
        )
        st.rerun()
    
    return sessions, cookies

def hide_nav_and_header():
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] {
            display: none !important;
            }
            
            .stAppHeader {
            display: none !important;
            }
        
            header[data-testid="stHeader"] {
                display: none !important;
            }
            footer {
                visibility: hidden;
            }
        </style>
    """, unsafe_allow_html=True)
        
# Database initialization
def init_db():
    conn = sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute(dbquery.create_user())
    cursor.execute(dbquery.clear_expired_session())
    
    conn.commit()
    conn.close()

# Session management
def clear_db():
    conn = sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("DELETE TABLE users")
    cursor.execute("DELETE TABLE session")
    
    conn.commit()
    conn.close()

def delete_db_sessions(cookies=None):
    if cookies:
        session_id = cookies.get('session_id')
    else:
        session_id = st.session_state.session_id
    
    if (session_id):
        conn = sqlite3.connect(config.DATABASE_NAME, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()

def logout(cookies=None, redirect=True):
    delete_db_sessions(cookies)
    st.session_state.clear()
    clear_cookies(cookies)
    
    time.sleep(0.5)
    if redirect:
        st.switch_page(config.ROUTE_LOGIN)

def login(email, password):
    user = get_user_by_email(email)
    
    if user and verify_password(password, user[3]):
        sessions = SessionManager()

        if sessions.auth_session(st.session_state.session_id, user[0]):
            return True
            
    return False
    
def clear_cookies(cookies: EncryptedCookieManager):
    if cookies:
        cookies.pop("session_id", None)
        cookies.save()

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

def get_user_by_email(email):
    """Gets user by email ID"""
    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def email_exists(email):
    """Gets user by email ID"""

    conn = sqlite3.connect(config.DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return True if user else False

def handle_session(user_id=None, forrce_new=False):
    """Returns the session of the cuurent user"""
    sessions, cookies = init_session_cookie()
    set_session_cookie(sessions=sessions, cookies=cookies, user_id=user_id, force_new_cookie=forrce_new)
    session = sessions.get_session(cookies.get('session_id'))
    
    if not session: # session exists in browser but not in DB
        set_session_cookie(sessions=sessions, cookies=cookies, force_new_cookie=True)
        session = sessions.get_session(cookies.get('session_id'))
        
    st.session_state.session_id = session['session_id']
    
    return session

def auth():
    """Checks if the user is authenticated"""
    session = handle_session()
    return True if session and session['user_id'] else False

# Authentication decorator
def authenticated(func):
    """Ensure that only authenticated users are allowed access to a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not auth(): # the browser's session is valid and the user is authenticated
            st.switch_page(config.ROUTE_LOGIN)
            return
        
        return func(*args, **kwargs)
    return wrapper

# Guest decorator
def guest(func):
    """Ensure that only unauthenticated users are allowed access to a function. (Login, register pages)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if auth(): # the browser's session is valid and the user is authenticated
            st.switch_page(st.session_state.current_page or config.ROUTE_HOME)
            return
        return func(*args, **kwargs)
    return wrapper

def set_session_cookie(sessions: SessionManager, cookies: EncryptedCookieManager, user_id=None, force_new_cookie=True):
  """Creates a new session if already not existing"""
  if not cookies.get('session_id') or force_new_cookie:
    session_id = sessions.create_session(user_id=user_id, payload={})
    session = sessions.get_session(session_id)
    
    if session:
        cookies['session_id'] = session_id
        cookies.save()
        time.sleep(0.3)  # Without delay, the cookie is not saved

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

import time
import sqlite3
import bcrypt
import time
import streamlit as st
from functools import wraps
from database.database import get_db
from models.user import User
from SessionManager import SessionManager
from streamlit_cookies_manager import EncryptedCookieManager
from loader.config_loader import config


def init_session_cookie():
    st.session_state.current_page = None
    cookies = EncryptedCookieManager(
        prefix = "cds_", 
        password = "38#$@__!@#$%^&*()_81~!!@",
    )
    time.sleep(2)
    
    if not cookies.ready():
        time.sleep(5)
        st.rerun()
    
    return cookies

def logout(cookies=None):
    sessions = SessionManager()
    sessions.delete_session(st.session_state.session_id)
    st.session_state.clear()
    
    clear_cookies(cookies)
    time.sleep(0.5)

def login(email, password):
    with get_db() as db:
        user = User.findByEmail(db, email)
    
    if user and verify_password(password, user.password):
        sessions = SessionManager()
        if sessions.auth_session(st.session_state.session_id, user.id):
            st.session_state.user_id = user.id
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
    with get_db() as db:
        # Create a user
        new_user = User.create(
            db,
            full_name=full_name,
            email=email,
            password=hash_password(password)
        )
    return new_user

def get_user_by_id(id):
    """Gets user by ID"""
    with get_db() as db:
        return User.find(db, id)

def email_exists(email):
    """Gets user by email ID"""

    conn = sqlite3.connect(config('database.name'))
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return True if user else False

def handle_session(user_id=None, forrce_new=False):
    """Returns the session of the curent user"""
    sessions = SessionManager()
    if 'session_id' not in st.session_state: # fresh page load
        cookies = init_session_cookie()
        session = set_session_cookie(sessions=sessions, cookies=cookies,
                                     user_id=user_id, force_new_cookie=forrce_new)
    else:
        session = sessions.get_session(st.session_state.session_id)
    
    if not session: # session exists in browser but not in DB
        session = set_session_cookie(sessions=sessions, cookies=cookies, force_new_cookie=True)
        
    return session

def auth():
    """Checks if the user is authenticated"""
    if 'user_id' in st.session_state and st.session_state.user_id:
        return True
    
    session = handle_session()
    return True if session and session['user_id'] else False

# Authentication decorator
def authenticated(func):
    """Ensure that only authenticated users are allowed access to a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not auth(): # the browser's session is valid and the user is authenticated
            st.switch_page(config('route.login'))
            return
        
        return func(*args, **kwargs)
    return wrapper

# Guest decorator
def guest(func):
    """Ensure that only unauthenticated users are allowed access to a function. (Login, register pages)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if auth(): # the browser's session is valid and the user is authenticated
            st.switch_page(st.session_state.current_page or config('route.home'))
            return
        return func(*args, **kwargs)
    return wrapper

def set_session_cookie(sessions: SessionManager, cookies: EncryptedCookieManager, user_id=None, force_new_cookie=True):
    """Creates a new session if already not existing"""
    session_id = cookies.get('session_id')
    if not cookies.get('session_id') or force_new_cookie:
        session_id = sessions.create_session(user_id=user_id)
        
    session = sessions.get_session(session_id)
    
    if session:
        st.session_state.session_id = session['id']
        st.session_state.user_id = session['user_id']
        cookies['session_id'] = session_id
        cookies.save()
        time.sleep(0.3)  # Without delay, the cookie is not saved
    
    return session

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

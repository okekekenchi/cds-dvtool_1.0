import sqlite3
import config
import dbquery
import sqlite3
import bcrypt
from datetime import datetime, timedelta
import streamlit as st
import uuid

class SessionManager:
    def __init__(self, db_name=config.DATABASE_NAME, bcrypt_rounds=12):
        self.db_name = db_name
        self.bcrypt_rounds = bcrypt_rounds
        self._initialize_db()
        
    def _initialize_db(self):
        """Initialize the database with the sessions table"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(dbquery.create_session())
            conn.commit()

    def _generate_session_token(self):
        """Generate a secure session token using bcrypt"""
        raw_token = bcrypt.gensalt(self.bcrypt_rounds)
        return bcrypt.hashpw(raw_token, bcrypt.gensalt(self.bcrypt_rounds)).decode('utf-8')

    def _verify_session_token(self, session_id):
        """Verify a session token"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_token FROM sessions 
                WHERE session_id = ? AND expires_at > datetime('now')
            ''', (session_id,))
            result = cursor.fetchone()
            
            return True if result else False
    
    def _get_client_info(self):
        """Get client IP and user agent from request headers"""
        try:
            ctx = st.runtime.get_instance().script_run_ctx
            if ctx and hasattr(ctx, 'request'):
                headers = ctx.request.headers
                ip_address = headers.get('X-Forwarded-For', headers.get('X-Real-Ip', '127.0.0.1'))
                user_agent = headers.get('User-Agent', 'Unknown')
                return ip_address.split(',')[0].strip(), user_agent
        except Exception:
            pass
        return '127.0.0.1', 'Unknown'

    def create_session(self, user_id=None, ip_address=None, user_agent=None,
                       payload=None, lifetime_minutes=config.SESSION_LIFETIME):
        """Create a new session with bcrypt-secured token"""
        session_id = str(uuid.uuid4())
        session_token = self._generate_session_token()
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=lifetime_minutes)
        
        if payload is None:
            payload = {}
            
        if ip_address is None or user_agent is None:
            client_ip, client_ua = self._get_client_info()
            ip_address = ip_address or client_ip
            user_agent = user_agent or client_ua
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions 
                (session_id, user_id, ip_address, user_agent, payload, created_at, expires_at, session_token)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, ip_address, user_agent, str(payload), created_at, expires_at, session_token))
            conn.commit()
            
        return session_id

    def get_session(self, session_id):
        """Retrieve a session by ID with token verification"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sessions 
                WHERE session_id = ? AND expires_at > datetime('now')
            ''', (session_id,))
            result = cursor.fetchone()
            
            return dict(result) if result else None

    def update_session(self, session_id, user_id=None, payload=None, extend_lifetime=False, lifetime_minutes=None):
        """Update an existing session with token verification"""
        if not self._verify_session_token(session_id):
            return False
            
        updates = []
        params = []
        
        if payload is not None:
            updates.append("payload = ?")
            params.append(str(payload))
            
        if extend_lifetime or lifetime_minutes is not None:
            if lifetime_minutes is None:
                lifetime_minutes = 120
            new_expiry = datetime.now() + timedelta(minutes=lifetime_minutes)
            updates.append("expires_at = ?")
            params.append(new_expiry)
            
        if not updates:
            return False
            
        params.append(session_id)
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE sessions 
                SET {', '.join(updates)} 
                WHERE session_id = ?
            ''', params)
            conn.commit()
            return cursor.rowcount > 0
    
    def auth_session(self, session_id, user_id=None):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE sessions 
                SET user_id = ?
                WHERE session_id = ?
            ''', (user_id, session_id))
            conn.commit()
            return cursor.rowcount > 0
        
    def delete_session(self, session_id):
        if session_id:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
                conn.commit()
                return cursor.rowcount > 0
            
        st.session_state.clear()

    def garbage_collect(self):
        """Clean up expired sessions"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
            conn.commit()
            return cursor.rowcount


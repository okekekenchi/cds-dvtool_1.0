import sqlite3
import sqlite3
from datetime import datetime, timedelta
import streamlit as st
import uuid
from loader.config_loader import config
from database.database import get_db
from models.session import Session

class SessionManager:
    def __init__(self, db_name=config('database.name'), bcrypt_rounds=12):
        self.db_name = db_name
        self.bcrypt_rounds = bcrypt_rounds
        self._clear_expired_sessions()
        
    def _clear_expired_sessions(self):
        """Initialize the database with the sessions table"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
            conn.commit()
    
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
                       payload={}, lifetime_minutes=config('session.lifetime')):
        """Create a new session"""
        if ip_address is None or user_agent is None:
            client_ip, client_ua = self._get_client_info()
            ip_address = ip_address or client_ip
            user_agent = user_agent or client_ua
        
        session = None
        with get_db() as db:
            session = Session.create(
                db,
                id=str(uuid.uuid4()),
                payload=payload,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.now() + timedelta(minutes=lifetime_minutes)
            )
            
        return session.id if session else None

    def get_session(self, session_id):
        """Retrieve a session by ID"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sessions 
                WHERE id = ? AND expires_at > datetime('now')
            ''', (session_id,))
            result = cursor.fetchone()
            
            return dict(result) if result else None
    
    def auth_session(self, session_id, user_id=None):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE sessions 
                SET user_id = ?
                WHERE id = ?
            ''', (user_id, session_id))
            conn.commit()
            return cursor.rowcount > 0
        
    def delete_session(self, session_id):
        if session_id:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
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


import sqlite3
import config
import dbquery
import utils
import sqlite3
import bcrypt
from datetime import datetime, timedelta
import streamlit as st
from user_agents import parse
import urllib.parse
import socket

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

    def _verify_session_token(self, session_id, token_to_verify):
        """Verify a session token"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT session_token FROM sessions 
                WHERE session_id = ? AND expires_at > datetime('now')
            ''', (session_id,))
            result = cursor.fetchone()
            
            if result:
                stored_token = result[0].encode('utf-8')
                return bcrypt.checkpw(token_to_verify.encode('utf-8'), stored_token)
            return False
    
    def _get_client_info(self):
        """Get client IP and user agent from request headers"""
        
        try:
            ctx = st.runtime.get_instance().script_run_ctx
            if ctx and hasattr(ctx, 'request'):
                headers = ctx.request.headers
                user_agent = headers.get('User-Agent', 'Unknown')
                ip_address = socket.gethostbyname(socket.gethostname())
                return ip_address, user_agent
        except Exception:
            pass
        return '127.0.0.1', 'Unknown'

    def create_session(self, user_id=None, ip_address=None, user_agent=None,
                       payload=None, lifetime_minutes=config.SESSION_LIFETIME):
        """Create a new session with bcrypt-secured token"""
        session_id = bcrypt.gensalt(self.bcrypt_rounds).decode('utf-8')[:64]
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

    def get_session(self, session_id, token_to_verify=None):
        """Retrieve a session by ID with token verification"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if token_to_verify:
                if not self._verify_session_token(session_id, token_to_verify):
                    return None
            
            cursor.execute('''
                SELECT * FROM sessions 
                WHERE session_id = ? AND expires_at > datetime('now')
            ''', (session_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None

    def update_session(self, session_id, payload=None, extend_lifetime=False, lifetime_minutes=None, token_to_verify=None):
        """Update an existing session with token verification"""
        if token_to_verify and not self._verify_session_token(session_id, token_to_verify):
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

    def delete_session(self, session_id, token_to_verify=None):
        """Delete a session with token verification"""
        if token_to_verify and not self._verify_session_token(session_id, token_to_verify):
            return False
            
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            conn.commit()
            return cursor.rowcount > 0

    def garbage_collect(self):
        """Clean up expired sessions"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
            conn.commit()
            return cursor.rowcount



# Example usage in Streamlit with token management
def main():
    session_manager = SessionManager()
    
    # Initialize session token in state if not exists
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None
    
    # Check for existing session
    if 'session_id' in st.session_state:
        session = session_manager.get_session(
            st.session_state.session_id,
            st.session_state.session_token
        )
        
        if session:
            st.success(f"Existing session loaded: {st.session_state.session_id}")
            st.json({k: v for k, v in session.items() if k != 'session_token'})
        else:
            st.warning("Session expired or invalid")
            del st.session_state.session_id
            del st.session_state.session_token
            st.rerun()
    else:
        # Create new session
        user_agent = parse(st.experimental_get_query_params().get('user_agent', [''])[0])
        session_id = session_manager.create_session(
            user_id=None,
            ip_address=st.experimental_get_query_params().get('ip', [''])[0],
            user_agent=str(user_agent),
            payload={'theme': 'dark', 'preferences': {}},
            lifetime_minutes=120
        )
        
        # Store both session ID and token
        session = session_manager.get_session(session_id)
        if session:
            st.session_state.session_id = session_id
            st.session_state.session_token = session['session_token']
            st.success(f"New session created: {session_id}")
    
    # Session management UI
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Extend Session"):
            if session_manager.update_session(
                st.session_state.session_id,
                extend_lifetime=True,
                token_to_verify=st.session_state.session_token
            ):
                st.success("Session extended by 120 minutes")
    
    with col2:
        if st.button("Logout"):
            session_manager.delete_session(
                st.session_state.session_id,
                st.session_state.session_token
            )
            del st.session_state.session_id
            del st.session_state.session_token
            st.rerun()

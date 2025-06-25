import streamlit as st
from utils import init_db, clear_db, valid_session, get_active_session, init_sessions, set_session_state
from SessionManager import SessionManager


"""
  In your deployment (e.g., Nginx config)
  add_header Set-Cookie "_streamlit_session_id=$SESSION_ID; Path=/; HttpOnly; Secure; SameSite=Lax";
"""

# Initialize database
init_db()

# Main app
def main():
	# clear_db()
	
	# Check for existing valid session
	session_id = st.session_state.get('session_id')
	# user = valid_session(session_id) if session_id else None
	
	user = get_active_session(st.request)

	if user:
		set_session_state(user)
	else:
		init_sessions()
			
	st.markdown("""
		<style>
			section[data-testid="stSidebar"] {
				display: none !important;
			}
		</style>
	""", unsafe_allow_html=True)
	
	st.set_page_config(initial_sidebar_state="collapsed")
	
	if 'authenticated' not in st.session_state:
		st.session_state.authenticated = False
	
	if st.session_state.authenticated:
		st.sidebar.title("Navigation")
		st.sidebar.success(f"Logged in as {st.session_state.user_email}")
		if st.sidebar.button("Logout"):
			st.session_state.clear()
			st.rerun()
	else:
		# Redirect to login page if not authenticated
		if st.query_params.get('page') != 'login':
			st.switch_page("pages/1_login.py")
			st.rerun()

if __name__ == "__main__":
	# Additional session validation on page load
	# if 'session_id' not in st.session_state or not valid_session(st.session_state.session_id):
	# 	st.session_state.clear()
	# 	st.switch_page("pages/1_login.py")
	# else:
	# 	main()
 
 
	session_manager = SessionManager()

	# Initialize session token in state if not exists
	init_sessions()

	st.write(session_manager._get_client_info())
    
	
	# Check for existing session
	if st.session_state.session_id:
		session = session_manager.get_session(
			st.session_state.session_id,
			st.session_state.session_token
		)
        
		if session:
			st.success(f"Existing session loaded: {st.session_state.session_id}")
			st.json({k: v for k, v in session.items() if k != 'session_token'})
			
			# Display session info
			with st.expander("Session Details"):
				st.write(f"IP Address: {session['ip_address']}")
				st.write(f"User Agent: {session['user_agent']}")
				st.write(f"Created At: {session['created_at']}")
				st.write(f"Expires At: {session['expires_at']}")
		else:
			st.warning("Session expired or invalid")
			del st.session_state.session_id
			del st.session_state.session_token
			st.rerun()
	else:
		# Create new session
		session_id = session_manager.create_session(
			user_id=None,
			payload={'theme': 'dark', 'preferences': {}}
		)
		
		# Store both session ID and token
		session = session_manager.get_session(session_id)
		if session:
			st.session_state.session_id = session_id
			st.session_state.session_token = session['session_token']
			st.success(f"New session created: {session_id}")
			st.success(f"Session token: {session['session_token']}")
			# st.rerun()
    
    # Session management UI
	st.divider()
	col1, col2 = st.columns(2)

	with col1:
		if st.button("Extend Session"):
			if session_manager.update_session(
				st.session_state.session_id,
				extend_lifetime=True,
				token_to_verify=st.session_state.session_token
			):
				st.success("Session extended by 120 minutes")
				st.rerun()
    
	with col2:
		if st.button("Logout"):
			session_manager.delete_session(
				st.session_state.session_id,
				st.session_state.session_token
			)
			del st.session_state.session_id
			del st.session_state.session_token
			st.success("Logged out successfully")
			st.rerun()
		
		
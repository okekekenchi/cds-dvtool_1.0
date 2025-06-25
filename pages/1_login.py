import streamlit as st
from utils import get_user, verify_password, create_session, valid_session, set_session_state

# Apply CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Force hide sidebar
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Page config
st.set_page_config(page_title="Login", page_icon="🔒", layout="centered", initial_sidebar_state="collapsed")

# Check for existing valid session
if 'session_id' in st.session_state:
    user = valid_session(st.session_state.session_id)
    if user:
        set_session_state(user)
        st.switch_page("pages/3_home.py")
        
# Login form container
with st.container():
    st.title("Login")
    st.markdown('<div class="container">', unsafe_allow_html=True)

    # Form inputs
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    login_button = st.button("Login", type="primary", use_container_width=True)

    # Login logic
    if login_button:
        if not email or not password:
            st.error("Please fill in all fields")
        else:
            user = get_user(email)
            if user and verify_password(password, user[3]):
                # Create new session
                session_id = create_session(user[0])
                
                # Set browser cookie
                st.query_params.session_id = session_id
                
                # Update session state
                set_session_state(user, session_id)
                st.switch_page("pages/3_home.py")
            else:
                st.error("Invalid email or password")

    # Registration link
    st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            Don't have an account? <a href="/register" target="_self">Register here</a>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    

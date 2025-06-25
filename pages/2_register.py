import streamlit as st
from utils import create_user, is_password_strong, get_user
import re

# Apply CSS styling
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Hide sidebar completely for registration page
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="Register",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Check if already logged in
if st.session_state.get('authenticated', False):
    st.switch_page("pages/3_home.py")

# Registration form container
with st.container():
    st.title("Create Account")
    st.markdown('<div style="width:400px; max-width:400px; min-width:400px;">', unsafe_allow_html=True)

    # Form inputs
    with st.form("registration_form"):
        full_name = st.text_input("Full Name", placeholder="John Doe")
        email = st.text_input("Email", placeholder="example@domain.com")
        password = st.text_input("Password", type="password", placeholder="********",
                               help="At least 8 characters with 1 number, 1 uppercase, and 1 lowercase")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="********")
        
        submitted = st.form_submit_button("Register", type="primary")

    # Registration logic
    if submitted:
        # Client-side validation
        errors = []
        
        if not full_name.strip():
            errors.append("Full name is required")
            
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Invalid email format")
            
        if get_user(email):
            errors.append("Email already registered")
            
        if password != confirm_password:
            errors.append("Passwords don't match")
            
        is_strong, pwd_msg = is_password_strong(password)
        if not is_strong:
            errors.append(pwd_msg)
            
        # Process if no errors
        if not errors:
            if create_user(full_name, email, password):
                st.success("Account created successfully! Please login.")
                # delay 3 secs
                st.switch_page("pages/1_login.py")
            else:
                st.error("Registration failed - please try again")
        else:
            for error in errors:
                st.error(error)

    # Login link
    st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            Already have an account? <a href="/login" target="_self"
            style="text-decoration:none; color:#e83757;">Login here</a>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
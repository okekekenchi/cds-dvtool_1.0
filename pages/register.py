import streamlit as st
import re
import time
from util.auth_utils import create_user, is_password_strong, email_exists, guest
from loader.config_loader import config
from loader.css_loader import load_css
from database.migration import init_db

st.set_page_config(page_title="Register", page_icon="📝", layout="centered", initial_sidebar_state="collapsed")

@guest
def main():
    load_css('assets/css/register.css')
    st.title("Sign Up")

    full_name = st.text_input("Full Name", placeholder="Enter your full name")
    email = st.text_input("Email", placeholder="example@domain.com")
    password = st.text_input("Password", type="password", placeholder="********",
                        help="At least 8 characters with 1 number, 1 uppercase, and 1 lowercase")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="********")
    
    st.write("")
    register_button = st.button("Register", type="primary", use_container_width=True)

    if register_button:
        # Client-side validation
        errors = []
        
        if not full_name.strip():
            errors.append("Full name is required")
            
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Invalid email format")
            
        if email_exists(email):
            errors.append("Email already registered")
            
        if password != confirm_password:
            errors.append("Passwords don't match")
            
        is_strong, pwd_msg = is_password_strong(password)
        if not is_strong:
            errors.append(pwd_msg)
            
        # Process if no errors
        if not errors:
            if create_user(full_name, email, password, "admin"):
                st.success("Account created successfully! Please login.")
                time.sleep(2)
                st.switch_page(config('route.login'))
            else:
                st.error("Registration failed - please try again")
        else:
            for error in errors:
                st.error(error)

    st.divider()
    col1, col2 = st.columns([1, 1], vertical_alignment="center")
    with col1:
        st.write("Already have an account?")
    with col2:
        if st.button("Login here", use_container_width=True, help="Login"):
            st.switch_page("pages/login.py")
    
    st.write("")
            
if __name__ == "__main__":
    init_db()
    st.session_state.current_page = config('route.register')
    main()
    
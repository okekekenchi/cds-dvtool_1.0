import streamlit as st
import re
import time
import config
from utils import create_user, is_password_strong, email_exists, guest, hide_nav_and_header

st.set_page_config(page_title="Register", page_icon="📝", layout="centered", initial_sidebar_state="collapsed")

# Apply CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    st.markdown("""
    <style>
        .stAppHeader { display: none; }        
        section[data-testid="stSidebar"] { display: none !important; }
        iframe { display: none !important; }
        h1 { padding-top: 0; }

        .stMainBlockContainer {
            padding-top: 50px;
            padding-bottom: 30px;
        }

        .st-emotion-cache-gsx7k2 {
            width: 400px;
            justify-self: center !important;
            border: 1px solid lightgray;
            border-radius: 2em;
            padding: 20px;
        }
    </style>
    """, unsafe_allow_html=True)

@guest
def main():
    hide_nav_and_header()
    st.session_state.current_page = config.ROUTE_REGISTER
    st.title("Sign Up")

    full_name = st.text_input("Full Name", placeholder="Enter your full name")
    email = st.text_input("Email", placeholder="example@domain.com")
    password = st.text_input("Password", type="password", placeholder="********",
                        help="At least 8 characters with 1 number, 1 uppercase, and 1 lowercase")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="********")

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
            if create_user(full_name, email, password):
                st.success("Account created successfully! Please login.")
                time.sleep(3)
                st.switch_page(config.ROUTE_LOGIN)
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
            
if __name__ == "__main__":
    main()
    
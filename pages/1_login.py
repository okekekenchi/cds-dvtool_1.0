import streamlit as st
from utils import login, guest, hide_nav_and_header
from loader.config_loader import config
from loader.css_loader import load_css

st.set_page_config(page_title="Login", page_icon="🔒", layout="centered", initial_sidebar_state="collapsed")
load_css('assets/css/login.css')
hide_nav_and_header()

@guest
def main():
    st.session_state.current_page = config('route.login')
    st.title("Sign In")
    
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    submit = st.button("Login", type="primary", use_container_width=True)

    if submit:
        if not email or not password:
            st.error("Please fill in all fields")
        else:
            if login(email, password):
                st.switch_page(config('route.home'))
            else:
                st.error("Invalid email or password")

    st.markdown("""
        <div style="text-align: center; margin-top: 20px;">
            Don't have an account? <a href="/register" target="_self"
            style="text-decoration:none; color:#e83757;">Register here</a>
        </div>
    """, unsafe_allow_html=True)
            
if __name__ == "__main__":
    main()
    
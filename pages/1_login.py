import streamlit as st
import config
from utils import login, guest, hide_nav_and_header

st.set_page_config(page_title="Login", page_icon="🔒", layout="centered", initial_sidebar_state="collapsed")

# Apply CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    st.markdown("""
    <style>
        .stAppHeader { display: none; }
        section[data-testid="stSidebar"] { display: none !important; }
        .stMainBlockContainer { padding-bottom: 0px; }
        iframe { display: none; }

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
    st.session_state.current_page = config.ROUTE_LOGIN
    st.title("Sign In")
    
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    submit = st.button("Login", type="primary", use_container_width=True)

    if submit:
        if not email or not password:
            st.error("Please fill in all fields")
        else:
            if login(email, password):
                st.switch_page(config.ROUTE_HOME)
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
    
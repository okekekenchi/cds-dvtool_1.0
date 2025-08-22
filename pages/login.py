import streamlit as st
from util.auth_utils import login, guest
from loader.config_loader import config
from loader.css_loader import load_css
from database.migration import init_db

st.set_page_config(page_title="Login", page_icon=":material/key:", layout="centered", initial_sidebar_state="collapsed")

@guest
def main():
    load_css('assets/css/login.css')
    st.write("")
    st.write("")
    st.title("Sign In")
    
    email = st.text_input("Email", placeholder="Enter your email", key="login_email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    
    st.write("")
    submit = st.button("Login", type="primary", use_container_width=True)

    if submit:
        if not email or not password:
            st.error("Please fill in all fields")
        else:
            if login(email, password):
                st.switch_page(config('route.home'))
            else:
                st.error("Invalid email or password")

    st.markdown("---")
    col1, col2 = st.columns([1, 1], vertical_alignment="center")
    with col1:
        st.write("Don't have an account?")
    with col2:
        if st.button("Register here", use_container_width=True, help="Register"):
            st.switch_page("pages/register.py")
    
    st.write("")
            
if __name__ == "__main__":
    init_db()
    st.session_state.current_page = config('route.login')
    main()
    
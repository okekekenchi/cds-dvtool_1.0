import streamlit as st
from util.auth_utils import authenticated
from components.side_nav import side_nav
from loader.config_loader import config
from loader.css_loader import load_css
from database.migration import init_db

st.set_page_config(page_title="Dashboard", page_icon=":material/dashboard:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/dashboard.css')

@authenticated
def main():
    side_nav()
    st.title('welcome home')    
    
    
if __name__ == "__main__":
    init_db()
    st.session_state.current_page = config('route.home')
    main()
    
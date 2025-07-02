import streamlit as st
from utils import authenticated
from components.side_nav import side_nav
from loader.config_loader import config
from loader.css_loader import load_css

st.set_page_config(page_title="Dashboard", page_icon=":material/dashboard:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/dashboard.css')

@authenticated
def main():
    st.session_state.current_page = config('route.home')
    side_nav()
    st.title('welcome home')    
    
    
if __name__ == "__main__":
    main()
    
import streamlit as st
from utils import authenticated, load_css
import config
from components.side_nav import side_nav

st.set_page_config(page_title="Dashboard", page_icon=":material/dashboard:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/dashboard.css')

@authenticated
def main():
    st.session_state.current_page = config.ROUTE_HOME
    side_nav()
    st.title('welcome home')
    
    
    
if __name__ == "__main__":
    main()
    
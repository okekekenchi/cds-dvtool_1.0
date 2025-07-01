import streamlit as st
from utils import authenticated
from components.side_nav import side_nav
from loader.config_loader import config
from loader.css_loader import load_css

st.set_page_config(page_title="Dashboard", page_icon=":bar_chart:", layout="wide", initial_sidebar_state="expanded")
load_css()

@authenticated
def main():
    st.session_state.current_page = "pages/5_validation_check.py"
    side_nav()
    st.write("Validation check content goes here")

if __name__ == "__main__":
    main()
    
import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("components.checklist")

import streamlit as st
from loader.css_loader import load_css
from database.migration import init_db
from components.side_nav import side_nav
from util.auth_utils import authenticated
from components.checklist.view import view_checklist
from components.checklist.create import create_checklist
from components.checklist.update import update_checklist

st.set_page_config(page_title="Checklist", page_icon=":material/task:",
                   layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/checklist.css')

def init_session_var():
    if 'selected_checklist' not in st.session_state:
        st.session_state.selected_checklist = {}
    if "active_records" not in st.session_state:
        st.session_state.active_records = 1
    if "update_checklist" not in st.session_state:
        st.session_state.update_checklist = False
    if "create_checklist" not in st.session_state:
        st.session_state.create_checklist = True
    if "reset_form" not in st.session_state:
        st.session_state.reset_form = True
        
def item_selected():
    return True if st.session_state.selected_checklist.get('id') else False
        
@authenticated
def main():
    st.title("Validation Checklist")
    side_nav()
    init_session_var()
    
    if item_selected():
        st.session_state.tabs = ["View", "Update Checklist"]
    else:
        st.session_state.tabs = ["View", "Create Checklist"]
    
    view, action = st.tabs(st.session_state.tabs)
    
    with view:
        view_checklist()
          
    with action:
        if item_selected():
            update_checklist()
        else:
            create_checklist()
                
    st.write('')
    st.write('')
                
if __name__ == "__main__":
    init_db()
    st.session_state.current_page = "pages/checklist.py"
    main()
    
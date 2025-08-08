import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

# reload_package("components.checklist_view")
# reload_package("components.checklist_create_form")
# reload_package("components.checklist_update_form")

import streamlit as st
from loader.css_loader import load_css
from database.migration import init_db
from components.side_nav import side_nav
from util.auth_utils import authenticated
from components.checklist_view import checklist_view
from components.checklist_create_form import checklist_create_form
from components.checklist_update_form import checklist_update_form

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
        
@authenticated
def main():
    st.title("Validation Checklist")
    st.session_state.current_page = "pages/checklist.py"
    side_nav()
    init_session_var()
    
    if st.session_state.selected_checklist.get('id'):
        st.session_state.tabs = ["View", "Update Checklist"]
    else:
        st.session_state.tabs = ["View", "Create Checklist"]
    
    view, action = st.tabs(st.session_state.tabs)
    
    with view:
        checklist_view()
          
    with action:
        if st.session_state.selected_checklist.get('id'):
            checklist_update_form()
        else:
            checklist_create_form()
                
    st.write('')
    st.write('')
                
if __name__ == "__main__":
    init_db()
    st.session_state.current_page = "pages/checklist.py"
    main()
    
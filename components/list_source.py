import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("services.list_service")

import streamlit as st
from services.list_service import (
    get_source_from_master_tables,
    get_source_from_sheets,
    get_source_from_validation_checklist
)


@st.dialog('List Source')
def set_list_source_string() -> str:
    st.session_state.update({'list_source_str': None})
    source_string = None
    
    list_type = st.selectbox(f"**Select List Source**",
                            options=['masters', 'sheets', 'validation_checklist'],
                            key="list_source_field",
                            format_func=lambda x: x.replace('_',' ').capitalize())

    if list_type == 'masters':
        source_string = get_source_from_master_tables()
    
    if list_type == 'sheets':
        source_string = get_source_from_sheets()
    
    if list_type == 'validation_checklist':
       source_string = get_source_from_validation_checklist()
    
    st.write('')
    st.write('')
    
    col1, _, col2 = st.columns([0.35,0.3,0.35])
    with col1:
        if st.button('Save', key="save_list_source", icon=":material/save:"):
            st.session_state.update({"list_source_str": source_string})
            st.rerun()
    with col2:
        if st.button('Cancel', key="cancel_list_source", icon=":material/close:"):
            st.rerun()

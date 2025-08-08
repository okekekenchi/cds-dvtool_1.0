import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])
            
reload_package("components.column_operation")

import pandas as pd
import streamlit as st
from components.column_operation import column_operation

def clear_sheets():
    """Reset all sheets"""
    st.session_state.config.update({"sheets":[], "joins":[], "conditions":[]})
    
def delete_sheet(sheet_index:int):
    """
    Delete sheet name at the specified index
    deletes all joins have the sheet name

    Args:
        sheet_index (int): _description_
    """
    sheet_name = st.session_state.config['sheets'][sheet_index]
    del st.session_state.config['sheets'][sheet_index]
    
    joins = st.session_state.config['joins']
    for idx, join in enumerate(joins):
        if sheet_name in [join["left_table"], join["right_table"]]:
            del st.session_state.config['joins'][idx]                            
    
@st.dialog('Preview Sheet/Table', width="large")
def preview_sheet(df):
    st.dataframe(df.head())

@st.dialog('Column Operation', width="large")
def configure_column(all_sheets: dict, sheet_name:str, sheet_index:int):
    column_operation(all_sheets, sheet_name, sheet_index)
    
    st.write('')
    st.write('')
    
    _, col1 = st.columns([0.8,0.2])
    with col1:
        if st.button('Close', key="close_col_operations", icon=":material/close:"):
            st.rerun()
    
def get_selected_sheet_names():
    return[
        sheet['name']
        for sheet in st.session_state.config.get('sheets', [])
    ]
    
def show_selected_sheets(all_sheets: dict):
    selected_sheet_names = get_selected_sheet_names()
    
    if not selected_sheet_names:
        clear_sheets()
        st.write("Your sheet list is empty!")
    else:
        for i, sheet_name in enumerate(selected_sheet_names):
            st.divider()
            col1, col2, col3, col4 = st.columns([0.6, 0.125,0.125,0.15])
            
            with col1:
                st.write(f"{i+1}. {sheet_name}")
            with col2:
                if (st.button(f"Preview ", key=f"preview_sheet_{i}",
                              icon=":material/visibility:", help="Preview the top 5 records")):
                    preview_sheet(all_sheets[sheet_name])
            with col3:
                if (st.button(f"Configure ", key=f"configure_column_{i}",
                    icon=":material/settings:", help="Configure column operations.")):
                    configure_column(all_sheets, sheet_name, i)
                    
            with col4:
                if st.button(f"Delete", key=f"delete_sheet_{i}", icon=":material/delete:"):
                    delete_sheet(sheet_index=i)                            
                    st.rerun()

def select_sheets(all_sheets: dict):
    """Renders UI for selecting and managing sheets for validation.
    
    Allows users to:
    - Select sheets from available workbook sheets
    - Add selected sheets to validation checklist
    - Remove sheets from validation checklist
    
    Returns:
        None - updates session state directly
    """
    col1, col2, col3, _ = st.columns([0.5,0.2,0.05, 0.25])
    sheet_options = list(all_sheets.keys())
    selected_sheets = get_selected_sheet_names()
    
    with col1:
        new_sheets = st.multiselect(
                        "Select sheets/tables to validate *",
                        key="selected_sheets",
                        options=[ option for option in sheet_options if option not in selected_sheets ],
                        default=None,
                        help="Select which sheets you want to include in validation"
                     )
    with col2:
        if st.button("Add", key="add_sheets", icon=":material/add:") and new_sheets:
            for sheet_name in new_sheets:
                if sheet_name not in selected_sheets:
                    st.session_state.config['sheets'].append({ "name": sheet_name, "col_operations":[] })
            st.rerun()
            
    with col3:
        st.write('')
        st.write('')
        if st.button("",key="clear_sheets",icon=":material/refresh:",help="Clear all selected sheets"):
            clear_sheets()
            
    show_selected_sheets(all_sheets)
    
        
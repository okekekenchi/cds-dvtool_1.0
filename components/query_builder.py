import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("components.list_source")
reload_package("components.query_builder_service")

import pandas as pd
import streamlit as st
from utils import alert
from util.project_utils import operators
from components.list_source import set_list_source_string
from services.query_builder_service import get_list_from_selected_source

def on_list_type_changed():
    if st.session_state.get("list_type") == "others":
        set_list_source_string()
    
def remove_condition(index):
    """Remove a condition from the list"""
    st.session_state.config['conditions'].pop(index)

def clear_conditions():
    """Reset all conditions"""
    st.session_state.config['conditions'] = []
    
@st.dialog('List')
def preview_list_from_selected_source(all_sheets: dict):
    st.dataframe(
        get_list_from_selected_source(
            all_sheets=all_sheets,
            list_source=st.session_state.list_source_str
        )
    )
    
def build_query(all_sheets: dict, joined_df: pd.DataFrame) -> pd.DataFrame:
    col1, col2, col3, col4 = st.columns([3, 3, 3, 3]) # Add new query condition
    new = {}
    new['value_2'] = None
    list_type = None
    value_1_is_required = True
    options = ([] if joined_df.empty else joined_df.columns.to_list())
        
    with col1:
        new['column'] = st.selectbox("Column *", key="new_column", options=options)
        character_placeholder = st.empty()
        
    with col2:
        new['operator'] = st.selectbox("Operator *",
                                        options=operators.keys(),
                                        key="new_operator",
                                        format_func=lambda x: operators[x])
    with col3:
        if new['operator'] in ['is_null', 'not_null']:
            new['value_1'] = None
            new['value_2'] = None
            value_1_is_required = False 
            
        elif new['operator'] in ['column_equals', 'column_not_equals', 'merge']:
            new['value_1'] = st.selectbox("Column *", key="new_matching_column",
                                            options=([] if joined_df.empty else joined_df.columns))
            if new['operator'] == 'merge':
                new['value_2'] = st.text_input("Column name *", key="merged_column_name")
            else:
                new['value_2'] = None
            
        elif new['operator'] in ['in_list', 'not_in_list']:
            list_type = st.selectbox("List type *",
                                    options=['custom', 'others'],
                                    key="list_type",
                                    format_func=lambda x: x.replace('_',' ').capitalize(),
                                    on_change=on_list_type_changed
                                )
            
            if list_type == "custom":
                new['value_1'] = st.text_input("Comma-separated values *", key="custom_list_string")
                new['value_2'] = st.session_state.nv_list_character = None
            else:                
                if st.session_state.list_source_str:
                    new['value_1'] = st.text_input("List source *", key="nv_lsource",
                                                    value=st.session_state.list_source_str, disabled=True)
                    new['value_2'] = st.number_input("Character", key="nv_list_character", min_value=0,
                                                     step=1, max_value=100)
                else:
                    st.warning('No list source selected.')
            
            with character_placeholder.container():
                new['column_char'] = st.number_input("Character", key="nv_char", min_value=0,
                                                     step=1, max_value=100)
                
        elif new['operator'] == 'between':
            new['value_1'] = st.text_input("From value *", key="nv_2")
            new['value_2'] = st.text_input("To value *", key="nv_3")
            
        elif new['operator'] in ['contains', 'not_contains']:
            new['value_1'] = st.text_input("Value *", "", key="nv_4")
            new['value_2'] = st.text_input("Position", key="nv_5")
            
        else:
            new['value_1'] = st.text_input("Value *", key="nv_6")
            new['value_2'] = None
            
    with col4:
        new['logic'] = st.selectbox("", options=['And', 'Or'], key="new_logic")
        
        if st.session_state.list_source_str and list_type == "others":
            st.markdown("<p style='margin-top:28px;'></p>", unsafe_allow_html=True)
            
            col_1, col_2, _ = st.columns([0.25,0.25, 0.5])
            with col_1:
                if st.button(f"", key=f"edit_list_source",icon=":material/edit:", help='Edit List Source'):
                    on_list_type_changed()
            with col_2:
                if st.button(f"", key=f"preview_list_source",icon=":material/visibility:", help="View list Source"):
                    preview_list_from_selected_source(all_sheets)
                    
    # Action buttons
    _, col1, col2 = st.columns([0.7,0.2,0.05])
    
    with col1:
        if st.button(f"Add", key="add_query_condition", icon=":material/add:"):            
            if (not new['column'] or not new['operator'] or not new['logic']):
                alert("Fill all required fields")
                return
            
            if not new['value_1'] and value_1_is_required:
                alert("Fill all required fields")
                return
            
            if new not in st.session_state.config['conditions']:
                st.session_state.config['conditions'].append(new)
                st.rerun()
            else:
                alert("You have already this condition")
                        
    with col2:
        st.button("", on_click=clear_conditions, icon=":material/refresh:",
                  help="Clear all conditions", key="clear_conditions")
    
    if st.session_state.config['conditions']:
        columns = ['Column', 'Character', 'Operator', 'Value', 'Logic', 'Action']
        
        for i, col in enumerate(st.columns([0.23, 0.18, 0.2, 0.22, 0.15, 0.07])):
            with col:
                st.write(f"**{columns[i]}**")
        
        for i, cond in enumerate(st.session_state.config['conditions']):
            col1, col2, col3, col4, col5, col6 = st.columns([0.23, 0.18, 0.2, 0.22, 0.15, 0.07])
            with col1:
                st.write(f"{cond['column']}")
            with col2:
                st.write(f"{cond['column_char'] if 'column_char' in cond else 'N/A'}")
            with col3:
                st.write(f"{cond['operator'].replace('_', ' ').title()}")
            with col4:
                if cond['operator'] in ['between']:
                    st.write(f"{cond['value_1']} **and** {cond['value_2']}")
                elif cond['operator'] in ['contains','not_contains'] and cond['value_2']:
                    st.write(f"{cond['value_1']} **in position** {cond['value_2']}")
                elif cond['operator'] in ['in_list','not_in_list'] and cond['value_2']:
                    st.write(f"{cond['value_2']} **char of** {cond['value_1']}")
                else:
                    st.write(f"{cond['value_1'] or 'N/A'}")
            with col5:
                if i < len(st.session_state.config['conditions']) - 1:
                    st.write(f"{cond.get('logic', 'And')}")
            with col6:
                st.button("", icon=":material/delete:", help="Delete query condition",
                          key=f"remove_condition_{i}", on_click=remove_condition, args=(i,))

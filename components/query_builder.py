import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("components.list_source")
reload_package("services.query_builder_service")
reload_package("util.project_utils")

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
    try:
        st.session_state.config['conditions'].pop(index)
    except Exception as e:
        st.toast('All cleared')

def clear_conditions():
    """Reset all conditions"""
    if 'conditions' in st.session_state.config:
        st.session_state.config['conditions'] = []
    
@st.dialog('List')
def preview_list_from_selected_source(all_sheets: dict):
    st.dataframe(
        get_list_from_selected_source(
            all_sheets=all_sheets,
            list_source=st.session_state.list_source_str
        )
    )

def set_logical_group():
    nested_logic = st.session_state.get('nested_logic')
    
    if nested_logic in ['AND','OR']:
        last_item = st.session_state.config['conditions'][-1]
        if 'nested_logic' in last_item:
            st.session_state.config['conditions'][-1]["nested_logic"] = nested_logic
        else:
            st.session_state.config['conditions'].append({
                "nested_logic": nested_logic
            })    

def show_selected_conditions():
    if st.session_state.config['conditions']:
        columns = ['Column', 'Character', 'Operator', 'Value', 'Logic', 'Action']
        
        for i, col in enumerate(st.columns([0.23, 0.18, 0.2, 0.22, 0.15, 0.07])):
            with col:
                st.write(f"**{columns[i]}**")
        
        for i, cond in enumerate(st.session_state.config['conditions']):
            col1, col2, col3, col4, col5, col6 = st.columns([0.23, 0.18, 0.2, 0.22, 0.15, 0.07])
            
            if 'nested_logic' in cond:
                with col1:
                    n_logic = st.selectbox(label="",
                                    options=['AND', 'OR'],
                                    key=f"selected_nested_logic_{i}",
                                    label_visibility="collapsed",
                                    index= 0 if cond['nested_logic'] == "AND" else 1
                                )
                    st.session_state.config['conditions'][i]["nested_logic"] = n_logic
            else:
                with col1:
                    st.write(f"{cond['column']}")
                with col2:
                    st.write(f"{cond['column_char'] if 'column_char' in cond else 'N/A'}")
                with col3:
                    st.write(f"{operators.get(cond['operator'])}")
                with col4:
                    if cond['operator'] in ['between']:
                        st.write(f"{cond['value_1']} **and** {cond['value_2']}")
                    elif cond['operator'] in ['contains','not_contains'] and cond['value_2']:
                        st.write(f"{cond['value_1']} **in position** {cond['value_2']}")
                    elif cond['operator'] in ['in_list','not_in_list','wildcard_match', 'wildcard_not_match'] and cond['value_2']:
                        st.write(f"{cond['value_2']} **char of** {cond['value_1']}")
                    else:
                        st.write(f"{cond['value_1'] or 'N/A'}")
                with col5:
                    if i < len(st.session_state.config['conditions']) - 1:
                        next_item = st.session_state.config['conditions'][i+1]
                        if 'nested_logic' not in next_item:
                            st.write(f"{cond.get('logic', 'And')}")
            with col6:
                st.button("", icon=":material/delete:", help="Delete query condition",
                          key=f"remove_condition_{i}", on_click=remove_condition, args=(i,))
    
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
        if new['operator'] in ['is_null', 'not_null', 'has_parent', 'has_no_parent']:
            new['value_1'] = None
            new['value_2'] = None
            value_1_is_required = False
        
        elif new['operator'] in ['distinct_combinations','non_distinct_combinations','length_equals','length_not_equals']:
            new['value_1'] = st.selectbox("Column *", key="new_matching_column", options=options)
            new['value_2'] = None
        
        elif new['operator'] in ['column_equals', 'column_not_equals']:
            new['value_1'] = st.selectbox("Column *", key="new_matching_column", options=options)
           
            with character_placeholder.container():
                new['column_char'] = st.number_input("Character", key="nv_char", min_value=0,
                                                    step=1, max_value=100,
                                                    help="Optional: Check at specific character position")
            if new['column_char']:
                new['value_2'] = st.number_input("Character", key="nv_list_character", min_value=0,
                                                step=1, max_value=100)
            else:
                new['value_2'] = None
                
        elif new['operator'] in ['in_column_list', 'not_in_column_list']:
            new['value_1'] = st.selectbox("Column *", key="new_matching_column", options=options)
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
                
        elif new['operator'] in ['wildcard_match', 'wildcard_not_match']:
            new['value_1'] = st.text_input("Wildcard Pattern *", key="wildcard_input")
            # new['value_2'] = st.number_input("Character Position", key="wildcard_char_position",
            #                                     step=1, min_value=0, max_value=100)
            new['value_2'] = None
            
        elif new['operator'] == 'between':
            new['value_1'] = st.text_input("From value *", key="from_between_input")
            new['value_2'] = st.text_input("To value *", key="to_between_input")
            
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
    
    show_selected_conditions()
    
    if st.session_state.config['conditions']:
        col1, col2, _ = st.columns([0.2, 0.1, 0.8])
        with col1:
            st.selectbox(label="",
                        options=['--Select Logical Group--','AND', 'OR'],
                        key="nested_logic",
                        help="Use nested logical operator to group rules",
                        label_visibility='hidden'
                    )
        with col2:
            st.write('')
            st.write('')
            st.button("", on_click=set_logical_group, icon=":material/add:",
                  help="Group logic", key="add_group_logical_operator")

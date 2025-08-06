import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("util.project_utils")

import pandas as pd
import streamlit as st
from utils import alert
from util.project_utils import column_operators

    
def remove_condition(index):
    """Remove a condition from the list"""
    st.session_state.config['col_operations'].pop(index)

def clear_col_operations():
    """Reset all column operations"""
    st.session_state.config['col_operations'] = []

def show_selected_col_operations():
    if st.session_state.config.get('col_operations', []):
        columns = ['Column', 'Operator', 'Value', 'Action']
        
        for i, col in enumerate(st.columns([0.33, 0.35, 0.3, 0.07])):
            with col:
                st.write(f"**{columns[i]}**")
        
        for i, cond in enumerate(st.session_state.config['col_operations']):
            col1, col3, col4, col6 = st.columns([0.33, 0.35, 0.3, 0.07])        
            with col1:
                st.write(f"{cond['column']}")
            with col3:
                st.write(f"{column_operators.get(cond['operator'])}")
            with col4:
                if cond['operator'] in ['between']:
                    st.write(f"{cond['value_1']} **and** {cond['value_2']}")
                elif cond['operator'] in ['contains','not_contains'] and cond['value_2']:
                    st.write(f"{cond['value_1']} **in position** {cond['value_2']}")
                elif cond['operator'] in ['in_list','not_in_list','wildcard_match', 'wildcard_not_match'] and cond['value_2']:
                    st.write(f"{cond['value_2']} **char of** {cond['value_1']}")
                else:
                    st.write(f"{cond['value_1'] or 'N/A'}")
            with col6:
                st.button("", icon=":material/delete:", help="Delete query condition",
                          key=f"remove_col_op_{i}", on_click=remove_condition, args=(i,))
    
def column_operation(joined_df: pd.DataFrame) -> pd.DataFrame:
    col1, col2, col3, col4 = st.columns([3, 3, 3, 3])
    new = {}
    new['value_2'] = None
    options = ([] if joined_df.empty else joined_df.columns.to_list())
        
    with col1:
        new['column'] = st.selectbox("Column *", key="new_col_op", options=options)
        
    with col2:
        new['operator'] = st.selectbox("Operator *",
                                        options=column_operators.keys(),
                                        key="new_col_op_operator",
                                        format_func=lambda x: column_operators[x])
    with col3:        
        if new['operator'] == "merge":
            new['value_1'] = st.selectbox("Column *", key="new_merge_col_op",
                                            options=([] if joined_df.empty else joined_df.columns))
                   
        elif new['operator'] == "split":
            new['value_1'] = st.text_input("Delimiter *", key="split_delimiter_input")
    with col4:
        if new['operator'] == "merge":
            new['value_2'] = st.text_input("Column name *", key="merged_column_name")
                   
        elif new['operator'] == "split":
            new['value_2'] = st.text_input("Column Names *", key="split_Column_names",
                                                help="Separated by comma, specify the column names")
                                
    _, col1, col2 = st.columns([0.7,0.2,0.05])
    
    with col1:
        if st.button(f"Add", key="add_col_op", icon=":material/add:"):
            if not new['column'] or not new['operator'] or not new['value_1']:
                alert("Fill all required fields")
                return
            
            try:
                if new not in st.session_state.config.get('col_operations', []):
                    st.session_state.config['col_operations'].append(new)
                    st.rerun()
                else:
                    alert("You already have this condition")
            except Exception as e:
                st.session_state.config['col_operations'] = []
    with col2:
        st.button("", on_click=clear_col_operations, icon=":material/refresh:",
                  help="Clear all column operations", key="clear_col_ops")
    
    show_selected_col_operations()

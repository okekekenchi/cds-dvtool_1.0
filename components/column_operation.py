import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("util.project_utils")

import pandas as pd
import streamlit as st
from util.project_utils import column_operators

    
def remove_condition(configuration: dict, sheet_index:int, operation_index:int):
    """Remove a condition from the list"""
    configuration['sheets'][sheet_index]['col_operations'].pop(operation_index)
    st.rerun(scope="fragment")

def clear_col_operations(configuration: dict, sheet_index:int):
    """Reset all column operations"""
    configuration['sheets'][sheet_index]['col_operations'] = []
    st.rerun(scope="fragment")


def show_selected_col_operations(configuration:dict, column_operations:list, sheet_index:int):    
    if column_operations:
        columns = ['Column', 'Operator', 'Value 1', 'Value 2', 'Action']
        
        for i, col in enumerate(st.columns([0.15, 0.27, 0.15, 0.33, 0.1], vertical_alignment='center')):
            with col:
                st.write(f"**{columns[i]}**")
        
        for i, cond in enumerate(column_operations):
            col1, col2, col3, col4, col5 = st.columns([0.15, 0.27, 0.15, 0.33, 0.1], vertical_alignment='center')
            with col1:
                st.write(f"{cond['column']}")
            with col2:
                st.write(f"{column_operators.get(cond['operator'])}")
            with col3:
                    st.write(f"{cond['value_1']}")
            with col4:
                    st.write(f"{cond['value_2'] if 'value_2' in cond else 'N/A'}")
            with col5:
                if (st.button("", icon=":material/delete:", help="Delete query condition",
                                key=f"remove_col_op_{i}")):
                    remove_condition(configuration, sheet_index, i)
    else:
        st.info("You have not performed any column operation.")
        
@st.dialog('Column Operation', width="large", dismissible=True, on_dismiss='rerun')
def column_operation(all_sheets:dict, configuration:dict, sheet_name:str, sheet_index:int) -> list:
    if 'col_operations' not in configuration['sheets'][sheet_index]:
        configuration['sheets'][sheet_index]['col_operations'] = []
        
    col1, col2, col3, col4 = st.columns([3, 3, 3, 3], vertical_alignment='center')
    selected_column_operations = configuration['sheets'][sheet_index]['col_operations']
    new = {}
    new['value_2'] = None
    sheet_df = all_sheets.get(sheet_name, pd.DataFrame())
    options = ([] if sheet_df.empty else sheet_df.columns.to_list())
        
    with col1:
        new['column'] = st.selectbox("Column *", key="new_col_op", options=options)
        
    with col2:
        new['operator'] = st.selectbox("Operator *", help="",
                                        options=column_operators.keys(),
                                        key="new_col_op_operator",
                                        format_func=lambda x: column_operators[x])
    with col3:        
        if new['operator'] == "merge":
            new['value_1'] = st.selectbox("Column *", key="new_merge_col_op",
                                            options=([] if sheet_df.empty else sheet_df.columns))
                   
        elif new['operator'] == "split":
            new['value_1'] = st.text_input("Delimiter : Max Split * (e.g.  , : 2)", key="split_delimiter_input",
                                           help="Specify how you wish to split the column.")
                   
        elif new['operator'] == "get_character":
            new['value_1'] = st.number_input("Character Position", key="split_char_pos_input",
                                             step=1, min_value=1, max_value=100)
    with col4:
        if new['operator'] in ["merge", "get_character"]:
            new['value_2'] = st.text_input("New Column name *", key="merged_column_name")
                   
        elif new['operator'] == "split":
            new['value_2'] = st.text_input("New Column Names *", key="split_Column_names",
                                            help="Separated by comma, specify the column names")
                                
    _, col1, col2 = st.columns([0.73,0.18,0.09], vertical_alignment='center')
    
    with col1:
        if st.button(f"Add", key="add_col_op", icon=":material/add:"):
            if new['column'] and new['operator'] and new['value_1'] and new['value_2']:                
                if new not in configuration['sheets'][sheet_index].get('col_operations', []):
                    selected_column_operations.append(new)
                else:
                    st.toast("You already have this condition")
            else:
                st.toast("Fill all required fields")
    with col2:
        if (st.button("", icon=":material/refresh:", key="clear_col_ops",
                      help="Clear all column operations")):
            clear_col_operations(configuration, sheet_index)
    
    show_selected_col_operations(configuration, selected_column_operations, sheet_index)
    st.write("")
    st.write("")

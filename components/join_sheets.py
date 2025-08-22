import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("services.join_service")
reload_package("components.join_conditions")

import pandas as pd
import streamlit as st
from utils import alert
from services.join_service import join_types, print_matching_columns
from components.join_conditions import join_conditions

def show_joined_sheets(sheets: dict, configuration:dict):
    if not configuration['joins']:
        st.write("Your join list is empty!")
        return

    for idx, join in enumerate(configuration['joins']):
        st.divider()
        col1, col2 = st.columns([0.8, 0.2], vertical_alignment='center')
        
        with col1:
            df = pd.DataFrame([join])
            if 'on_cols' in df:
                df = df.drop(columns=["on_cols"])  # Remove column
            
            df['join_type'] = df['join_type'].map(join_types)
            df.columns = [ f"**{column.replace('_', ' ').capitalize()}**" for column in df.columns]
            st.table(df)
        
        with col2:
            if st.button("Conditions", key=f"join_conditions_{idx}"):
                if join['left_table'] and join['right_table'] and join['join_type']:
                    join_conditions(sheets, configuration, idx, join)
                else:
                    alert("Fill all required fields")
            
            if st.button(f"Delete", key=f"delete_join_conditions_{idx}", icon=":material/delete:"):
                del configuration['joins'][idx]
                configuration['conditions'] = []
                st.rerun(scope='fragment')

def join_sheets(sheets: dict, configuration: dict):
    """Renders UI for selecting and joining sheets for validation.
    
    Allows users to:
    - Join sheets from selected worksheets
    - Add selected joins to validation list
    - Remove jions from validation list
    
    Returns:
        None - updates session state directly
    """
    col1, col2, col3, col4 = st.columns([0.3, 0.2, 0.3, 0.2])
    new_join = {}
    
    with col1:
        new_join['left_table'] = st.selectbox(
                                    "Left Table *",
                                    options=sheets,
                                    index=None,
                                    help="Select which sheets/tables you want to include in the validation"
                                )
    with col2:
        new_join['join_type'] = st.selectbox(
                                    "Join Type *",
                                    options=join_types.keys(),
                                    index=1,
                                    help="Select which join type to implement",
                                    format_func=lambda x: join_types[x]
                                )
    with col3:
        new_join['right_table'] = st.selectbox(
                                        "Right Table *",
                                        options=sheets,
                                        index=None,
                                        help="Select which sheets/tables you want to include in the validation"
                                    )
    with col4:
        st.markdown("<style>.m-top{margin-top:23px;}</style><div class='m-top'></div>", unsafe_allow_html=True)
        if st.button("Add", key="add_joins", icon=":material/add:"):
            if new_join['left_table'] and new_join['right_table'] and new_join['join_type']:            
                if new_join['left_table'] == new_join['right_table']:
                    alert("You have selected the same option for both left and right tables")
                    return
                
                if new_join not in configuration['joins']:
                    configuration['joins'].append(new_join)
                else:
                    alert("You have already joined these sheets")
            else:
                alert("Fill all required fields")
    
    print_matching_columns(sheets, new_join)
    
    show_joined_sheets(sheets, configuration)

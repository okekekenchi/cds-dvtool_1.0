import streamlit as st
from utils import alert
from util.project_utils import join_types
from components.join_conditions import join_conditions
from util.project_utils import print_matching_columns
import pandas as pd
 
def join_sheets(sheets: dict):
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
        if st.button("Add", key="add_joins", icon=":material/add:"):
            if not new_join['left_table'] or not new_join['right_table'] or not new_join['join_type']:
                alert("Fill all required fields")
                return
            
            if new_join['left_table'] == new_join['right_table']:
                alert("You have selected the same option for both left and right tables")
                return
            
            if new_join not in st.session_state.config['joins']:
                st.session_state.config['joins'].append(new_join)
                st.rerun()
            else:
                alert("You have already joined these sheets")
    
    print_matching_columns(sheets, new_join)
        
    if not st.session_state.config['joins']:
        st.write("Your join list is empty!")
    else:
        # View join list
        for idx, join in enumerate(st.session_state.config['joins']):
            st.divider()
            col1, col2 = st.columns([0.8, 0.2])
            
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
                        join_conditions(sheets, idx, join)
                    else:
                        alert("Fill all required fields")
                
                if st.button(f"Delete", key=f"delete_join_conditions_{idx}", icon=":material/delete:"):
                    del st.session_state.config['joins'][idx]
                    st.rerun()


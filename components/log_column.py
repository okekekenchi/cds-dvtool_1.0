import copy
import pandas as pd
import streamlit as st
    
def unselect_column(configuration: dict, index: int):
    """Remove a condition from the list"""
    try:
        del configuration["log"]["columns"][index]
        st.rerun(scope='fragment')
    except Exception as e:
        st.toast('Cleared')
        
def select_column(configuration: dict, column: str):
    configuration["log"]["columns"].append(column)
    st.rerun(scope="fragment")

def clear_all_columns(configuration: dict):
    """Clear all selected columns"""
    configuration["log"]["columns"] = []
    st.rerun(scope="fragment")
    
def log_column(configuration:dict, joined_df: pd.DataFrame):
    if not configuration.get("log", None):
        configuration["log"] = {}
    
    if not configuration["log"].get("columns", None):
        configuration["log"]["columns"] = []
    
    all_columns = copy.deepcopy(joined_df.columns.to_list())
    unselected_container,_ , selected_container = st.columns([0.45, 0.05,0.45])
    
    with unselected_container:
        render_available_columns(configuration, all_columns)
        
    with selected_container:
        render_selected_columns(configuration, all_columns)
        
    st.write("")
    st.write("")
    st.write("")    

def render_available_columns(configuration: dict, all_columns: list[str]):
    """Render the available columns section"""
    available_cols = [
        column for column in all_columns
        if column not in configuration["log"]["columns"]
    ]
    
    st.markdown("""
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
            <h5 style='margin: 0;'>Available Columns</h5>
            <span style='font-size: 0.9em; color: #666;'>
                {}/{} columns
            </span>
        </div>
    """.format(len(available_cols), len(all_columns)), unsafe_allow_html=True)
    
    st.divider()
    st.text_input(label="", placeholder="Search and click enter",
                    label_visibility="collapsed", key="search_column")
    st.divider()
    
    available_cols = [
        column for column in available_cols
        if st.session_state.search_column.lower() in str(column).lower()
    ]
    
    if available_cols:
        for column in available_cols:
            if st.checkbox(column, key=f"avail_{column}"):
                select_column(configuration, column)
    else:
        st.info("No available column.")
            
            
def render_selected_columns(configuration: dict, all_columns: list[str]):
    """Render the selected columns section"""
    st.markdown("""
        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
            <h5 style='margin: 0;'>Selected Columns</h5>
            <span style='font-size: 0.9em; color: #666;'>
                {}/{} columns
            </span>
        </div>
    """.format(len(configuration["log"]["columns"]), len(all_columns)), unsafe_allow_html=True)
    st.divider()
    
    if configuration["log"]["columns"]:
        for idx, column in enumerate(configuration["log"]["columns"]):
            if st.checkbox(column, key=f"selected_{column}"):
                unselect_column(configuration, idx)
                
        if st.button("Clear All Columns", key="clear_all_cols_btn", use_container_width=True, icon=":material/close:"):
            clear_all_columns(configuration)
    else:
        st.info("No column selected.")
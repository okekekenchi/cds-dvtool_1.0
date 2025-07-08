import streamlit as st
from utils import authenticated, alert
from components.side_nav import side_nav
from loader.config_loader import config
from loader.css_loader import load_css
import pandas as pd
import os
from io import BytesIO
from pathlib import Path
import hashlib


st.set_page_config(page_title="Project", page_icon=":material/folder:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/project.css')

st.markdown("""
        <style>
            .stTabs > div {
                width: -webkit-fill-available !important;
            }
            
            div[data-testid="stExpanderDetails"] {
                min-height: 200px;
            }
            
        </style>
    """, unsafe_allow_html=True)

join_types = {
    "left":"Left Join",
    "a_left":"Left Anti-Join",
    "right":"Right Join",
    "a_right":"Right Anti-Join",
    "inner":"Inner Join",
    "a_inner":"Inner Anti-Join",
    "outer":"Outer Join"
}

def init_session_var():
    if 'project' not in st.session_state:
        st.session_state.project = {
            'project_name': None,
            'workbook': None,
            'sheets': {},
            'project_name': '',
            'workbook_hash': None,
            'joined_sheets': [],
        }
    
    if 'validation' not in st.session_state:
        st.session_state.validation = {
            'sheets': [],
            'joins': []
        }
    

# Cache functions with hash-based invalidation
@st.cache_resource
def load_workbook(file_path: BytesIO, file_hash: str) -> pd.ExcelFile:
    """Load workbook from bytes"""
    try:
        return pd.ExcelFile(BytesIO(file_path))
    except Exception as e:
        st.error(f"Error loading workbook: {str(e)}")
        st.stop()

@st.cache_data
def load_sheet(_excel_file, sheet_name):
    """Load individual sheet from cached workbook"""
    try:
        return pd.read_excel(_excel_file, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Error loading sheet '{sheet_name}': {str(e)}")
        return pd.DataFrame()

def get_file_hash(uploaded_file):
    """
    Generate hash for file content to detect changes
    """
    return hashlib.md5(uploaded_file.getvalue()).hexdigest()

def get_common_columns(sheet_name1: str, sheet_name2: str) -> list[str]:
    """
    Get matching column names between two sheets stored in session state.

    Args:
        sheet_name1: The name of the first sheet.
        sheet_name2: The name of the second sheet.

    Returns:
        A list of column names common to both sheets. Returns an empty list
        if no common columns are found or if either sheet name is not found
        in the session state.
    """
    sheets = st.session_state.project['sheets']
    
    if sheet_name1 in sheets and sheet_name2 in sheets:
        cols1 = set(sheets[sheet_name1].columns)
        cols2 = set(sheets[sheet_name2].columns)
        return list(cols1 & cols2)
    else:
        return []

def print_matching_columns(join:dict):
    """
    Retrieves common columns between two tables specified in the 'join' dictionary
    and displays them in the Streamlit app.

    If no common columns are found, a warning message is displayed.

    Args:
        join: A dictionary expected to contain 'left_table' and 'right_table' keys,
              whose values are the names of the tables to compare.
    """
    if 'left_table' not in join or 'right_table' not in join:
        st.error("Error: 'join' dictionary must contain 'left_table' and 'right_table' keys.")
        return
    
    matching_columns = get_common_columns(join['left_table'], join['right_table'])
    if not matching_columns:
        st.warning('There are no matching columns found in both tables')
    else:
        formatted_columns  = ", ".join(item.strip() for item in matching_columns)
        st.write(f"**Matching columns includes:** {formatted_columns }")
        
def select_sheets():
    """Renders UI for selecting and managing sheets for validation.
    
    Allows users to:
    - Select sheets from available workbook sheets
    - Add selected sheets to validation checklist
    - Remove sheets from validation checklist
    
    Returns:
        None - updates session state directly
    """
    col1, col2, _ = st.columns([0.5,0.2,0.3])
    sheet_options = list(st.session_state.project['sheets'].keys())
    selected_options = st.session_state.validation['sheets']
    
    with col1:
        new_sheets = st.multiselect(
                        "Select sheets/tables to validate",
                        options=[ option for option in sheet_options if option not in selected_options ],
                        default=None,
                        help="Select which sheets you want to include in validation"
                     )
    with col2:
        if st.button("Add", key="add_sheets", icon=":material/add:") and new_sheets:
            for sheet in new_sheets:
                if sheet not in st.session_state.validation['sheets']:
                    st.session_state.validation['sheets'].append(sheet)
            st.rerun()
    
    if not st.session_state.validation['sheets']:
        st.write("Your sheet list is empty!")
    else:
        for i, sheet in enumerate(st.session_state.validation['sheets']):
            st.divider()
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            
            with col1:
                st.write(f"{i+1}. {sheet}")
            with col2:
                if st.button(f"View", key=f"preview_sheet_{i}", icon=":material/visibility:"):
                    preview_sheet(st.session_state.project['sheets'][sheet])
            with col3:
                if st.button(f"Delete", key=f"delete_sheet_{i}", icon=":material/delete:"):
                    del st.session_state.validation['sheets'][i]
                    st.rerun()
        
@st.dialog('Preview Table', width="large")
def preview_sheet(df):
    st.dataframe(df)
    
def join_sheets():
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
                                    "Left Table",
                                    options=st.session_state.validation['sheets'],
                                    index=None,
                                    help="Select which sheets you want to include in validation"
                                )
    with col2:
        new_join['join_type'] = st.selectbox(
                                    "Join Type",
                                    options=join_types.keys(),
                                    index=1,
                                    help="Select which join type to implement",
                                    format_func=lambda x: join_types[x]
                                )
    with col3:
        new_join['right_table'] = st.selectbox(
                                        "Right Table",
                                        options=st.session_state.validation['sheets'],
                                        index=None,
                                        help="Select which sheets you want to include in validation"
                                    )                    
    with col4:
        if st.button("Add", key="add_joins", icon=":material/add:"):
            if not new_join['left_table'] or not new_join['right_table'] or not new_join['join_type']:
                alert("Fill all required fields")
                return
            
            if new_join['left_table'] == new_join['right_table']:
                alert("You have selected the same option for both left and right tables")
                return
            
            if new_join not in st.session_state.validation['joins']:
                st.session_state.validation['joins'].append(new_join)
                st.rerun()
            else:
                alert("You have already joined these sheets")
    
    print_matching_columns(new_join)
        
    if not st.session_state.validation['joins']:
        st.write("Your join list is empty!")
    else:
        # View join list
        for idx, join in enumerate(st.session_state.validation['joins']):
            st.divider()
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                df = pd.DataFrame([join])
                if 'on_cols' in df:
                    df = df.drop(columns=["on_cols"])  # Remove column
                
                df['join_type'] = df['join_type'].map(join_types)
                df.columns = [ f"**{column.replace('_', " ").capitalize()}**" for column in df.columns]
                st.table(df)
            
            with col2:
                if st.button("Conditions", key=f"join_conditions_{idx}"):
                    if join['left_table'] and join['right_table'] and join['join_type']:
                        join_conditions(idx, join)
                    else:
                        alert("Fill all required fields")
                
                if st.button(f"Delete", key=f"delete_join_conditions_{idx}", icon=":material/delete:"):
                    del st.session_state.validation['joins'][idx]
                    st.rerun()

def table_columns(table_name: str):
    return list(st.session_state.project['sheets'][table_name].columns)

@st.dialog("Join Conditions", width='large')
def join_conditions(idx, join):
    """multi-column join"""
    col1, col2, col3, _ = st.columns([0.15, 0.3, 0.3, 0.25])
    
    with col1:
        st.write('', '', '')
        st.write('', '', '')
        f"Left table: **{join['left_table']}**"
    with col2:
        join_type = st.selectbox(label='',
                        placeholder="Join Type",
                        options=join_types.keys(),
                        index=list(join_types.keys()).index(join['join_type']),
                        help="Select which join type to implement",
                        format_func=lambda x: join_types[x],
                        key="join_type_condition"
                    )
    with col3:
        st.write('', '', '')
        st.write('', '', '')
        f"Right table: **{join['right_table']}**"
        
    st.session_state.validation['joins'][idx]['join_type'] = join_type
                
    col1, col2, col3 = st.columns([0.3, 0.3, 0.16])
    
    if 'on_cols' not in st.session_state.validation['joins'][idx]:
        st.session_state.validation['joins'][idx]['on_cols'] = []
       
    on_col = {}
    
    with col1:
        on_col['left_column'] = st.selectbox(
                                    "Left Column",
                                    options=table_columns(join['left_table']),
                                    index=None,
                                    help="Select which sheets you want to include in validation"
                                )
    with col2:
        on_col['right_column'] = st.selectbox(
                                    "Right Column",
                                    options=table_columns(join['right_table']),
                                    index=None,
                                    help="Select the column you want to join."
                                )
    with col3:
        st.write('')
        st.write('')
        if st.button("Add", key="add_join_columns", icon=":material/add:") and on_col:
            if on_col['right_column'] and on_col['left_column']:
                if on_col not in st.session_state.validation['joins'][idx]['on_cols']:
                    st.session_state.validation['joins'][idx]['on_cols'].append(on_col)
                else:
                    st.warning("Columns have already been joined")
            else:
                st.warning('Fill all required fields.')
    
    if not st.session_state.validation['joins'][idx]['on_cols']:
        st.write("Your join condition list is empty!")
    else:
        for i, on_col in enumerate(st.session_state.validation['joins'][idx]['on_cols']):
            st.divider()
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                col4, col5, col6 = st.columns([0.4,0.2,0.3])
                with col4:
                    st.write(f"**{join['left_table']} . {on_col['left_column']}**")
                with col5:
                    st.write("**=**")
                with col6:
                    st.write(f"**{join['right_table']} . {on_col['right_column']}**")
            with col2:
                if st.button(f"Delete", key=f"delete_join_condition_{i}", icon=":material/delete:"):
                    del st.session_state.validation['joins'][idx]['on_cols'][i]
                    
    _, col1, col2 = st.columns([0.6,0.2,0.2])
    with col1:
        if st.session_state.validation['joins'][idx]['on_cols']:
            if st.button("Save"):
                st.rerun()
    with col2:
        if st.button("Cancel"):
            st.rerun()
            
def get_selected_sheets() -> dict:
    all_sheets = st.session_state.project['sheets']
    selected_sheet_names = st.session_state.validation['sheets']
    return { name: all_sheets.get(name) for name in selected_sheet_names }

def add_prefix_to_columns(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    return df.rename(columns={col: f"{prefix}.{col}" for col in df.columns})

def perform_joins(joins) -> pd.DataFrame:
    """
    Performs a sequence of Pandas DataFrame joins based on a list of join specifications.

    Args:
        joins: A list of dictionaries, where each dictionary defines a join operation.
               Each join dict is expected to have:
               - 'left_table': str (name of the left table/DataFrame)
               - 'right_table': str (name of the right table/DataFrame)
               - 'join_type': str (e.g., 'inner', 'left', 'right', 'outer')
               - 'on_cols': list of dicts, each with 'left_column' and 'right_column'

    Returns:
        A pandas DataFrame representing the result of the chained joins, or None
        if no joins are specified, an invalid join definition is found,
        or a required sheet is missing.
    """
    result = None
    selected_sheets = get_selected_sheets()
    
    for i, join in enumerate(joins):
        if join["left_table"] and join["right_table"] and "on_cols" in join:
            left_df = result if result is not None and join['left_table'] == result.name else selected_sheets[join["left_table"]]
            right_df = selected_sheets[join["right_table"]]
            how = join["join_type"]
            is_anti_join = join["join_type"][:2] == "a_"
            
            left_on = [ col["left_column"] for col in join["on_cols"] ]
            right_on = [ col["right_column"] for col in join["on_cols"] ]
            
            if left_on and right_on:
                try:
                    result = pd.merge(left_df,
                                    right_df[[right_on[0], right_on[1]]].drop_duplicates(),
                                    left_on=left_on,
                                    right_on=right_on,
                                    how=(join["join_type"]).replace("a_", ""),
                                    indicator=is_anti_join
                                    )
                    
                    if is_anti_join:
                        result = result.query('_merge == "left_only"').drop('_merge', axis=1)
                        
                except Exception as e:
                    st.error(f"An error occurred during join {i+1} ('{join['left_table']}' {how} '{join["right_table"]}'): {e}")
                    return None
            else:
                return None
        else:
            return None
    return result

def view_output():
    selected_sheets = get_selected_sheets()
    result = None
    
    if selected_sheets:
        joins = st.session_state.validation['joins']
        merged_df = perform_joins(joins) if joins else next(iter(selected_sheets.values())) # returns the first item if no join exists
        merged_df
        
    else:
        st.info("No sheets seleted.")

@authenticated
def main():
    st.session_state.current_page = "pages/4_project.py"
    side_nav()
    st.title("New Project")
    init_session_var()
    
    with st.expander("📂 Project Setup", expanded=True):
        col1, col2 = st.columns([0.55, 0.45])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Select Workbook (Excel File)",
                type=["xlsx", "xls"],
                help="Upload an Excel workbook containing your data sheets"
            )
            
            st.markdown("""
                <style>
                    button {
                        max-width: 150px;
                    }
                </style>
            """, unsafe_allow_html=True)
            
            if uploaded_file:
                current_hash = get_file_hash(uploaded_file)
                
                if st.session_state.project['workbook_hash'] != current_hash:
                    try:
                        # Load directly from bytes without temp file
                        excel_file = load_workbook(uploaded_file.getvalue(), current_hash)
                        sheets = { sheet: load_sheet(excel_file, sheet_name=sheet) 
                                    for sheet in excel_file.sheet_names}
                        
                        st.session_state.project = {
                            'workbook': excel_file,
                            'sheets': sheets,
                            'project_name': uploaded_file.name.split('.')[0],
                            'workbook_hash': current_hash,
                            'joined_sheets': {}
                        }
                    except Exception as e:
                        st.error(f"Error processing workbook: {str(e)}")
                        st.stop()
        
        with col2:
            if uploaded_file:
                project_name = st.text_input(
                    "Project Name",
                    value=st.session_state.project['project_name'],
                    help="Automatically populated from workbook name"
                )
                st.session_state.project['project_name'] = project_name
                
                with st.expander("Workbook Info"):
                    st.write(f"**File Name:** {uploaded_file.name}")
                    st.write(f"**Sheets in Workbook:** {len(st.session_state.project['sheets'])}")
    
    if uploaded_file and st.session_state.project.get('sheets'):
        with st.expander("✅ Validation", expanded=True):
            sheet_tab, join_tab, column_tab, output_tab = st.tabs(["sheets", "Joins", "Columns", "Output"], width='stretch')

            with sheet_tab:
                select_sheets()
                                
            with join_tab:
                join_sheets()
                
            with column_tab:
                st.write("Column queries")
                
            with output_tab:
                view_output()
                            

if __name__ == "__main__":
    main()
    
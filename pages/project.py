import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

# 🔁 Reload util and components before importing anything from them
reload_package("util")
reload_package("components")

# Now import everything
import streamlit as st
from utils import get_model_class, system_tables
from util.auth_utils import authenticated
from components.side_nav import side_nav
from database.database import get_db
import json
from loader.css_loader import load_css
import pandas as pd
from io import BytesIO
import hashlib


st.set_page_config(page_title="Project", page_icon=":material/folder:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/project.css')

# st.markdown("""
#         <style>
            
#         </style>
#     """, unsafe_allow_html=True)


def init_session_var():
    if 'project' not in st.session_state:
        st.session_state.project = {
            'project_name': None,
            'workbook': None,
            'sheets': {},
            'workbook_hash': None,
            'joined_sheets': [],
        }
    
    if 'validation' not in st.session_state:
        st.session_state.validation = {
            'sheets': [],
            'joins': [],
            'conditions': []
        }
    
    if 'joined_df' not in st.session_state:
        st.session_state.joined_df = pd.DataFrame()
    if 'queried_df' not in st.session_state:
        st.session_state.queried_df = pd.DataFrame()
    if 'list_type' not in st.session_state:
        st.session_state.list_type = None
    if 'list_source_str' not in st.session_state:
        st.session_state.list_source_str = None
    
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
    """
    Load individual sheet from cached workbook
    Elimimate columnms with whitespace/empty headers
    """
    try:    
        df = pd.read_excel(_excel_file, sheet_name=sheet_name)
        columns_to_drop = df.columns[df.columns.str.strip() == '']

        return df if columns_to_drop.empty else df.drop(columns=columns_to_drop)
    except Exception as e:
        st.error(f"Error loading sheet '{sheet_name}': {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_table(table_name):
    """
    Load individual master table
    """
    try:    
       with get_db() as db:
            model = get_model_class(table_name)
            return model.all_df(db)
    except Exception as e:
        st.error(f"Error loading table '{table_name}': {str(e)}")
        return pd.DataFrame()

def get_file_hash(uploaded_file):
    """
    Generate hash for file content to detect changes
    """
    return hashlib.md5(uploaded_file.getvalue()).hexdigest()

@authenticated
def main():
    st.title("New Project")
    st.session_state.current_page = "pages/project.py"
    side_nav()
    init_session_var()
    st.markdown("<p style='margin-top:28px;'></p>", unsafe_allow_html=True)
    
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
                    button { max-width: 150px; }
                </style>
            """, unsafe_allow_html=True)
            
            if uploaded_file:
                current_hash = get_file_hash(uploaded_file)
                                
                if st.session_state.project['workbook_hash'] != current_hash:
                    
                    st.session_state.clear()
                    init_session_var()
                    
                    try:
                        # Load directly from bytes without temp file
                        excel_file = load_workbook(uploaded_file.getvalue(), current_hash)
                        with open("config/master.json", "r") as file:
                            table_names = (json.load(file)).keys()
                        
                        if excel_file.sheet_names:
                            sheets = { name: load_sheet(excel_file, sheet_name=name) 
                                        for name in excel_file.sheet_names }
                        else: st.warning("Unable to load sheets try again.")
                    except Exception as e:
                        st.error(f"Error processing workbook: {str(e)}")
                        st.stop()
                        
                    if table_names:
                        system_tables.append('validation_checklist')
                        tables = { name : load_table(name)
                                    for name in table_names if name not in system_tables }
                    else: st.warning("Unable to load master tables contact admin.")
                        
                    st.session_state.project = {
                        'workbook': excel_file,
                        'sheets': sheets | tables,
                        'project_name': uploaded_file.name.split('.')[0],
                        'workbook_hash': current_hash,
                        'joined_sheets': {}
                    }
        
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
                    st.write(f"**Sheets in Workbook:** {len(st.session_state.project['sheets']) - 8}")
    
    if uploaded_file and st.session_state.project.get('sheets'):
        st.info('uploaded')
        
if __name__ == "__main__":
    main()
    
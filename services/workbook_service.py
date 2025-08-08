import streamlit as st
from utils import get_model_class
from database.database import get_db
from util.datatable import get_table_names
import pandas as pd
from io import BytesIO
import hashlib

# Cache functions with hash-based invalidation
# @st.cache_resource
def load_workbook(file_path: BytesIO, file_hash: str) -> pd.ExcelFile:
    """Load workbook from bytes"""
    try:
        return pd.ExcelFile(BytesIO(file_path))
    except Exception as e:
        st.error(f"Error loading workbook: {str(e)}")
        st.stop()

# @st.cache_data
def load_sheet(_excel_file, sheet_name):
    """
    Load individual sheet from cached workbook
    Elimimate columnms with whitespace/empty headers
    """
    try:    
        df = pd.read_excel(
            _excel_file,
            sheet_name=sheet_name,
            na_values=None,
            dtype=str
        )
        columns_to_drop = df.columns[df.columns.str.strip() == '']

        return df if columns_to_drop.empty else df.drop(columns=columns_to_drop)
    except Exception as e:
        st.error(f"Error loading sheet '{sheet_name}': {str(e)}")
        return pd.DataFrame()

# @st.cache_data(ttl=300)
def load_table(table_name:str) -> pd.DataFrame:
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
    try:
        return hashlib.md5(uploaded_file.getvalue()).hexdigest()
    except Exception as e:
        st.warning("Could not load file")

def get_sheet_columns(sheets:dict, sheet_name: str):
    if sheet_name in sheets:
        return list(sheets[sheet_name].columns)
    else:
        return []
    
def load_data(file_hash):
    try:
        excel_file = load_workbook(st.session_state.uploaded_file.getvalue(), file_hash)
        
        if excel_file.sheet_names:
            sheets = { name: load_sheet(excel_file, sheet_name=name) 
                        for name in excel_file.sheet_names }
        else:
            st.badge("Unable to load sheets from workbook try again.", color='orange')

        exempt_tables = ['validation_checklists', 'tags']
        table_names = [name[:-1] for name in get_table_names() if name not in exempt_tables]
        
        if table_names:
            tables = { name : load_table(name).astype(str) for name in table_names }
        else: st.warning("Unable to load master tables contact admin.")
        
        return excel_file, sheets, tables
    except Exception as e:
        st.warning(f"Could not load workbook.")
        st.stop()
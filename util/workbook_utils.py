import streamlit as st
from utils import get_model_class
from database.database import get_db
import pandas as pd
from io import BytesIO
import hashlib

        

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
        df = pd.read_excel(_excel_file, sheet_name=sheet_name,na_values=None)
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
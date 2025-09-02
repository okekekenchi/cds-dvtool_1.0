import time
import pandas as pd
import streamlit as st
from database.database import engine
from util.datatable import get_table_data

def load_data_with_retry(table: str, query: str="", max_retries: int = 3, **filters) -> pd.DataFrame:
    """Helper function with retry logic for database operations"""
    for attempt in range(max_retries):
        try:
            df = get_table_data(table, query, **filters)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(1 * (attempt + 1))
    
    if df.empty:
        st.warning("No records found")
        return pd.DataFrame()
    
    user_map = get_user_mapping()
    df['created_by'] = df['created_by'].map(lambda x: user_map.get(x, "System"))
    return df

@st.cache_data(ttl=120)
def get_user_mapping() -> dict:
    """Cached user data lookup"""
    users = pd.read_sql("SELECT id, full_name FROM users", engine)
    return {
        **users.set_index('id')['full_name'].to_dict(),
        st.session_state.user_id: "Me"
    }
    
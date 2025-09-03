import sqlite3
import streamlit as st
import importlib
from models.base import BaseModel
from datetime import datetime, timezone
from loader.config_loader import config

system_tables = ["users","sessions","project_logs","validation_checklists"]
system_fields = ["created_by", "created_at", "updated_at"]
bool_fields = ["active"]
textarea_fields = ["mb_desc", "desc", "description"]
required_fields = [
    "task_type_id","task_type","meas_base","mb_desc","lsaconxb_char_length","lcnindxb",
    "taskcdca_2nd_char","task_code_interval","task_code_interval_desc","bh_freq","bh_freq_mb",
    "task_code","desc_1","desc_2","smrcodhg","",""
]

# Session management
def clear_db():
    conn = sqlite3.connect(config('database.name'), check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("DELETE TABLE users")
    cursor.execute("DELETE TABLE session")
    
    conn.commit()
    conn.close()


def get_model_class(model_name) -> BaseModel:
    module = importlib.import_module(f"models.{model_name}")
    # Assumes class name matches module name in CamelCase
    class_name = ''.join([part.capitalize() for part in model_name.split('_')])
    return getattr(module, class_name)
        
@st.dialog("Info", dismissible=True, on_dismiss="ignore")
def alert(msg):
    st.warning(msg)
    
def format_datetime(timestamp: str):
    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
    dt_utc = dt.replace(tzinfo=timezone.utc)  # Mark as UTC time
    dt_local = dt_utc.astimezone()  # Convert to local timezon
    return dt_local.strftime("%B %d, %Y at %I:%M %p")
 

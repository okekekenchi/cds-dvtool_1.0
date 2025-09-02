import json
import time
import copy
import pandas as pd
import streamlit as st
from utils import alert
from typing import Final
from loader.css_loader import load_css
from util.datatable import delete_record
from sqlalchemy.exc import IntegrityError
from database.database import get_db
from models.validation_checklist import ValidationChecklist
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from services.checklist_service import load_data_with_retry

st.set_page_config(page_title="Masters", page_icon=":material/settings:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/project.css')

TABLE_NAME: Final[str] = "validation_checklists"
STATUS_OPTIONS: Final[dict[int, str]] = {1: "Active", 0: "Inactive"}
COLUMNS_TO_HIDE: Final[list[str]] = ["id", "active", "config", "tags"]

checklist = {
    'code': '',
    'name': '',
    'description': '',
    'tags': [],
    'workbook': None,
    'sheets': {},
    'active': True,
    'config': {}
}

config = {
    'sheets': [],
    'joins': [],
    'col_operations': [],
    'conditions': []
}

@st.dialog("Clone Checklist")
def clone_checklist_form(record_id):    
    st.write(f"Clone checklist with code: **{st.session_state.selected_checklist.get('code')}**")
    
    st.text_input("Code *", help="Code must be Unique",
                    key="clone_checklist_code", max_chars=15)
    
    st.text_input("Name *", help="Name must be Unique",
                    key="clone_checklist_name", max_chars=100)
        
    col1, col2 = st.columns([1,1], vertical_alignment="center")
    cloned = False
    error_message = None
    
    with col1:
        if st.button("Clone Record", key="confirm_clone_checklist", use_container_width=True):
            if not st.session_state.clone_checklist_code or not st.session_state.clone_checklist_name:
                error_message = "Fill all required fields."
            else:        
                try:
                    with get_db() as db:
                        model = ValidationChecklist.find(db, record_id)
                        model.clone(db, attr={
                                        'code': st.session_state.clone_checklist_code,
                                        'name': st.session_state.clone_checklist_name,
                                        'created_by': st.session_state.user_id
                                    })
                    cloned = True
                except IntegrityError:
                    error_message = f"The 'Code' and 'Name' provided must be unique"
                except Exception as e:
                    error_message = f"Error cloning record: {e}"
    
    with col2:
        if st.button("Cancel", key="cancel_clone_checklist", use_container_width=True):
            st.session_state.selected_checklist = {}
            st.rerun()

    if error_message:
        st.warning(error_message)
        return
    
    if cloned:
        st.success("Record cloned successfully!")
        st.session_state.selected_checklist = {}
        time.sleep(2)
        st.rerun()
        
def is_system_record():
    if st.session_state.selected_checklist:
        return st.session_state.selected_checklist.get("created_by") == "System"
    else:
        return False
        
@st.dialog("Delete Checklist")
def delete_checklist_form(record_id):
    record_code = st.session_state.selected_checklist.get("code")

    st.warning(f"Are you sure you want to delete this record: {record_code}?")
    
    col1, col2 = st.columns([2, 1], vertical_alignment='center', use_container_width=True)
    deleted = False
    with col1:
        if st.button("Delete", key="confirm_delete_checklist"):
            try:
                delete_record(TABLE_NAME, record_id)
                deleted = True
            except Exception as e:
                st.error(f"Error deleting record: {e}")
    with col2:
        if st.button("Cancel", key="cancel_delete_checklist"):
            st.session_state.selected_checklist = {}
            st.rerun()
            
    if deleted:
        st.success("Record deleted successfully!")
        st.session_state.selected_checklist = {}
        time.sleep(2)
        st.rerun()
    
def handle_selection_change(selected_rows: list[dict]):
    if 'selected_checklist' not in st.session_state:
        st.session_state.selected_checklist = {}
        
    # Convert to list of dicts if it's a DataFrame
    if hasattr(selected_rows, 'to_dict'):
        selected_rows = selected_rows.to_dict('records')

    # Now safely check if we have selected rows
    if isinstance(selected_rows, list) and len(selected_rows) > 0:
        
        selected_checklist = selected_rows[0]
        selected_checklist.update({
            "tags": json.loads(selected_checklist.get('tags')),
            "config": json.loads(selected_checklist.get('config'))
        })
        
        if st.session_state.selected_checklist.get('id') != selected_checklist['id']:
            st.session_state.selected_checklist = selected_checklist
            st.session_state.reset_form = True # Reset form for update
            st.rerun()
    else:
        if st.session_state.selected_checklist.get("id", None) != None:
            if st.session_state.selected_checklist.get('id'):
                st.session_state.reset_form = True # Reset form for create
                st.session_state.config = copy.deepcopy(config)
                st.session_state.selected_checklist = copy.deepcopy(checklist)
            st.rerun()
 

def view_checklist():    
    col1, _, col2 = st.columns([0.45, 0.37, 0.18], vertical_alignment="center")
    
    if 'active_records' not in st.session_state:
        st.session_state.active_records = 1
    
    with col1:
        st.text_input(
            "", label_visibility="collapsed",
            placeholder="Type to search...",
            key="checklist_search_query",
            help="Search across all columns"
        )
    with col2:
        st.segmented_control(
            "", options=STATUS_OPTIONS.keys(),
            format_func=lambda option: STATUS_OPTIONS[option],
            label_visibility="collapsed",
            key="active_records",
            width="stretch"
        )
    
    st.divider()

    # Main content area
    action_placeholder = st.empty()
    
    filters = { "active": st.session_state.active_records }
    filters = filters if st.session_state.active_records in [0,1] else {}
    
    try:
        st.session_state.data = load_data_with_retry(TABLE_NAME, st.session_state.checklist_search_query,
                                 max_retries=3, **filters)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()
    
    # Configure tables
    gb = GridOptionsBuilder.from_dataframe(st.session_state.data)
    gb.configure_pagination(paginationAutoPageSize=False)
    gb.configure_default_column(editable=False, filterable=False, sortable=True, resizable=True, width=250)
    gb.configure_grid_options(domLayout='normal')
    gb.configure_column(field="created_by", header_name="Created by")
    gb.configure_column(field="created_by", header_name="Created by")
    gb.configure_column(field="created_at", header_name="Created at", valueFormatter="new Date(data.created_at).toLocaleString()")
    gb.configure_column(field="updated_at", header_name="Updated at", valueFormatter="new Date(data.updated_at).toLocaleString()")
    gb.configure_selection(selection_mode='single', use_checkbox=True)
    
    for column in COLUMNS_TO_HIDE:
        if column in st.session_state.data:
            gb.configure_column(field=column, hide=True)
    
    grid_response = AgGrid(
        st.session_state.data,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme='streamlit',
        enable_enterprise_modules=True,
        sidebar=True,
        fit_columns_on_grid_load=True,
        key="checklist_datatable"
    )
    
    handle_selection_change(grid_response.get("selected_rows"))
    
    # # Show action buttons for selected row
    with action_placeholder.container():
        record_id = st.session_state.selected_checklist.get("id")
        if record_id:
            col1, _ = st.columns([2, 1], vertical_alignment="center")
            with col1:
                if st.button("Clone", icon=":material/content_copy:",
                             key="colne_checklist_dialog", help="Clone record"):
                    clone_checklist_form(record_id)
                
                if st.button("Delete", icon=":material/delete:", key="delete_checklist_dialog"):
                    if is_system_record():
                        alert("This is a **system record** - you cannot delete.")
                        return
                    delete_checklist_form(record_id)
        
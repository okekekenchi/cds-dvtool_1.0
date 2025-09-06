import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("components.checklist.configuration")
reload_package("services.workbook_service")

import copy
import streamlit as st
from utils import alert
from models.tag import Tag
from database.database import get_db
from sqlalchemy.exc import IntegrityError
from models.validation_checklist import ValidationChecklist
from services.checklist_service import load_data_with_retry
from components.checklist.configuration import configure_checklist
from services.workbook_service import load_data
from typing import Final

TABLE_NAME: Final[str] = "validation_checklists"

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

def init_session_var():   
    if 'checklist' not in st.session_state:
        st.session_state.checklist = copy.deepcopy(checklist)
    if 'config' not in st.session_state:
        st.session_state.config = copy.deepcopy(config)
    
    if 'reset_inputs' not in st.session_state:
        st.session_state.reset_inputs = False
    if 'list_type' not in st.session_state:
        st.session_state.list_type = None
    if 'list_source_str' not in st.session_state:
        st.session_state.list_source_str = None

def reset_inputs():
    st.session_state.checklist_code = None
    st.session_state.checklist_name = None
    st.session_state.checklist_description = None
    st.session_state.checklist_active = 1
    st.session_state.checklist_tags = []
    st.session_state.reset_inputs = False

def init_form():
    reset_form()
    reset_inputs()    

def load_tags():
    try:
        with get_db() as db:
            result = Tag.where(db, ["id","name"])
            if result is None:
                return []
            return list(result) if hasattr(result, '__iter__') else []
    except Exception as e:
        print(f"Error loading tags: {e}")
        return []
    
def form_inputs():
    if st.session_state.reset_inputs:
        reset_inputs()
        
    col11, col12 = st.columns([0.3, 0.7], vertical_alignment='center')
    with col11:
        st.session_state.checklist['code'] = st.text_input(
                                                "Checklist Code *", help="Must be Unique",
                                                key="checklist_code", max_chars=15)
    with col12:
        st.session_state.checklist['name'] = st.text_input(
                                                "Name *", help="Must be Unique",
                                                key="checklist_name", max_chars=100)
        
    st.session_state.checklist['description'] = st.text_area(
                                                    "Description *", height=70,
                                                    key="checklist_description", max_chars=200)
    
    col31, col32 = st.columns([0.8, 0.2], vertical_alignment='center')
    
    tags_options = { tag['id']: tag['name'] for tag in load_tags() }
    
    with col31:
        st.session_state.checklist['tags'] = st.multiselect(
                                                "Link Tags",
                                                key="checklist_tags",
                                                options=tags_options.keys(),
                                                format_func=lambda x: tags_options[x],
                                                help="Use tags for easy retrieval and categorization")
    with col32:
        st.write('')
        st.write('')
        st.session_state.checklist['active'] = st.checkbox("**Active**", key="checklist_active")

def form_action():
    _, col1, col2 = st.columns([1,1,1], vertical_alignment='center')
    with col1:
        if st.button("Save", key="save_checklist", icon=":material/save:", use_container_width=True):
            save_checklist()
    with col2:
        if st.button("Reset Form", key="reset_checklist_form",
                  icon=":material/refresh:", use_container_width=True):
            st.session_state.reset_inputs = True
            reset_form()
            st.rerun(scope='fragment')

def can_save() -> bool:
    if not st.session_state.uploaded_file:
        st.toast("No file uploaded")
        return False
        
    if (st.session_state.checklist['code'] and
        st.session_state.checklist['name'] and
        st.session_state.checklist['description']):
        return True
    else:
        st.toast("Fill all required fields.")
        return False

def save_checklist():
    try:
        if can_save():
            created = False
            checklist = copy.deepcopy(st.session_state.checklist)
            checklist['config'] = copy.deepcopy(st.session_state.config)
            checklist['created_by'] = st.session_state.user_id
            
            for key in ['workbook','sheets']:
                checklist.pop(key, None)
                
            with get_db() as db:
                created = ValidationChecklist.create(db, **checklist)
            
            if created:
                st.toast("Record created successfully", icon=":material/check_circle:")
                
                if 'data' in st.session_state:
                    del st.session_state.data
                    
                st.session_state.data = load_data_with_retry(
                    TABLE_NAME,
                    st.session_state.get('checklist_search_query', '')
                )
                
                st.rerun(scope='fragment')
            else:
                alert('Error: Could not create record')
    except IntegrityError:
        st.toast("The 'Code' and 'Name' provided must be unique")
    except Exception as e:
        st.toast(f"Error creating record: {e}")
        
def reset_form():
    st.session_state.update({ 
        "checklist": copy.deepcopy(checklist),
        "config": copy.deepcopy(config),
        "list_type": None,
        "list_source_str": None
    })
    
    st.session_state.reset_form = True
    
def upload_workbook():
    st.file_uploader(
        "Select Workbook (Excel File) *",
        type=["xlsx", "xls"], key="uploaded_file",
        help="Upload an Excel workbook containing your data sheets.",
    )
        
    if st.session_state.uploaded_file:
        file, sheets, tables = load_data(st.session_state.uploaded_file)
        sheets_and_tables = sheets | tables
        
        st.session_state.checklist.update({
            'workbook': file,
            'only_sheets': sheets,
            'sheets': sheets_and_tables,
            "list_type": None,
            "list_source_str": None
        })
    else:            
        st.warning("Select file to continue")
        
    return st.session_state.uploaded_file

@st.fragment
def create_checklist():
    init_session_var()
    
    if st.session_state.reset_form:
        init_form()
        st.session_state.reset_form = False
        
    col1, col2 = st.columns([0.5, 0.5], border=True, vertical_alignment='center')
        
    with col1:
        form_inputs()
        
    with col2:
        form_action()
            
        st.divider()
        
        workbook = upload_workbook()
    
    st.divider()
    
    if workbook and st.session_state.config:
       configure_checklist(st.session_state.config)
                
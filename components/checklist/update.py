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
from components.checklist.configuration import configure_checklist
from services.workbook_service import load_data

config = {
    'sheets': [],
    'joins': [],
    'col_operations': [],
    'conditions': []
}

def init_session_var():
    selected_checklist = copy.deepcopy(st.session_state.selected_checklist)
    
    if 'checklist' not in st.session_state:
        st.session_state.checklist = selected_checklist
    if 'config' not in st.session_state:
        st.session_state.config = selected_checklist.get('config')
        
    if 'reset_inputs' not in st.session_state:
        st.session_state.reset_inputs = False
    if 'list_type' not in st.session_state:
        st.session_state.list_type = None
    if 'list_source_str' not in st.session_state:
        st.session_state.list_source_str = None

def reset_inputs():
    selected_checklist = copy.deepcopy(st.session_state.selected_checklist)
    st.session_state.checklist_code = selected_checklist.get('code')
    st.session_state.checklist_name = selected_checklist.get('name')
    st.session_state.checklist_description = selected_checklist.get('description')
    st.session_state.checklist_active = selected_checklist.get('active')
    st.session_state.checklist_tags = selected_checklist.get('tags')
    st.session_state.reset_inputs = False

def init_form():
    reset_form()
    reset_inputs()

def load_tags():
    with get_db() as db:
        return Tag.where(db, ["id","name"])

def form_inputs():
    if st.session_state.reset_inputs:
        reset_inputs()
        
    col11, col12 = st.columns([0.3, 0.7], vertical_alignment='center')
    with col11:
        st.session_state.checklist['code'] = st.text_input(
                                                "Checklist Code *", help="Must be Unique",
                                                key="checklist_code", max_chars=15, disabled=True)
    with col12:
        st.session_state.checklist['name'] = st.text_input(
                                                "Name *", help="Must be Unique",
                                                key="checklist_name", max_chars=100)
        
    st.session_state.checklist['description'] = st.text_area(
                                                    "Description *", height=70,
                                                    key="checklist_description", max_chars=400)
    
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
    _, col1, col2 = st.columns([0.65,0.25,0.1], vertical_alignment='center')
    with col1:
        if st.button("Save", key="save_checklist", icon=":material/save:"):
            save_checklist()
    with col2:
        if st.button("", key="reset_checklist_form", icon=":material/refresh:", help="Reset form"):
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
            updated = False
            form_fields = [ 'id','name','description','tags','active' ]
            checklist = { key:st.session_state.checklist.get(key) for key in form_fields }
            checklist['config'] = st.session_state.config
            
            with get_db() as db:
                ValidationChecklist.update(db, st.session_state.checklist['id'], checklist)
                updated = True
            
            if updated:
                st.toast("Record Updated")
                st.rerun()
            else:
                alert('Error: Could not update record')
    except IntegrityError:
        st.toast(f"The 'Code' and 'Name' provided must be unique")
    except Exception as e:
        st.toast(f"Error updating record: {e}")

def reset_form():
    selected_checklist = copy.deepcopy(st.session_state.selected_checklist)
    st.session_state.update({
        "checklist": selected_checklist,
        "config": selected_checklist.get('config'),
        "list_type": None,
        "list_source_str": None
    })
    
    st.session_state.reset_form = False    

def upload_workbook():
    f_ = st.file_uploader(
        "Select Workbook (Excel File) *",
        type=["xlsx", "xls"], key="uploaded_file",
        help="Upload an Excel workbook containing your data sheets."
    )
    
    # st.markdown("<style>button { max-width:150px; }</style>", unsafe_allow_html=True)
    
    if st.session_state.uploaded_file:
        file, sheets, tables = load_data(st.session_state.uploaded_file)
        sheets_and_tables = sheets | tables
        
        st.session_state.update({
            "config": copy.deepcopy(st.session_state.selected_checklist.get('config'))
        })
        
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
def update_checklist():
    init_session_var()
    
    if st.session_state.reset_form:
        init_form()
        
    col1, col2 = st.columns([0.5, 0.5], border=True, vertical_alignment='center')
    
    with col1:
        form_inputs()
        
    with col2:
        form_action()
        
        st.divider()
        
        workbook = upload_workbook()
    
    st.divider()
    
    if workbook:
        configure_checklist(st.session_state.config)

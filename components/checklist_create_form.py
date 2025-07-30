# import importlib
# import sys

# def reload_package(package_name: str):
#     for name in list(sys.modules):
#         if name == package_name or name.startswith(f"{package_name}."):
#             importlib.reload(sys.modules[name])

# reload_package("components.checklist_configuration")
# reload_package("services.workbook_service")

import streamlit as st
from utils import alert
from models.tag import Tag
from database.database import get_db
from sqlalchemy.exc import IntegrityError
from models.validation_checklist import ValidationChecklist
from components.checklist_configuration import configure_checklist
from services.workbook_service import load_data, get_file_hash

checklist = {
    'code': '',
    'name': '',
    'description': '',
    'tags': [],
    'workbook': None,
    'sheets': {},
    'workbook_hash': None,
    'active': True,
    'config': {}
}

config = {
    'sheets': [],
    'joins': [],
    'conditions': []
}

def init_session_var():
    if 'checklist' not in st.session_state:
        st.session_state.checklist = checklist
    if 'config' not in st.session_state:
        st.session_state.config = config
    
    if 'list_type' not in st.session_state:
        st.session_state.list_type = None
    if 'list_source_str' not in st.session_state:
        st.session_state.list_source_str = None

def init_form():
    st.session_state.checklist_code = None
    st.session_state.checklist_name = None
    st.session_state.checklist_description = None
    st.session_state.checklist_tags = []
    st.session_state.checklist_active = True

def load_tags():
    with get_db() as db:
        return Tag.where(db, ["id","name"])
    
def form_fields():        
    col11, col12 = st.columns([0.3, 0.7])
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
    _, col1, col2 = st.columns([0.5,0.35,0.1], vertical_alignment='center')
    with col1:
        if st.button("Save", key="save_checklist", icon=":material/save:"):
            save_checklist()
    with col2:
        if st.button("", key="reset_checklist_form", icon=":material/refresh:", help="Reset form"):
            reset_form()

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
            checklist = st.session_state.checklist
            checklist['config'] = st.session_state.config
            checklist['created_by'] = st.session_state.user_id
            
            for key in ['workbook','sheets','workbook_hash']:
                checklist.pop(key, None)
                
            with get_db() as db:
                created = ValidationChecklist.create(db, **checklist)
            
            if created:
                st.toast("Record created successfully")
                reset_form()
            else:
                alert('Error: Could not create record')
    except IntegrityError:
        st.toast("The 'Code' and 'Name' provided must be unique")
    except Exception as e:
        st.toast(f"Error creating record: {e}")
        
def reset_form():
    st.session_state.update({ 
        "checklist": checklist,
        "config": config,
        "list_type": None,
        "list_source_str": None
    })
    
    st.session_state.reset_form = True
    st.rerun()

def upload_workbook():
    st.file_uploader(
        "Select Workbook (Excel File) *",
        type=["xlsx", "xls"], key="uploaded_file",
        help="Upload an Excel workbook containing your data sheets.",
    )
    
    st.markdown("<style>button { max-width:150px; }</style>", unsafe_allow_html=True)
    
    if st.session_state.uploaded_file:
        current_file_hash = get_file_hash(st.session_state.uploaded_file)
                
        if st.session_state.checklist.get("workbook_hash", None) != current_file_hash:
            file, sheets, tables = load_data(current_file_hash)
            
            st.session_state.checklist.update({
                'workbook': file,
                'only_sheets': sheets,
                'sheets': sheets | tables,
                'workbook_hash': current_file_hash,
                # "config": config,
                "list_type": None,
                "list_source_str": None
            })
        
    return st.session_state.uploaded_file
    
def checklist_create_form():
    init_session_var()
    
    if st.session_state.reset_form:
        init_form()
        st.session_state.reset_form = False
        
    col1, col2 = st.columns([0.5, 0.5], border=True)
        
    with col1:
        form_fields()
        
    with col2:
        form_action()
            
        st.divider()
        
        workbook = upload_workbook()
    
    st.divider()
    
    if workbook:
       configure_checklist()
                
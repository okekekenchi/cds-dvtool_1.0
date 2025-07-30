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

config = {
    'sheets': [],
    'joins': [],
    'conditions': []
}

def init_session_var():
    if 'checklist' not in st.session_state:
        st.session_state.checklist = st.session_state.selected_checklist
    if 'config' not in st.session_state:
        st.session_state.config = st.session_state.selected_checklist.get('config')
        
    if 'list_type' not in st.session_state:
        st.session_state.list_type = None
    if 'list_source_str' not in st.session_state:
        st.session_state.list_source_str = None

def init_form():
    st.session_state.checklist_code = st.session_state.selected_checklist.get('code')
    st.session_state.checklist_name = st.session_state.selected_checklist.get('name')
    st.session_state.checklist_description = st.session_state.selected_checklist.get('description')
    st.session_state.checklist_active = st.session_state.selected_checklist.get('active')
    st.session_state.checklist_tags = st.session_state.selected_checklist.get('tags')
    
    st.session_state.update({
        "checklist": st.session_state.selected_checklist,
        "config": st.session_state.selected_checklist.get('config'),
        "list_type": None,
        "list_source_str": None
    })

def load_tags():
    with get_db() as db:
        return Tag.where(db, ["id","name"])

def form_fields():        
    col11, col12 = st.columns([0.3, 0.7])
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
            updated = False
            checklist = { key:st.session_state.checklist.get(key) for key in ['id','code','name','description','tags','active']}
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
    
def get_selected_sheets(all_sheets: dict) -> dict:
    selected_sheet_names = st.session_state.config['sheets']
    return { name: all_sheets.get(name) for name in selected_sheet_names }

def reset_form():
    st.session_state.update({
        "checklist": st.session_state.selected_checklist,
        "config": st.session_state.selected_checklist.get('config'),
        "list_type": None,
        "list_source_str": None
    })
    
    st.session_state.reset_form = False
    st.rerun()

def selected_sheets_and_columns_are_present_in_file(sheets:dict):
    config_db = st.session_state.config
    columns_across_sheets = []

    if config_db['sheets']:
        for sheet in config_db['sheets']:
            if sheet not in sheets:
                st.badge(f"**{sheet}** sheet is missing but required by the query", color='orange')
                st.stop()
            else:
                columns_across_sheets.extend(list(sheets[sheet].columns))
    
    if config_db['joins']:
        for join in config_db['joins']:
            if join['on_cols']:
                for on_col in join['on_cols']:
                    if on_col["left_column"] not in columns_across_sheets:
                        st.badge(f"**{on_col['left_column']}** column is missing but required by the query", color='orange')
                        st.stop()
                    if on_col["right_column"] not in columns_across_sheets:
                        st.badge(f"**{on_col['right_column']}** column is missing but required by the query", color='orange')
                        st.stop()
    
    if config_db['conditions']:
        for condition in config_db['conditions']:
            if condition['column'] not in columns_across_sheets:
                st.badge(f"**{condition['column']}** column is missing but required by the query", color='orange')
                st.stop()
                
    #         if condition['operator'] in ['column_equals','column_not_equals']:
    #             if condition['value_1'] not in columns_across_sheets:
    #                 st.badge(f"**{condition['value_1']}** column is missing but required by the query", color='orange')
    #                 st.stop()
            
    #         if condition['operator'] in ['in_list', 'not_in_list']:
    #             list_source = condition['value_1']
    #             parts = list_source.split('.', maxsplit=2)
    
    #             if len(parts) == 3:                
    #                 list_type, source, column = parts
                    
    #                 if source not in sheets:
    #                     st.badge(f"**{sheet}** sheet is missing but required by the query", color='orange')
    #                     st.stop()
    return True


def upload_workbook():
    st.file_uploader(
        "Select Workbook (Excel File) *",
        type=["xlsx", "xls"], key="uploaded_file",
        help="Upload an Excel workbook containing your data sheets."
    )
    
    st.markdown("<style>button { max-width:150px; }</style>", unsafe_allow_html=True)
    
    if st.session_state.uploaded_file:
        current_file_hash = get_file_hash(st.session_state.uploaded_file)
        
        if st.session_state.checklist.get("workbook_hash", None) != current_file_hash:
            file, sheets, tables = load_data(current_file_hash)
            sheets_and_tables = sheets | tables
            
            if selected_sheets_and_columns_are_present_in_file(sheets_and_tables):
                st.session_state.update({
                    "config": st.session_state.selected_checklist.get('config')
                })
                
            st.session_state.checklist.update({
                'workbook': file,
                'only_sheets': sheets,
                'sheets': sheets_and_tables,
                'workbook_hash': current_file_hash,
                "list_type": None,
                "list_source_str": None
            })
    else:            
        st.badge("Select file to continue", color='orange')
        
    return st.session_state.uploaded_file

def checklist_update_form():
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

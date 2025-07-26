# import importlib
# import sys

# def reload_package(package_name: str):
#     for name in list(sys.modules):
#         if name == package_name or name.startswith(f"{package_name}."):
#             importlib.reload(sys.modules[name])

# reload_package("components.select_sheets")

import pandas as pd
import streamlit as st
from utils import alert
from models.tag import Tag
from database.database import get_db
from sqlalchemy.exc import IntegrityError
from util.datatable import get_table_names
from components.join_sheets import join_sheets
from components.query_builder import build_query
from components.select_sheets import select_sheets
from models.validation_checklist import ValidationChecklist
from util.workbook_utils import load_workbook, load_sheet, load_table, get_file_hash

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
    
    if 'joined_df' not in st.session_state:
        st.session_state.joined_df = pd.DataFrame()
    if 'queried_df' not in st.session_state:
        st.session_state.queried_df = pd.DataFrame()
    if 'list_type' not in st.session_state:
        st.session_state.list_type = None
    if 'list_source_str' not in st.session_state:
        st.session_state.list_source_str = None

def load_tags():
    with get_db() as db:
        return Tag.where(db, ["id","name"])

def init_form():
    st.session_state.checklist_code = None
    st.session_state.checklist_name = None
    st.session_state.checklist_description = None
    st.session_state.checklist_tags = []
    st.session_state.checklist_active = True

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
            error_msg = save_checklist()
            if error_msg:
                st.toast(error_msg)
    with col2:
        if st.button("", key="reset_checklist_form", icon=":material/refresh:", help="Reset form"):
            reset_form()

def can_save() -> bool:
    if (st.session_state.checklist['code'] and
        st.session_state.checklist['name'] and
        st.session_state.checklist['description']):
        return True
    else:
        return False

def save_checklist():
    error_message = None
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
                reset_form()
            else:
                alert('Error: Could not create record')
        else:
            alert('Fill all required field.')
    except IntegrityError:
        error_message = f"The 'Code' and 'Name' provided must be unique"
    except Exception as e:
        error_message = f"Error cloning record: {e}"
        
    return error_message

def get_selected_sheets(all_sheets: dict) -> dict:
    selected_sheet_names = st.session_state.config['sheets']
    return { name: all_sheets.get(name) for name in selected_sheet_names }

def reset_form():
    st.session_state.update({
        "checklist": checklist,
        "config": config,
        "joined_df": pd.DataFrame(),
        "queried_df": pd.DataFrame(),
        "list_type": None,
        "list_source_str": None
    })
    
    st.session_state.reset_form = True
    st.rerun()
    
def upload_workbook():    
    st.file_uploader(
        "Select Workbook (Excel File) *",
        type=["xlsx", "xls"], key="create_file",
        help="Upload an Excel workbook containing your data sheets.",
    )
    
    st.markdown("""
        <style>
            button { max-width: 150px; }
        </style>
    """, unsafe_allow_html=True)
    
    if st.session_state.create_file:
        current_hash = get_file_hash(st.session_state.create_file)
                
        if 'workbook_hash' not in st.session_state.checklist:
            st.session_state.checklist['workbook_hash'] = None
            
        if st.session_state.checklist['workbook_hash'] != current_hash:
            
            st.session_state.update({
                "config": config,
                "joined_df": pd.DataFrame(),
                "queried_df": pd.DataFrame(),
                "list_type": None,
                "list_source_str": None
            })
            
            try:
                # Load directly from bytes without temp file
                excel_file = load_workbook(st.session_state.create_file.getvalue(), current_hash)
                table_names = [name[:-1] for name in get_table_names()]
                
                if excel_file.sheet_names:
                    sheets = { name: load_sheet(excel_file, sheet_name=name) 
                                for name in excel_file.sheet_names }
                else: st.warning("Unable to load sheets try again.")
            except Exception as e:
                st.error(f"Error processing workbook: {str(e)}")
                st.stop()
            
            if table_names:
                exempt_tables = ['validation_checklists']
                tables = { name : load_table(name)
                            for name in table_names if name not in exempt_tables }
            else: st.warning("Unable to load master tables contact admin.")
                
            st.session_state.checklist.update({
                'workbook': excel_file,
                'sheets': sheets | tables,
                'workbook_hash': current_hash
            })
        
    return st.session_state.create_file

    
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
    
    if workbook and st.session_state.checklist.get('sheets'):
        st.markdown("""<h4> Configuration </h4>""", unsafe_allow_html=True)
        tabs = ["Select Sheets *", "Join Sheets", "Build Query", "View Output"]
        sheet_tab, join_tab, query_tab, output_tab = st.tabs(tabs, width='stretch')
        all_sheets = st.session_state.checklist['sheets']
        selected_sheets = get_selected_sheets(all_sheets)
        
        with sheet_tab:
            select_sheets(st.session_state.checklist['sheets'], selected_sheets)
        
        with join_tab:
            if len(selected_sheets) >= 2:
                join_sheets(sheets=selected_sheets)
            else:
                st.info('You need at least two or more sheets/tables to perform a join.')
        
        with query_tab:
            if len(selected_sheets):
                build_query(sheets=selected_sheets)
            else:
                st.info("Select sheets/tables to begin building queries")
        
        with output_tab:
            if len(selected_sheets):
                if not st.session_state.queried_df.empty:
                    st.info(f"{len(st.session_state.queried_df)} record(s) returned by query.")
                    st.write(st.session_state.queried_df)
                else:
                    st.info("No queried result.")
            else:
                st.info("No sheets seleted.")
                
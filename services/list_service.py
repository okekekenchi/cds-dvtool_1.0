import streamlit as st
from utils import system_fields
from enums.list_type import ListType
from database.database import get_db
from loader.config_loader import config
from services.workbook_service import get_sheet_columns
from services.query_builder_service import load_checklist
from models.validation_checklist import ValidationChecklist
from util.datatable import get_table_columns, get_table_names

def get_source_from_master_tables():
    list_source = {}
    options = {}
    
    for name in get_table_names():
        try:
            options[name] = config(f'master.{name[:-1]}.label')
        except Exception: # Or a more specific exception
            options[name] = name.replace('_', ' ').capitalize() # Fallback
    
    list_source['table'] = st.selectbox(
                                "**Select a Table:**",
                                options.keys(),
                                format_func=lambda x: options[x],
                                key="master_table_select",
                                index=None
                            )

    if list_source['table']:
        column_names = [col for col in get_table_columns(list_source['table']) if col not in system_fields]
        options = { name: name.replace('_', ' ').capitalize() for name in column_names }
        
        list_source['column'] = st.selectbox(
                                    "**Select a Column:**",
                                    options.keys(),
                                    format_func=lambda x: options[x],
                                    key="master_column_select"
                                )
        
        if list_source['column']:
            return f"{ListType.Master.value}.{list_source['table']}.{list_source['column']}"
    return None

def get_source_from_sheets():
    if 'only_sheets' not in st.session_state.checklist:
        st.warning('There are no sheets in workbook if uploaded.')
        return
    
    list_source = {}
    sheets = st.session_state.checklist['only_sheets']
    
    list_source['sheet'] = st.selectbox(
                                "**Select a sheet from workbook:**",
                                options=sheets.keys(),
                                key="27989892__",
                                index=None
                            )

    if list_source['sheet']:
        column_names = get_sheet_columns(sheets, list_source['sheet'])
        options = { name: name.replace('_', ' ').capitalize() for name in column_names }
        
        list_source['column'] = st.selectbox(
                                    "**Select a Column:**",
                                    options.keys(),
                                    format_func=lambda x: options[x],
                                    key="9382783__"
                                )
        
        if list_source['column']:
            return f"{ListType.Sheet.value}.{list_source['sheet']}.{list_source['column']}"
    return None

def get_source_from_validation_checklist():
    if 'sheets' not in st.session_state.checklist:
        st.warning('There are no sheets in workbook if uploaded.')
        return
    
    list_source = {}
    sheets:dict = st.session_state.checklist['only_sheets']
    
    with get_db() as db:
        checklists = ValidationChecklist.all(db, columns=["id", "name"], as_dict=True)
    
    options = { checklist['id']:checklist['name'] for checklist in checklists }
    
    list_source['checklist_id'] = st.selectbox(
                                    "**Select a Validation Checklist:**",
                                    options.keys(),
                                    format_func=lambda x: options[x],
                                    key="select_checklist_as_source",
                                    index=None
                                )
    
    if list_source['checklist_id']:
        with get_db() as db:
            checklist = ValidationChecklist.find(db, list_source['checklist_id'])

        column_names = load_checklist(checklist.config, sheets).columns
        
        list_source['column'] = st.selectbox(
                                    "**Select a Column:**",
                                    options=column_names,
                                    key="checklist_col_list_source"
                                )
        
        if list_source['column']:
            return f"{ListType.Checklist.value}.{checklist.id}.{list_source['column']}"
    return None


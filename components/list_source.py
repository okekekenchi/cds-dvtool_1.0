import streamlit as st
from utils import system_fields, get_model_class
from util.project_utils import get_sheet_columns
from util.datatable import get_table_columns, get_table_names
from loader.config_loader import config
from enums.list_type import ListType
from database.database import get_db

@st.dialog('List Source')
def set_list_source_string() -> str:
    st.session_state.update({'list_source_str': None})
    source_string = None
    
    list_type = st.selectbox(f"**Select List Source**",
                            options=['masters', 'sheets', 'validation_checklist'],
                            key="list_source_field",
                            format_func=lambda x: x.replace('_',' ').capitalize())

    if list_type == 'masters':
        source_string = get_source_from_master_tables()
    
    if list_type == 'sheets':
        source_string = get_source_from_sheets()
        
    if list_type == 'validation_checklist':
       source_string = get_source_from_validation_checklist()
    
    st.write('')
    st.write('')
    
    _, col1, col2 = st.columns([0.3,0.35,0.35])
    with col1:
        if st.button('Save', key="save_list_source"):
            st.session_state.update({"list_source_str": source_string})
            st.rerun()
    with col2:
        if st.button('Cancel', key="cancel_list_source"):
            st.rerun()

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
    if 'sheets' not in st.session_state.project:
        st.warning('There are no sheets in workbook if uploaded.')
        return
    
    list_source = {}
    sheet_options = st.session_state.project['sheets'].keys()
    
    list_source['sheet'] = st.selectbox(
                                "**Select a sheet from workbook:**",
                                options=sheet_options,
                                key="27989892__",
                                index=None
                            )

    if list_source['sheet']:
        column_names = get_sheet_columns(list_source['sheet'])
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
    list_source = {}
    return None
    # return f"{ListType.Checklist.value}.{list_source['checklist']}.{list_source['column']}"
    
def model(table_name):
    table_class = table_name[:-1]
    return get_model_class(table_class)

def get_list_from_selected_source(list_source: str) -> list:
    parts = list_source.split('.', maxsplit=2)
    
    if len(parts) != 3:
        return None
    
    list_type, source, column = parts
    
    if list_type not in (list_type.value for list_type in ListType):
        return None
    
    if list_type == ListType.Master.value:
        with get_db() as db:
            return model(source).all_df(db, columns=[column]).drop_duplicates().values.tolist()
        
    elif list_type == ListType.Sheet.value:
        if source in st.session_state.project['sheets']:
            all_list = st.session_state.project['sheets'][source]
            if column in all_list:
                return all_list[column].drop_duplicates().values.tolist()
            else:
                st.warning(f'Column: {column} does not exist in sheet: {source}.')
        else:
            st.warning(f'There is no sheet: {source} in workbook.')
        
    elif list_type == ListType.Checklist.value:
        return []
    
    return []

import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("services.column_operation_service")
reload_package("services.join_service")
reload_package("components.select_sheets")
reload_package("components.join_sheets")
reload_package("components.query_builder")

import streamlit as st
from components.join_sheets import join_sheets
from components.query_builder import build_query
from components.select_sheets import select_sheets
from services.join_service import get_joined_sheets
from services.column_operation_service import run_column_operations
from services.query_builder_service import execute_query

@st.fragment
def configure_checklist(configuration: dict):
    if st.session_state.checklist.get('sheets'): # Question this
        st.markdown("""<h4> Configuration </h4>""", unsafe_allow_html=True)
        tabs = ["Select Sheets *", "Join Sheets", "Build Query", "View Output"]
        sheet_tab, join_tab, query_tab, output_tab = st.tabs(tabs, width='stretch')
        
        with sheet_tab:
            select_sheets(st.session_state.checklist['sheets'], configuration)
            
            selected_sheets = run_column_operations(
                                all_sheets=st.session_state.checklist['sheets'],
                                selected_sheets=configuration.get('sheets')
                              )
            
        with join_tab:
            if len(selected_sheets) >= 2:
                join_sheets(selected_sheets, configuration)
            else:
                st.info('You need at least two or more sheets/tables to perform a join.')
                
            if len(selected_sheets):
                joined_df = get_joined_sheets(
                                sheets=selected_sheets,
                                join_conditions=configuration.get('joins', [])
                            )
        
        with query_tab:
            if len(selected_sheets):
                build_query(
                    all_sheets=st.session_state.checklist.get('sheets', []),
                    configuration=configuration,
                    joined_df=joined_df
                )
            else:
                st.info("Select sheets/tables to begin building queries")
        
        with output_tab:
            if len(selected_sheets):
                queried_df = execute_query(
                                all_sheets=st.session_state.checklist.get('sheets', []),
                                joined_df=joined_df,
                                conditions=configuration.get('conditions', []),
                            )
                
                if not queried_df.empty:
                    st.info(f"{len(queried_df)} record(s) returned by query.")
                    st.dataframe(queried_df)
                else:
                    st.info("No queried result.")
            else:
                st.info("No sheets seleted.")

import streamlit as st
from util.project_utils import clear_sheets
    
@st.dialog('Preview Table', width="large")
def preview_sheet(df):
    st.dataframe(df.head())
       
def select_sheets(all_sheets: dict, selected_sheets: dict):
    """Renders UI for selecting and managing sheets for validation.
    
    Allows users to:
    - Select sheets from available workbook sheets
    - Add selected sheets to validation checklist
    - Remove sheets from validation checklist
    
    Returns:
        None - updates session state directly
    """
    col1, col2, col3, _ = st.columns([0.5,0.2,0.05, 0.25])
    sheet_options = list(all_sheets.keys())
    
    with col1:
        new_sheets = st.multiselect(
                        "Select sheets/tables to validate *",
                        key="selected_sheets",
                        options=[ option for option in sheet_options if option not in selected_sheets.keys() ],
                        default=None,
                        help="Select which sheets you want to include in validation"
                     )
    with col2:
        if st.button("Add", key="add_sheets", icon=":material/add:") and new_sheets:
            for sheet in new_sheets:
                if sheet not in selected_sheets.keys():
                    st.session_state.config['sheets'].append(sheet)
            st.rerun()
    with col3:
        st.write('')
        st.write('')
        st.button("", on_click=clear_sheets, key="clear_sheets",
                  icon=":material/refresh:", help="Clear all selected sheets")
             
    if not selected_sheets:
        clear_sheets()
        st.write("Your sheet list is empty!")
    else:
        for i, sheet in enumerate(selected_sheets.keys()):
            st.divider()
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            
            with col1:
                st.write(f"{i+1}. {sheet}")
            with col2:
                if st.button(f"View", key=f"preview_sheet_{i}", icon=":material/visibility:"):
                    preview_sheet(all_sheets[sheet])
            with col3:
                if st.button(f"Delete", key=f"delete_sheet_{i}", icon=":material/delete:"):
                    del st.session_state.config['sheets'][i]
                    st.rerun()
        

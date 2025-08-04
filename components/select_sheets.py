import streamlit as st

def clear_sheets():
    """Reset all sheets"""
    st.session_state.update({
        "config": {
            "sheets": [],
            "joins": [],
            "conditions": []
        }
    })
    
def delete_sheet(sheet_index:int):
    """
    Delete sheet name at the specified index
    deletes all joins have the sheet name

    Args:
        sheet_index (int): _description_
    """
    sheet_name = st.session_state.config['sheets'][sheet_index]
    del st.session_state.config['sheets'][sheet_index]
    
    joins = st.session_state.config['joins']
    for idx, join in enumerate(joins):
        if sheet_name in [join["left_table"], join["right_table"]]:
            del st.session_state.config['joins'][idx]                            
    
@st.dialog('Preview Sheet/Table', width="large")
def preview_sheet(df):
    st.dataframe(df.head())
    
def show_selected_sheets(all_sheets: dict):
    selected_sheets = st.session_state.config.get("sheets")
    
    if not selected_sheets:
        clear_sheets()
        st.write("Your sheet list is empty!")
    else:
        for i, sheet in enumerate(selected_sheets):
            st.divider()
            col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
            
            with col1:
                st.write(f"{i+1}. {sheet}")
            with col2:
                if st.button(f"View", key=f"preview_sheet_{i}", icon=":material/visibility:"):
                    preview_sheet(all_sheets[sheet])
            with col3:
                if st.button(f"Delete", key=f"delete_sheet_{i}", icon=":material/delete:"):
                    delete_sheet(sheet_index=i)                            
                    st.rerun()

def select_sheets(all_sheets: dict):
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
    selected_sheets = st.session_state.config.get('sheets', [])
    
    with col1:
        new_sheets = st.multiselect(
                        "Select sheets/tables to validate *",
                        key="selected_sheets",
                        options=[ option for option in sheet_options if option not in selected_sheets ],
                        default=None,
                        help="Select which sheets you want to include in validation"
                     )
    with col2:
        if st.button("Add", key="add_sheets", icon=":material/add:") and new_sheets:
            for sheet in new_sheets:
                if sheet not in selected_sheets:
                    st.session_state.config['sheets'].append(sheet)
            st.rerun()
    with col3:
        st.write('')
        st.write('')
        st.button("", on_click=clear_sheets, key="clear_sheets",
                  icon=":material/refresh:", help="Clear all selected sheets")
        
    show_selected_sheets(all_sheets)
    
        
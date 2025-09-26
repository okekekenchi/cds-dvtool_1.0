import streamlit as st
from components.column_operation import column_operation
    
@st.dialog('Preview Sheet/Table', width="large", dismissible=True)
def preview_sheet(df):
    st.dataframe(df.head())
    
def get_selected_sheet_names(sheets: list[dict]):
    return[
        sheet['name']
        for sheet in sheets
    ]
    
def delete(configuration: dict, idx: int):
    del configuration["sheets"][idx]
    configuration["joins"] = []
    configuration["conditions"] = []
    st.rerun(scope='fragment')
    
def clear(configuration: dict):
    configuration["sheets"] = []
    configuration["joins"] = []
    configuration["conditions"] = []
    st.rerun(scope='fragment')
    
def add(configuration: dict, sheet_name: str):
    if "sheets" in configuration:
        configuration["sheets"].append({ "name": sheet_name, "col_operations":[] })
        st.toast("Sheet(s) added")
    else:
        configuration["sheets"] = []

def show_selected_sheets(all_sheets: dict, configuration: dict):
    selected_sheet_names = get_selected_sheet_names(configuration.get('sheets', []))
    
    if not selected_sheet_names:
        st.write("Your sheet list is empty!")
        return

    for i, sheet_name in enumerate(selected_sheet_names):
        st.divider()
        col1, col2, col3, col4 = st.columns([0.6, 0.125,0.125,0.15], vertical_alignment="center")
        
        with col1:
            st.write(f"{i+1}. {sheet_name}")
            
        with col2:
            if (st.button(f"Preview ", key=f"preview_sheet_{i}",
                            icon=":material/visibility:", help="Preview the top 5 records")):
                preview_sheet(all_sheets[sheet_name])
                
        with col3:
            if st.button(f"Configure ", key=f"configure_column_{i}",
                         icon=":material/settings:", help="Configure column operations."):
                column_operation(all_sheets, configuration, sheet_name, i)
                
        with col4:
            if st.button(f"Delete", key=f"delete_col_operation_{i}", icon=":material/delete:"):
                delete(configuration, i)

def select_sheets(all_sheets: dict, configuration: dict):
    """Renders UI for selecting and managing sheets for validation"""
    
    col1, _, col2, col3 = st.columns([2.5,1.5,0.6,0.8], vertical_alignment="center")
    sheet_options = list(all_sheets.keys())
    selected_sheet_names = get_selected_sheet_names(configuration.get('sheets', []))
    
    with col1:
        new_sheets = st.multiselect(
                        "Select sheets/tables to validate *",
                        key="selected_sheets",
                        options=[ option for option in sheet_options if option not in selected_sheet_names ],
                        default=None,
                        help="Select which sheets you want to include in validation"
                     )
    with col2:
        # st.markdown("<style>.m-top{margin-top:23px;}</style><div class='m-top'></div>", unsafe_allow_html=True)
        if st.button("Add", key="add_sheets", icon=":material/add:", use_container_width=True) and new_sheets:
            for sheet_name in new_sheets:
                if sheet_name not in selected_sheet_names:
                    add(configuration, sheet_name)
            st.rerun(scope='fragment')
            
    with col3:
        if st.button("Clear Sheets", key="clear_sheets",
                     icon=":material/refresh:", use_container_width=True):
            clear(configuration)
            
    show_selected_sheets(all_sheets, configuration)
    
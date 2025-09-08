import copy
import streamlit as st
from util.auth_utils import requires_any_role
from utils import get_model_class, system_tables, system_fields, bool_fields, required_fields, textarea_fields
from components.side_nav import side_nav
from loader.config_loader import config
from loader.css_loader import load_css
from database.migration import init_db
from util.datatable import get_table_columns, get_table_names, get_table_data, delete_record
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
import time
from utils import alert
from database.database import get_db, engine

st.set_page_config(page_title="Masters", page_icon=":material/settings:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/masters.css')

def init_session_var():
  if "new_record" not in st.session_state:
    st.session_state.new_record = False
  if "selected_row" not in st.session_state:
    st.session_state.selected_row = {}
  if "active_records" not in st.session_state:
    st.session_state.active_records = True

def field_name(field: str):
    f_name =  f"{field} *" if field in required_fields else field
    return f_name.replace('_', ' ').capitalize()

def model():
    table_class = st.session_state.selected_table[:-1]
    return get_model_class(table_class)

def form_action(form_data, action: str):
    col1, col2 = st.columns([1,1], vertical_alignment="center")
    saved = False
    with col1:
        if st.button(f"{action.capitalize()} Record", use_container_width=True,
                        disabled=is_system_record(), key="save_master"):
            try:
                with get_db() as db:
                    if action.lower() == "create":
                        _, saved = model().first_or_create(db, **form_data)
                    elif action.lower() == "update":
                        model().update(db, form_data["id"], form_data)
                        saved = True
                    else:
                        st.error(f"Invalid action: {action}")
            except Exception as e:
                st.error(f"Error saving record****: {e}")
    with col2:
        if st.button("Cancel", key="cancel_master", use_container_width=True):
            st.session_state.new_record = False
            st.rerun()
            
    if saved:
        st.success(f"Record {action.lower()}d successfully!")
        st.session_state.new_record = False
        st.session_state.selected_row = {}
        time.sleep(1.5)
        st.rerun()

@st.dialog("Delete Record", dismissible=True, on_dismiss="ignore")
def delete_form(record_id):                
    st.warning(f"Are you sure you want to delete record with ID: **{record_id}**?")
    
    col1, col2 = st.columns([1, 1], vertical_alignment="center")
    deleted = False
    with col1:
        if st.button("Confirm Delete", key="confirm_master_delete_btn", use_container_width=True):
            try:
                delete_record(st.session_state.selected_table, record_id)
                deleted = True
            except Exception as e:
                st.error(f"Error deleting record: {e}")
    with col2:
        if st.button("Cancel", key="cancel_delete", use_container_width=True):
            st.session_state.selected_row = {}
            st.rerun()
            
    if deleted:
        st.success("Record deleted successfully!")
        st.session_state.selected_row = {}
        time.sleep(1.5)
        st.rerun()
        
def form_fields(data):
    for col in get_table_columns(st.session_state.selected_table):
        if col != "id" and col not in system_fields: # Disallow editing of ID and system fields
            if 'selected_row' in st.session_state:
                current_value = st.session_state.selected_row.get(col) if "id" in data else None
            else:
                current_value = None
            
            if col in bool_fields:
                data[col] = st.checkbox(field_name(col), value=current_value or True, disabled=is_system_record())
            elif  col in textarea_fields:
                data[col] = st.text_area(field_name(col), value=current_value, disabled=is_system_record(), max_chars=500)
            else:
                data[col] = st.text_input(field_name(col), value=current_value, disabled=is_system_record(), max_chars=100)
    return data

def is_system_record():
    if st.session_state.selected_row:
        return st.session_state.selected_row.get("created_by", None) == "System"
    else:
        return False

@st.dialog("Edit Record", dismissible=True, on_dismiss="rerun")
def edit_form(record_id):
    if is_system_record():
        st.warning("You cannot edit a **System** record.")
    
    init_form_data = { "id": record_id }
    form_data = form_fields(init_form_data)
    form_action(form_data, "Update")

@st.dialog("Create Record", dismissible=True, on_dismiss="rerun")
def create_form():
    init_form_data = { "created_by": st.session_state.user_id}
    form_data = form_fields(init_form_data)
    form_action(form_data, 'Create')

def show_datatable(create_btn_placeholder):
    action_placeholder = st.empty()
    
    try:
        df = get_table_data(st.session_state.selected_table,
                            st.session_state.search_query,
                            **{ "active": st.session_state.active_records })
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

    # Format Created By
    users = pd.read_sql("SELECT id, full_name FROM users", engine)
    user_map = dict(zip(users['id'], users['full_name']))
    user_id = st.session_state.user_id
    df['created_by'] = df['created_by'].map(lambda x: "Me" if x == user_id else user_map.get(x, "System")).fillna("System").replace("", "System")

    # Configure tablez
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_default_column(editable=False, filterable=False, sortable=True, resizable=True, width=250)
    gb.configure_grid_options(domLayout='normal')
    
    columns_to_hide = ["active", "config"]
    for column in columns_to_hide:
        if column in df:
            gb.configure_column(field=column, hide=True)
        
    gb.configure_column(field="created_by", header_name="Created by")
    gb.configure_column(field="created_by", header_name="Created by")
    gb.configure_column(field="created_at", header_name="Created at", valueFormatter="new Date(data.created_at).toLocaleString()")
    gb.configure_column(field="updated_at", header_name="Updated at", valueFormatter="new Date(data.updated_at).toLocaleString()")
    gb.configure_selection(selection_mode='single', use_checkbox=True)
                
    # Display the grid
    grid_response = AgGrid(
        df,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme='streamlit',
        enable_enterprise_modules=True,
        sidebar=True,
        fit_columns_on_grid_load=True
    )
    
    # Handle row selection for editing
    selected_rows = grid_response.get("selected_rows", [])
    
    # Convert to list of dicts if it's a DataFrame
    if hasattr(selected_rows, 'to_dict'):
        selected_rows = selected_rows.to_dict('records')

    # Now safely check if we have selected rows
    if isinstance(selected_rows, list) and len(selected_rows) > 0:
        st.session_state.selected_row = copy.deepcopy(selected_rows[0])
        st.session_state.new_record = False
    else:
        st.session_state.selected_row = {}
        
    # Show action buttons for selected row
    with action_placeholder.container():
        if st.session_state.selected_row:
            record_id = st.session_state.selected_row.get("id")
            if not record_id:
                st.warning("Invalid record ID")
                return
            
            col1, _ = st.columns([1, 1], vertical_alignment="center")
            with col1:
                if (st.button("Edit Record", icon=":material/edit:", key="edit_master_btn", help="Edit record") and
                    st.session_state.active_records):
                    edit_form(record_id)

                if st.session_state.selected_table not in ['tags']:
                    if st.button("Delete Record", icon=":material/delete:", key="delete_master_btn"):
                        if is_system_record():
                            alert("This is a **system record** - you cannot delete.")
                            return
                        
                        delete_form(record_id)
                        
    with create_btn_placeholder.container():
        if not st.session_state.selected_row and st.session_state.selected_table:
            if st.button("New Record", key="create", icon=":material/add:", use_container_width=True):
                st.session_state.new_record = True
                st.session_state.selected_row = {}
                create_form()
        else:
            st.session_state.new_record = False    

def reset_params():
    st.session_state.new_record = False
    st.session_state.selected_row = {}

@requires_any_role("admin")
def main():
    init_session_var()
    
    col1, col2, col3, col4 = st.columns([0.35, 0.3, 0.15, 0.2], vertical_alignment="bottom")
    with col1:
        table_names = [ name for name in get_table_names() if name not in system_tables ]
        options = { name: config(f'master.{name[:-1]}.label') for name in table_names }

        if options:
            st.selectbox(
                "Select a Table:",
                options=options.keys(),
                format_func=lambda x: options[x],
                key="selected_table",
                on_change=reset_params
            )
        else:
            st.warning("Error loading tables.")
            
    with col2:
        st.text_input(
            "Search Records:",
            placeholder="Type to search...",
            key="search_query", help="Search across all columns"
        )
    with col3:
        st.selectbox(
            "Show Records",
            options=[True, False],
            format_func=lambda x: "Active" if x else "Inactive",
            index=0 if st.session_state.active_records else 1,
            key="active_records",
            on_change=reset_params,
            help=f"Show {'active' if st.session_state.active_records else 'inactive'} records",
        )
    with col4:
       create_btn_placeholder = st.empty()
    
    st.divider()

    if st.session_state.selected_table:
        show_datatable(create_btn_placeholder)
    else:
        st.info("Please select a table from the sidebar to begin.")
        
if __name__ == "__main__":
    init_db()
    st.session_state.current_page = "pages/masters.py"
    st.markdown("""<h2>Master Records</h2>""", unsafe_allow_html=True)
    side_nav()
    main()
    
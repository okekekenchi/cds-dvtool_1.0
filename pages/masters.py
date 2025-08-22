import streamlit as st
from util.auth_utils import authenticated
from utils import get_model_class, system_fields, bool_fields, required_fields, textarea_fields
from components.side_nav import side_nav
from loader.config_loader import config
from loader.css_loader import load_css
from database.migration import init_db
from util.datatable import get_table_columns, get_table_names, get_table_data, delete_record
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
import time
from database.database import get_db, engine

st.set_page_config(page_title="Masters", page_icon=":material/settings:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/project.css')

def init_session_var():
  if "edit_record" not in st.session_state:
    st.session_state.edit_record = None
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
    _, col1, col2 = st.columns([0.49, 0.31, 0.2])
    saved = False
    with col1:
        if st.form_submit_button(f"{action.capitalize()} Record", disabled=is_system()):
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
        if st.form_submit_button("Cancel"):
            st.session_state.new_record = False
            st.rerun()
            
    if saved:
        st.success(f"Record {action.lower()}d successfully!")
        st.session_state.new_record = False
        st.session_state.edit_record = None
        st.session_state.selected_row = {}
        time.sleep(1.5)
        st.rerun()

@st.dialog("Delete Record")
def delete_form():
    record_id = st.session_state.selected_row.get("id")
    
    if is_system():
        st.warning("This is a **system record** - you cannot delete.")
        return
                
    st.warning(f"Are you sure you want to delete this record: {record_id}?")
    
    _, col1, col2 = st.columns([0.35, 0.4, 0.25])
    deleted = False
    with col1:
        if st.button("Confirm Delete", key="confirm_delete"):
            try:
                delete_record(st.session_state.selected_table, record_id)
                deleted = True
            except Exception as e:
                st.error(f"Error deleting record: {e}")
    with col2:
        if st.button("Cancel", key="cancel_delete"):
            st.session_state.selected_row = {}
            st.rerun()
            
    if deleted:
        st.success("Record deleted successfully!")
        st.session_state.selected_row = {}
        time.sleep(1.5)
        st.rerun()
        
def form_fields(data):
    for col in get_table_columns(st.session_state.selected_table):
        if col != "id" and col not in system_fields:
            current_value = st.session_state.edit_record.get(col) if "id" in data else None
            
            if col in bool_fields:
                data[col] = st.checkbox(field_name(col), value=current_value or True, disabled=is_system())
            elif  col in textarea_fields:
                data[col] = st.text_area(field_name(col), value=current_value, disabled=is_system(), max_chars=500)
            else:
                data[col] = st.text_input(field_name(col), value=current_value, disabled=is_system(), max_chars=100)
    return data

def is_system():
    if st.session_state.edit_record:
        return st.session_state.edit_record.get("created_by", None) == "System"
    else:
        return False

@st.dialog("Edit Record")
def edit_form():
    record_id = st.session_state.edit_record.get("id")
    
    if not record_id:
        st.warning("No ID column found in this table. Editing requires an 'id' column.")
        return
    else:
        with st.form(key="edit_form"):
            init_form_data = { "id": st.session_state.edit_record.get("id") }
            form_data = form_fields(init_form_data)
            form_action(form_data, "Update")

@st.dialog("Create Record")
def create_form():
    if st.session_state.selected_row:
        st.warning("You have a record selected for update - unselect to create new records.")
        return
    
    with st.form(key="create_form"):
        init_form_data = { "created_by": st.session_state.user_id}
        form_data = form_fields(init_form_data)
        form_action(form_data, 'Create')

def show_datatable(create_btn_placeholder):
    action_placeholder = st.empty()
    
    # fetch data
    # search_columns =  get_table_columns(st.session_state.selected_table) - system_fields
    # search_columns
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

    if not df.empty:
        # Configure tablez
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_default_column(editable=False, filterable=False, sortable=True, resizable=True, width=250)
        gb.configure_grid_options(domLayout='normal')
        
        columns_to_hide = ["id", "active", "config"]
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
            st.session_state.selected_row = selected_rows[0]
            st.session_state.edit_record = None
            st.session_state.new_record = False
        else:
            st.session_state.selected_row = {}
    else:
        st.warning("No records found in this table.")
        
    # Show action buttons for selected row
    with action_placeholder.container(): 
        if st.session_state.selected_row:                
            col1, col2, _ = st.columns([2,2, 6], vertical_alignment="center")
            with col1:
                if st.session_state.active_records and st.button("Edit Record", icon=":material/edit:"):
                    st.session_state.edit_record = st.session_state.selected_row
            with col2:
                if st.session_state.selected_table not in ['tags']:
                    st.button("Delete Record", icon=":material/delete:", on_click=delete_form)
    with create_btn_placeholder.container():
        if not st.session_state.selected_row and st.session_state.selected_table:
            st.markdown("<style>.m-top{margin-top:23px;}</style><div class='m-top'></div>", unsafe_allow_html=True)
            if st.button("New Record", key="create", icon=":material/add:"):
                st.session_state.new_record = True
                st.session_state.edit_record = None
                st.session_state.selected_row = {}
    
    # Edit form
    if  st.session_state.active_records and st.session_state.edit_record and st.session_state.selected_row:
        edit_form()

    # Create new record form
    if st.session_state.new_record and not st.session_state.selected_row:
        create_form()

def reset_params():
    st.session_state.edit_record = None
    st.session_state.new_record = False
    st.session_state.selected_row = {}

@authenticated
def main():
    st.title("Master Records")
    side_nav()
    init_session_var()
    
    st.write('')
    st.write('')
    st.write('')
    
    col1, col2, col3, col4 = st.columns([0.35, 0.3, 0.15, 0.2])
    with col1:
        exempt_tables = ['validation_checklists']
        table_names = [ name for name in get_table_names() if name not in exempt_tables ]
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
    main()
    
import streamlit as st
from utils import authenticated, get_model_class, get_user_by_id
from components.side_nav import side_nav
from loader.config_loader import config
from loader.css_loader import load_css
from util.datatable import update_record, get_table_columns, get_table_names, get_table_data, delete_record, initialize_session
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
from models.bh_task_type import BhTaskType
import time
from database.database import get_db, engine

st.set_page_config(page_title="Masters", page_icon=":settings:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/masters.css')

system_tables = ["users","sessions"]
system_fields = ["created_by", "created_at", "updated_at"]
bool_fields = ["active"]
required_fields = ["task_type_id","meas_base","mb_desc"]

st.markdown("""
        <style>
        button[aria-label="Close"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

def field_name(field: str):
    f_name =  f"{field} *" if field in required_fields else field
    return f_name.replace('_', ' ').capitalize()

def model():
    table_class = st.session_state.selected_table[:-1]
    return get_model_class(table_class)

def form_action(form_data):
    col1, col2 = st.columns([0.5,0.5])
    saved = False
    with col1:
        if st.form_submit_button("Create Record"):
            try: 
                with get_db() as db:
                    _, saved = model().first_or_create(db, **form_data)
            except Exception as e:
                st.error(f"Error creating record: {e}")
    with col2:
        if st.form_submit_button("Cancel"):
            st.session_state.new_record = False
            st.rerun()
            
    if saved:
        st.success("Record created successfully!")
        st.session_state.new_record = False
        time.sleep(2)
        st.rerun()
        

@st.dialog("Delete Record")
def delete_form():
    record_id = st.session_state.selected_row.get("id")
                
    st.warning(f"Are you sure you want to delete this record: {record_id}?")
    
    col1, col2 = st.columns([0.5,0.5])
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
            st.session_state.selected_row = None
            st.rerun()
            
    if deleted:
        st.success("Record deleted successfully!")
        st.session_state.selected_row = None
        time.sleep(2)
        st.rerun()
                            
@st.dialog("Edit Record")
def edit_form():
    return
    with st.form(key="edit_form"):
        record_id = st.session_state.edit_record.get("id")
        if not record_id:
            st.error("No ID column found in this table. Editing requires an 'id' column.")
        else:
            form_data = {}
            columns = get_table_columns(st.session_state.selected_table)
            
            for col in columns:
                if col != "id":  # Skip ID field
                    current_value = st.session_state.edit_record.get(col)
                    if pd.isna(current_value):
                        current_value = None
                    form_data[col] = st.text_input(col, value=current_value)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Save Changes"):
                    try:
                        update_record(st.session_state.selected_table, record_id, form_data)
                        st.success("Record updated successfully!")
                        st.session_state.edit_record = None
                        st.session_state.selected_row = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating record: {e}")
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.edit_record = None
                    st.rerun()

@st.dialog("Create Record")
def create_form():
    if st.session_state.selected_row:
        return
    
    with st.form(key="create_form"):
        form_data = { "created_by": st.session_state.user_id}
        for col in get_table_columns(st.session_state.selected_table):
            if col != "id" and col not in system_fields:
                if col in bool_fields:
                    form_data[col] = st.checkbox(field_name(col), value=True)
                elif col == "task_type_id":
                    with get_db() as db:
                        task_types = BhTaskType.where(db, ["id","task_type","desc"], **{"active":True})
                        options = {item['id']: f"{item['task_type']} - {item['desc']}" for item in task_types}
                        form_data[col] = st.selectbox("Select a task type", options.keys(), format_func=lambda x: options[x])
                else:
                    form_data[col] = st.text_input(field_name(col), value=None)
        form_action(form_data)

@authenticated
def main():
    st.session_state.current_page = "pages/8_masters.py"
    side_nav()
    st.title("Master Records")
    initialize_session()
    
    col1, col2, col3, col4 = st.columns([0.35, 0.3, 0.15, 0.2])
    with col1:
        table_names = [name for name in get_table_names() if name not in system_tables]
        options = { name: config(f'master.{name[:-1]}.label') for name in table_names }
        
        selected_table = st.selectbox(
            "Select a Table:",
            options.keys(),
            format_func=lambda x: options[x],
            key="table_select",
            index=table_names.index(st.session_state.selected_table) if st.session_state.selected_table in table_names else 0,
        )
    with col2:
        st.session_state.search_query = st.text_input(
            "Search Records:",
            value=st.session_state.search_query,
            placeholder="Type to search...",
            key="search_input",
            help="Search across all columns"
        )
    with col3:
        toggle_active_records = st.selectbox(
            "Show Records",
            options=[True, False],
            format_func=lambda x: "Active" if x else "Inactive",
            index=0 if st.session_state.active_records else 1,
            key="active_records_selector",
            help=f"Show {'active' if st.session_state.active_records else 'inactive'} records",
        )
    with col4:
       create_btn_placeholder = st.empty()
    
        
    if selected_table != st.session_state.selected_table:
        st.session_state.selected_table = selected_table
        st.session_state.edit_record = None
        st.session_state.new_record = False
        st.session_state.selected_row = None
        st.rerun()
    
    if toggle_active_records != st.session_state.active_records:
        st.session_state.active_records = toggle_active_records
        st.rerun()
    
    st.markdown("---")

    # Main content area
    if st.session_state.selected_table:
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
        df['created_by'] = df['created_by'].map(user_map).fillna("System").replace("", "System")

        if not df.empty:
            # Configure tablez
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
            gb.configure_default_column(editable=False, filterable=True, sortable=True, resizable=True)
            gb.configure_grid_options(domLayout='normal')
            gb.configure_column(field="active", header_name="Active")
            gb.configure_column(field="created_by", header_name="Created by")
            gb.configure_column(field="created_at", header_name="Created at", valueFormatter="new Date(data.created_at).toLocaleString()")
            gb.configure_column(field="updated_at", header_name="Updated by", valueFormatter="new Date(data.updated_at).toLocaleString()")
            gb.configure_selection(selection_mode='single', use_checkbox=True)
                        
            # Display the grid
            grid_response = AgGrid(
                df,
                gridOptions=gb.build(),
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                theme='streamlit',
                enable_enterprise_modules=True,
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
                st.session_state.selected_row = None
        else:
            st.warning("No records found in this table.")
         
        # Show action buttons for selected row
        with action_placeholder.container(): 
            if st.session_state.selected_row:                
                col1, col2, _ = st.columns([1.5,1.6,5], vertical_alignment="center")
                with col1:
                    if st.button("Edit Record", icon=":material/edit:"):
                        st.session_state.edit_record = st.session_state.selected_row
                with col2:
                    if st.button("Delete Record", icon=":material/delete:"):
                        delete_form()
        
        with create_btn_placeholder.container():
            if not st.session_state.selected_row:
                if st.button("New Record", key="create", icon=":material/add:") and selected_table:
                    st.session_state.new_record = True
                    st.session_state.edit_record = None
                    st.session_state.selected_row = None
        
        # Edit form
        if st.session_state.edit_record and st.session_state.selected_row:
            edit_form()

        # Create new record form
        if st.session_state.new_record and not st.session_state.selected_row:
            create_form()

    else:
        st.info("Please select a table from the sidebar to begin.")
        
if __name__ == "__main__":
    main()
    
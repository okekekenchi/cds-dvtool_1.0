import time
import pandas as pd
import streamlit as st
from util.auth_utils import authenticated
from components.side_nav import side_nav
from loader.css_loader import load_css
from database.migration import init_db
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from database.database import get_db
from services.checklist_service import load_data_with_retry
from models.user import User
from util.auth_utils import requires_any_role, hash_password, email_exists

st.set_page_config(page_title="Users", page_icon=":material/settings:", layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/users.css')

TABLE_NAME = "users"

def init_session_var():
  if "selected_row" not in st.session_state:
    st.session_state.selected_row = {}
  if "active_accounts" not in st.session_state:
    st.session_state.active_accounts = True
    
def status_action(record_id, action:str):
    st.warning(f"Are you sure you want to {action} account with ID: **{record_id}**?")
    
    col1, col2 = st.columns([1, 1], vertical_alignment="center")
    status = False
    with col1:
        if st.button("Confirm action", key=f"confirm_user_{action}_btn", use_container_width=True):
            try:
                with get_db() as db:
                    User.update(db, record_id, { "active": 1 if action == "activate" else 0 })
                    status = True
            except Exception as e:
                st.write(e)
                st.error(f"Error deactivating account: {e}")
    with col2:
        if st.button("Cancel", key=f"cancel_{action}", use_container_width=True):
            st.session_state.selected_row = {}
            st.rerun()
            
    if status:
        st.success(f"Record {action}d successfully!")
        st.session_state.selected_row = {}
        time.sleep(1.5)
        st.rerun()

@st.dialog("Dactivate Account", dismissible=True, on_dismiss="ignore")
def deactivate_form(record_id):                
    status_action(record_id, "deactivate")
    
@st.dialog("Activate Account", dismissible=True, on_dismiss="ignore")
def activate_form(record_id):                
    status_action(record_id, "activate")

@st.dialog("Create Record", dismissible=True, on_dismiss="rerun")
def create_form():
    form_data = { "created_by": st.session_state.user_id}
    form_data["full_name"] = st.text_input("Full Name*", placeholder="Enter your full name")
    form_data["email"] = st.text_input("Email *", placeholder="example@domain.com")
    form_data["password"] = hash_password("Passw0rd")
    error = None
    st.info("The new user's password defaults as **Passw0rd**.\n Changes can be made later.")
    
    col1, col2 = st.columns([1,1], vertical_alignment="center")
    saved = False
    with col1:
        if st.button("Create New User", use_container_width=True, key="save_user"):
            if not email_exists(form_data["email"]):
                try:
                    with get_db() as db:
                        saved = User.create(db, **form_data)
                except Exception as e:
                    st.write(e)
                    st.error(f"Error saving account****: {e}")
            else:
                error = "The email already exist."
    with col2:
        if st.button("Cancel", key="cancel_user", use_container_width=True):
            st.rerun()
    
    if error:
        st.warning(error)
        return
    
    if saved:
        st.success(f"User created successfully!")
        st.session_state.selected_row = {}
        time.sleep(1.5)
        st.rerun()

def show_datatable(create_btn_placeholder):
    action_placeholder = st.empty()
    
    filters = { "active": st.session_state.active_accounts }
    filters = filters if st.session_state.active_accounts in [0,1] else {}
    columns = ["id", "full_name", "role", "email", "active", "created_by", "created_at", "updated_at"]
    
    try:
        df = load_data_with_retry(TABLE_NAME, st.session_state.search_query,
                                 columns, **filters)
    except Exception as e:
        st.write(e)
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()
    
    if not df.empty:
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
        gb.configure_default_column(editable=False, filterable=False, sortable=True, resizable=True, width=250)
        gb.configure_grid_options(domLayout='normal')
        gb.configure_column(field="active", hide=True)
        gb.configure_column(field="id", header_name="ID")
        gb.configure_column(field="email", header_name="Email")
        gb.configure_column(field="full_name", header_name="Full Name")
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
            
        if isinstance(selected_rows, list) and len(selected_rows) > 0:
            st.session_state.selected_row = selected_rows[0]
        else:
            st.session_state.selected_row = {}
        
    # Show action buttons for selected row
    with action_placeholder.container():
        if st.session_state.selected_row:
            record_id = st.session_state.selected_row.get("id")
            if record_id:
                col1, _ = st.columns([1, 1], vertical_alignment="center")
                with col1:
                    if st.session_state.active_accounts:
                        if st.button("Deactivate Account", icon=":material/cancel:", key="deactivate_user_btn"):
                            deactivate_form(record_id)
                    else:
                        if st.button("Activate Account", icon=":material/check:", key="activate_user_btn"):
                            activate_form(record_id)
                        
    with create_btn_placeholder.container():
        if not st.session_state.selected_row :
            if st.button("New Record", key="create", icon=":material/add:", use_container_width=True):
                st.session_state.selected_row = {}
                create_form()  

def reset_params():
    st.session_state.selected_row = {}

@authenticated
def main():
    st.title("User Accounts")
    side_nav()
    init_session_var()
    
    st.write('')
    st.write('')
    st.write('')
    
    col1, col2, col3 = st.columns([0.35, 0.3, 0.15], vertical_alignment="bottom")
    with col1:
        st.text_input(
            "Search Records:",
            placeholder="Type to search...",
            key="search_query", help="Search across all columns"
        )
    with col2:
        st.selectbox(
            "Show Accounts",
            options=[True, False],
            format_func=lambda x: "Active" if x else "Inactive",
            index=0 if st.session_state.active_accounts else 1,
            key="active_accounts",
            on_change=reset_params,
            help=f"Show {'active' if st.session_state.active_accounts else 'inactive'} accounts",
        )
    with col3:
       create_btn_placeholder = st.empty()
    
    st.divider()

    show_datatable(create_btn_placeholder)
        
if __name__ == "__main__":
    init_db()
    st.session_state.current_page = "pages/users.py"
    main()
    
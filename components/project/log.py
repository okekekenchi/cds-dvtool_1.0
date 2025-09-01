import json
import pandas as pd
from datetime import datetime, timedelta, timezone
import streamlit as st
from typing import Final
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from services.checklist_service import load_data_with_retry

TABLE_NAME: Final[str] = "project_logs"
STATUS_OPTIONS = { 1: "Show", 0: "Hide" }
COLUMNS_TO_HIDE: Final[list[str]] = ["id", "data", "description","updated_at"]

def handle_selection_change(selected_rows: list[dict]):
    if 'selected_log' not in st.session_state:
        st.session_state.selected_log = {}
        
    # Convert to list of dicts if it's a DataFrame
    if hasattr(selected_rows, 'to_dict'):
        selected_rows = selected_rows.to_dict('records')

    # Now safely check if we have selected rows
    if isinstance(selected_rows, list) and len(selected_rows) > 0:
        selected_log = selected_rows[0]
        selected_log.update({
            "data": json.loads(selected_log.get('data')),
        })
        
        if st.session_state.selected_log.get('id') != selected_log['id']:
            st.session_state.selected_log = selected_log
            st.session_state.toggle_view = True
            st.rerun()
    else:
        if st.session_state.selected_log != {}:
            if st.session_state.selected_log.get('id'):
                st.session_state.selected_log = {}
                st.session_state.toggle_view = False
            st.rerun()

def findRule(rule_id):
  if st.session_state.all_rules:
    for rule in st.session_state.all_rules:
      if rule["id"] == rule_id:
        return rule
  else:
    return {}

def project_list():
    try:
        st.session_state.data = load_data_with_retry(table=TABLE_NAME)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()
    
    if st.session_state.data.empty:
        return
    
    # Configure tables
    gb = GridOptionsBuilder.from_dataframe(st.session_state.data)
    gb.configure_pagination(paginationAutoPageSize=False)
    gb.configure_default_column(editable=False, filterable=False, sortable=True, resizable=True, width=250)
    gb.configure_grid_options(domLayout='normal')
    gb.configure_column(field="created_by", header_name="Created by")
    gb.configure_column(field="created_by", header_name="Created by")
    gb.configure_column(field="created_at", header_name="Created at", valueFormatter="new Date(data.created_at).toLocaleString()")
    gb.configure_column(field="updated_at", header_name="Updated at", valueFormatter="new Date(data.updated_at).toLocaleString()")
    gb.configure_selection(selection_mode='single', use_checkbox=True)
    
    for column in COLUMNS_TO_HIDE:
        if column in st.session_state.data:
            gb.configure_column(field=column, hide=True)
    
    grid_response = AgGrid(
        st.session_state.data,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        theme='streamlit',
        enable_enterprise_modules=True,
        sidebar=True,
        fit_columns_on_grid_load=True,
        key="checklist_datatable"
    )
    # st.write(grid_response.get("selected_rows"))
    handle_selection_change(grid_response.get("selected_rows"))

def project_detail():
	st.markdown("""
		<div style='display: flex; justify-content: space-between; margin-bottom: 0px;'>
			<h5>Log Details</h5>
		</div>
	""", unsafe_allow_html=True)
	st.divider()
 
	log = st.session_state.selected_log
	st.write(f"**File name:** {log["file_name"]}")
	st.write(f"**Type:** {log["file_type"]}")
	st.write(f"**Version:** {log["version"]}")
 
	timestamp = log["created_at"]
	dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
	dt_utc = dt.replace(tzinfo=timezone.utc)  # Mark as UTC time
	dt_local = dt_utc.astimezone()  # Convert to local timezone

	st.write(f"**Run on:** {dt_local.strftime("%B %d, %Y at %I:%M %p")}")
	st.write(f"**Rules Applied:** ")

	for idx, data in enumerate(log["data"]):
		rule = findRule(data["rule_id"])
		st.write(f"""
			↓\n
			**Rule {idx + 1}: {rule['name']}**\n
				→ Total: {data["total_records"]} records\n
				→ Passed: {data["total_records"] - len(data["failed_df"])} records\n
				→ Failed: {len(data["failed_df"])} records\n
		""")

		if len(data["failed_df"]):
			st.dataframe(data["failed_df"])
		else:
			st.info("There were no failed records for this run")

@st.fragment
def project_log():		
	if "toggle_view" not in st.session_state:
		st.session_state.toggle_view = 0

	st.write("")
	partition = [6,4] if st.session_state.toggle_view else None

	if partition:
		st.markdown("""
			<style>
			.stColumn {
				height: 500px;
				overflow: auto;
				background: white;
				padding: 10px 20px 20px 20px;
				border-radius: 1.5em;
			}
			
			input {
				background: white !important;
			}
			</style>
		"""
		, unsafe_allow_html=True)
  
		col1, col2 = st.columns(partition, vertical_alignment="center")

		with col1:
			project_list()
			
		with col2:
			project_detail()
	else:
		project_list()
  
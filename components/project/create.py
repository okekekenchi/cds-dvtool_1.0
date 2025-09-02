import importlib
import sys
import time

def reload_package(package_name: str):
  for name in list(sys.modules):
    if name == package_name or name.startswith(f"{package_name}."):
      importlib.reload(sys.modules[name])

reload_package("services.workbook_service")
reload_package("services.query_builder_service")

import os
import copy
import pandas as pd
import streamlit as st
from utils import alert
from util.env import EnvHelper
from database.database import get_db
from services.workbook_service import load_data
from services.query_builder_service import load_checklist
from models.validation_checklist import ValidationChecklist
from models.project_log import ProjectLog

def init_session_var():
  if 'all_rules' not in st.session_state:
    with get_db() as db:
      st.session_state.all_rules = ValidationChecklist().all(db, ["id", "name", "code", "config"])
  if 'selected_ids' not in st.session_state:
    st.session_state.selected_ids = []
  if 'project_df' not in st.session_state:
    st.session_state.project_df = pd.DataFrame()

def reset_form():
  return

def file_changed():
  return

def upload_workbook()-> dict:
  """
  Allows users to select a workbook file for validation.
  Joins the master records to the sheets in the workbook.
  Assigns the joined dataframes to the session variable.

  Returns:
      file: byte
  """
  st.markdown("<div><h6>Select Workbook (Excel File) *</h6></div>", unsafe_allow_html=True)
  st.file_uploader(
    "",
    type=["xlsx", "xls"], key="project_file",
    label_visibility="collapsed",
    on_change=file_changed,
  )
    
  if st.session_state.project_file:
    file, sheets, tables = load_data(st.session_state.project_file)
    return sheets | tables
  else:
    st.warning("Select file to continue")
    return {}

def select_rule(id):
  st.session_state.selected_ids.append(id)
  st.rerun(scope="fragment")

def unselect_rule(idx):
  del st.session_state.selected_ids[idx]
  st.rerun(scope="fragment")
  
def can_not_save():
  return not (
    st.session_state.project_file and
    st.session_state.selected_ids
  )
  
def run_query():
  results = []
  input_sheets = copy.deepcopy(st.session_state.all_sheets)

  try:
    for idx, rule_id in enumerate(st.session_state.selected_ids):
      for rule in st.session_state.all_rules:
        if rule["id"] == rule_id:
          result = dict(load_checklist(rule["config"], input_sheets, "all"))
          log = rule["config"].get("log", {})
          selected_columns = log.get("columns", [])
          
          if not selected_columns:
            st.warning(f"No column selection made for rule: **{rule['name']}**")
            
          failed_df = result["failed_df"][selected_columns]

          results.append({
            "rule_id": rule_id,
            "total_records": result["total_records"],
            "join_steps": result["join_steps"],
            "failed_df": failed_df.to_dict(orient='records')
          })
          break

    st.session_state.validation_results = results
    log_error(results)
    st.toast("Validation Successful.", icon=":material/check_circle:")
    st.rerun()
  except Exception as e:
    st.write(e)
    st.warning(f"Check validation rule combination {str(e)}")

def log_error(results:list[dict]):
  file_name = st.session_state.project_file.name
  env = EnvHelper()
  
  project_log = {
    "name": f"{file_name}_{time.time()}",
    "file_name": os.path.splitext(file_name)[0],
    "file_type": os.path.splitext(file_name)[1].lower(),
    "version": env("config.client.version"),
    "data": results,
    "created_by": st.session_state.user_id
  }
  
  try:
    with get_db() as db:
      ProjectLog.create(db, **project_log)
  except Exception as ex:
    st.warning(f"Unable to save log {str(ex)}")

def render_available_rules():
  """Render the available columns section"""
  available_rules = [
    rule for rule in st.session_state.all_rules
    if rule["id"] not in st.session_state.selected_ids
  ]

  st.markdown("""
    <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
        <h5>Available Columns</h5>
        <span style='font-size: 0.9em; color: #666; height: 33px;'>
            {}/{} columns
        </span>
    </div>
  """.format(len(available_rules), len(st.session_state.all_rules)), unsafe_allow_html=True)
  st.divider()
  
  st.text_input(placeholder="Search and click enter", label_visibility="collapsed", label="", key="search_rule")
  available_rules = [
    rule for rule in available_rules
    if st.session_state.search_rule.lower() in str(rule["name"]).lower()
  ]
  
  if available_rules:
    for rule in available_rules:
      if st.checkbox(f"{rule['code']} - {rule['name']}", key=f"avail_{rule['id']}", value=False):
        select_rule(rule["id"])
  else:
    st.info("No available rule.")
  
  st.write("")
  st.write("")
  st.write("___")
  
def render_selected_rules():
  """Render the selected columns section"""
  st.markdown("""
      <div style='display: flex; justify-content: space-between; margin-bottom: 10px;'>
          <h5>Selected Columns</h5>
          <span style='font-size: 0.9em; color: #666; height: 33px;'>
              {}/{} columns
          </span>
      </div>
  """.format(len(st.session_state.selected_ids), len(st.session_state.all_rules)), unsafe_allow_html=True)
  st.divider()
  
  if st.session_state.selected_ids:
    for idx, rule_id in enumerate(st.session_state.selected_ids):
      for rule in st.session_state.all_rules:
        if rule["id"] == rule_id:
          if st.checkbox(f"{rule['code']} - {rule['name']}", key=f"selected_{rule['id']}"):
            unselect_rule(idx)
  else:
    st.info("No rule selected.")
    
  st.write("")
  st.write("")
  st.write("___")

def select_validation_rules():
  available_container, selected_container = st.columns([0.5,0.5])
  
  st.markdown("""
    <style>
      .stColumn {
        height: 500px;
        overflow: auto;
        background: rgb(240, 242, 246);
        padding: 10px 20px 20px 20px;
        border-radius: 1.5em;
      }
      
      input {
        background: white !important;
      }
    </style>
  """
  , unsafe_allow_html=True)
  
  with available_container:
    render_available_rules()
      
  with selected_container:
    render_selected_rules()

@st.fragment
def create_project():
  init_session_var()
  st.session_state['all_sheets'] = upload_workbook()  
  st.divider()
  
  if st.session_state.project_file:
    select_validation_rules()
    st.divider()

  if st.button("Run Check", key="run_query", icon=":material/send:", disabled=can_not_save()):
    if not st.session_state.selected_ids:
      alert("No rule selected.")
      return False
  
    run_query()
  
  st.write("")
  st.write("")

import importlib
import sys

def reload_package(package_name: str):
  for name in list(sys.modules):
    if name == package_name or name.startswith(f"{package_name}."):
      importlib.reload(sys.modules[name])

reload_package("services.workbook_service")
reload_package("services.query_builder_service")

import pandas as pd
import streamlit as st
from utils import alert
from database.database import get_db
from services.workbook_service import load_data
from services.query_builder_service import load_checklist
from models.validation_checklist import ValidationChecklist

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

def upload_workbook():
  st.file_uploader(
    "Select Workbook (Excel File) *",
    type=["xlsx", "xls"], key="project_file",
    help="Upload an Excel workbook containing your data sheets.",
  )
  
  # st.markdown("<style>button { max-width:150px; }</style>", unsafe_allow_html=True)
  
  if st.session_state.project_file:
    file, sheets, tables = load_data(st.session_state.project_file)
    st.session_state['all_sheets'] = sheets | tables
  else:            
    st.warning("Select file to continue")
      
  return st.session_state.project_file

def select_rule(id):
  st.session_state.selected_ids.append(id)
  st.rerun(scope="fragment")

def unselect_rule(idx):
  del st.session_state.selected_ids[idx]
  st.rerun(scope="fragment")
  
def run_query():
  if not st.session_state.selected_ids:
    alert("No rule selected.")
    
  result_df = pd.DataFrame()
  
  for idx, rule_id in enumerate(st.session_state.selected_ids):
    for rule in st.session_state.all_rules:
      if rule["id"] == rule_id:
        if idx == 0:
          result_df = load_checklist(rule["config"],  st.session_state.all_sheets)
        else:
          result_df = load_checklist(rule["config"],  { f'result_{idx}': result_df })
  
  st.write(result_df)
  return result_df

@st.fragment
def select_valudation_rules():
  unselected_container, selected_container = st.columns([0.5,0.5])
  
  st.markdown("""
    <style>
      .stColumn {
        height: 500px;
        overflow: auto;
        background: rgb(240, 242, 246);
        padding: 5px 20px 20px 20px;
        border-radius: 1.5em;
      }
      input {
        background: white !important;
      }
    </style>
  """
  , unsafe_allow_html=True)
  
  with unselected_container:
    available_rules = [
      rule for rule in st.session_state.all_rules
      if rule["id"] not in st.session_state.selected_ids
    ]
  
    st.subheader("Available Rules")
    st.write('')
    st.write('')
    st.write(f"*Check a rule to select it* -  ",
             f"**[{len(available_rules)} of {len(st.session_state.all_rules)} rules]**")
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
      
  with selected_container:
    st.subheader("Selected Rules")
    st.write("")
    st.write("")
    st.write(f"*Check a rule to remove it* - ",
             f"**[{len(st.session_state.selected_ids)} of {len(st.session_state.all_rules)} rules selected]**")
    st.divider()
    
    if st.session_state.selected_ids:
      for idx, rule_id in enumerate(st.session_state.selected_ids):
        for rule in st.session_state.all_rules:
          if rule["id"] == rule_id:
            if st.checkbox(f"{rule['code']} - {rule['name']}", key=f"selected_{rule['id']}"):
              unselect_rule(idx)
    else:
      st.info("No rule selected.")

  if st.button("Run Check", key="run_query", icon=":material/send:"):
    run_query()
    
  st.write("")
  st.write("")
  st.write("")
  
    
def create_project():
  init_session_var()
  
  workbook = upload_workbook()
    
  st.divider()
  
  if workbook:
    select_valudation_rules()
    
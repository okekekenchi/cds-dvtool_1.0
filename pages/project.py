# import importlib
# import sys

# def reload_package(package_name: str):
#     for name in list(sys.modules):
#         if name == package_name or name.startswith(f"{package_name}."):
#             importlib.reload(sys.modules[name])

# reload_package("components.project.create")
# reload_package("components.project.report")
# reload_package("components.project.log")

import streamlit as st
from loader.css_loader import load_css
from database.migration import init_db
from util.auth_utils import authenticated
from components.side_nav import side_nav
from components.project.create import create_project
from components.project.log import project_log
from components.project.report import project_report

st.set_page_config(page_title="Project", page_icon=":material/folder:",
                   layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/project.css')

@authenticated
def main():    
    create_tab, report_tab, log_tab = st.tabs(["Create Project", "Report", "Project Log"])
    
    with create_tab:
        create_project()
          
    with report_tab:
        project_report()
          
    with log_tab:
        project_log()

if __name__ == "__main__":
    init_db()
    st.session_state.current_page = "pages/project.py"
    st.markdown("""<h2>Projects</h2>""", unsafe_allow_html=True)
    side_nav()
    main()
    
import importlib
import sys

def reload_package(package_name: str):
    for name in list(sys.modules):
        if name == package_name or name.startswith(f"{package_name}."):
            importlib.reload(sys.modules[name])

reload_package("components.project")

import streamlit as st
from loader.css_loader import load_css
from database.migration import init_db
from components.side_nav import side_nav
from util.auth_utils import authenticated
from components.project.create import create_project
from components.project.view import view_projects
from components.project.report import project_report

st.set_page_config(page_title="Project", page_icon=":material/folder:",
                   layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/project.css')


@authenticated
def main():
    st.title("Project")
    side_nav()
    
    create, projects, report = st.tabs(["Create Project", "My Projects", "Report"])
    
    with create:
        create_project()
          
    with projects:
        view_projects()
          
    with report:
        project_report()

if __name__ == "__main__":
    init_db()
    st.session_state.current_page = "pages/project.py"
    main()
    
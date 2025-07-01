import config
import streamlit as st
from utils import init_db, hide_nav_and_header, auth
  
def main():
  init_db()
  hide_nav_and_header()
  
  if auth(): # Authenticated
    st.switch_page(st.session_state.current_page or config.ROUTE_HOME)
  else: # Guest
    st.switch_page(config.ROUTE_LOGIN)
    
if __name__ == "__main__":
  main()
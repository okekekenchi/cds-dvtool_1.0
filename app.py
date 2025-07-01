import streamlit as st
from utils import hide_nav_and_header, auth
from loader.config_loader import config
from database.migration import init_db
  
def main():  
  init_db()
  hide_nav_and_header()
    
  if auth(): # Authenticated
    st.switch_page(st.session_state.current_page or config('route.home'))
  else: # Guest
    st.switch_page(config('route.login'))
    
if __name__ == "__main__":
  main()
  

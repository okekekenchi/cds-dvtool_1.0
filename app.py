import streamlit as st
from util.auth_utils import auth
from loader.config_loader import config
from database.migration import init_db

st.markdown("""
  <style>
    section[data-testid="stSidebar"] {
      display: none !important;
    }
    
    .stAppHeader {
      display: none !important;
    }

    header[data-testid="stHeader"] {
        display: none !important;
    }
    footer {
        visibility: hidden;
    }
  </style>
""", unsafe_allow_html=True)

def main():
  init_db()
    
  if auth():
    st.switch_page(st.session_state.current_page or config('route.home'))
  else: # Guest
    st.switch_page(config('route.login'))
    
if __name__ == "__main__":
  main()
  
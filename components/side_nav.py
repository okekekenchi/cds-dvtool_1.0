import streamlit as st
from PIL import Image
from utils import get_user_by_id, logout, auth
import os
import config

PRIMARY_COLOR = "#e83757"
SECONDARY_COLOR = "#381338"
BG_COLOR = "#ffffff"

def side_nav():
    if not auth():
        return

    user = get_user_by_id(st.session_state.user_id)
    
    if not user:
        return
    
    with st.sidebar:
        st.markdown(f"""
            <style>
            .sidebar .sidebar-content {{
                background-color: {SECONDARY_COLOR};
                color: white;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("""
            <style>
                .st-emotion-cache-1iuhdj4 { display: none !important; }
                .st-emotion-cache-8atqhb { justify-items: center !important; }
                hr { margin: 0px !important; }
                .st-emotion-cache-1h08hrp {
                    width: -webkit-fill-available !important;
                    height: 30px !important;
                    min-height: 30px !important;
                    padding: 0px !important;
                    margin: 0px !important;
                }
                .st-emotion-cache-1kwt99k { display: flex !important; height: 30px !important; }
                .st-emotion-cache-1h08hrp > p { margin-top: -9px !important; }
                .st-emotion-cache-595tnf  {
                    right: 0px!important;
                    position: absolute!important;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        user_avatar_path = os.path.join("assets/images", "user_icon.png")
        if os.path.exists(user_avatar_path):
            st.image(Image.open(user_avatar_path), width=100)
        
        
        # User profile section
        st.markdown(f"""
            <p style='text-transform:uppercase; font-size:larger; text-align:center;
                margin:0; color:#4f3f3f; font-family:sans-serif; width: 100%;
                white-space:nowrap; text-overflow:ellipsis; overflow:hidden;'>
                {user[1]}
            </p>
            <p style='text-align:center; font-size:small; font-style:italic; width: 100%;
                white-space:nowrap; text-overflow:ellipsis; overflow:hidden;'>
                <strong>{user[2]}</strong>
            </p>
            """, unsafe_allow_html=True
        )

        # Logout button with icon
        if st.button("Logout", key="logout", icon=":material/logout:", use_container_width=True):
            logout()
            st.switch_page(config.ROUTE_LOGIN)
                    
        st.markdown(
            f"""<hr style="border: 1px solid {PRIMARY_COLOR};"/>""",
            unsafe_allow_html=True
        )        
        
    path = "pages"
    st.sidebar.page_link(f"{path}/3_home.py", label="Dashboard", icon=":material/dashboard:"),
    st.sidebar.page_link(f"{path}/4_project.py", label="My Projects", icon=":material/folder:"),
    st.sidebar.page_link(f"{path}/8_masters.py", label="Masters", icon=":material/settings:"),
    st.sidebar.page_link(f"{path}/5_validation_check.py", label="Validation Checks", icon=":material/check_circle:"),
    st.sidebar.page_link(f"{path}/6_users.py", label="Users", icon=":material/groups:"),                
    st.sidebar.page_link(f"{path}/7_account.py", label="My account", icon=":material/account_circle:"),
        
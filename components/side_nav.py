import streamlit as st
from PIL import Image
from utils import get_user_by_id, logout, auth
import os
from loader.config_loader import config
from loader.css_loader import load_css

PRIMARY_COLOR = "#e83757"
SECONDARY_COLOR = "#381338"
BG_COLOR = "#ffffff"

def side_nav():
    if not auth():
        return

    user = get_user_by_id(st.session_state.user_id)
    
    if not user:
        return
    load_css('assets/css/side_nav.css')
    with st.sidebar:
        st.markdown(f"""
            <style>
            .sidebar .sidebar-content {{
                background-color: {config('theme.secondary')};
                color: white;
            }}
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
                {user.full_name}
            </p>
            <p style='text-align:center; font-size:small; font-style:italic; width: 100%;
                white-space:nowrap; text-overflow:ellipsis; overflow:hidden;'>
                <strong>{user.email}</strong>
            </p>
            """, unsafe_allow_html=True
        )

        # Logout button with icon
        if st.button("Logout", key="logout", icon=":material/logout:", use_container_width=True):
            logout()
            st.switch_page(config('route.login'))
                    
        st.markdown(
            f"""<hr style="border: 1px solid {PRIMARY_COLOR};"/>""",
            unsafe_allow_html=True
        )
        
    path = "pages"
    st.sidebar.page_link(f"{path}/3_home.py", label="Dashboard", icon=":material/dashboard:"),
    st.sidebar.page_link(f"{path}/4_project.py", label="My Projects", icon=":material/folder:"),
    st.sidebar.page_link(f"{path}/8_masters.py", label="Masters", icon=":material/settings:"),
    st.sidebar.page_link(f"{path}/6_users.py", label="Users", icon=":material/groups:"),                
    st.sidebar.page_link(f"{path}/7_account.py", label="My account", icon=":material/account_circle:"),
    
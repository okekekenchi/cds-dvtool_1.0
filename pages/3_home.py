import streamlit as st
from utils import authenticated, logout
from datetime import datetime
import time
import config
from streamlit_extras.colored_header import colored_header
from streamlit_extras.let_it_rain import rain
from PIL import Image
import base64

st.set_page_config(page_title="Dashboard", page_icon=":bar_chart:", layout="wide", initial_sidebar_state="expanded")

PRIMARY_COLOR = "#e83757"
SECONDARY_COLOR = "#381338"
BG_COLOR = "#ffffff"

# Apply CSS styling
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    st.markdown("""
    <style>
        .stMainBlockContainer {
            padding-top: 0px;
        }
        
        iframe {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

@authenticated
def main():
    st.session_state.current_page = config.ROUTE_REGISTER
    
    with st.sidebar:
        st.markdown(
            f"""
            <style>
            .sidebar .sidebar-content {{
                background-color: {SECONDARY_COLOR};
                color: white;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # User profile section
        st.markdown(
            f"""
            <div style="padding: 1rem; border-bottom: 1px solid {PRIMARY_COLOR};">
                <h2 style="color: {PRIMARY_COLOR};">Dashboard User</h2>
                <h3>JOHN DON</h3>
                <p>johndon@company.com</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Navigation links
        nav_options = ["Dashboard", "Users", "Validation Checks", "Projects"]
        selected = st.radio(
            "Navigation",
            nav_options,
            label_visibility="collapsed"
        )
        
        # Logout button with icon
        if st.button("Logout", key="logout"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.markdown(
            """
            <style>
            div[data-testid="stRadio"] div {
                color: white;
            }
            button[kind="secondary"] {
                background-color: #e83757 !important;
                color: white !important;
                border: none;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    # Main content area
    colored_header(
        label=selected,
        description="",
        color_name="red-70"
    )

    # Dashboard content
    if selected == "Dashboard":
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Earning")
            st.markdown(f"<h1 style='color: {PRIMARY_COLOR};'>$ 628</h1>", unsafe_allow_html=True)
            
            metrics = {
                "Share": "2434",
                "Likes": "1259",
                "Rating": "8.5"
            }
            
            for metric, value in metrics.items():
                st.metric(metric, value)
        
        with col2:
            st.subheader("Result")
            st.line_chart([30, 20, 15, 10, 25, 30, 35, 40, 35, 45, 50, 60, 70, 80, 90, 100, 150, 200, 250, 300])
        
        st.markdown("---")
        st.button("Learn More", key="learn")
        st.button("Check Now", key="check")

    elif selected == "Users":
        st.write("Users management content goes here")

    elif selected == "Validation Checks":
        st.write("Validation checks content goes here")

    elif selected == "Projects":
        st.write("Projects content goes here")

    # Add some visual effects
    def add_logo():
        st.markdown(
            """
            <style>
                [data-testid="stSidebarNav"] {
                    background-image: url(https://streamlit.io/images/brand/streamlit-mark-color.png);
                    background-repeat: no-repeat;
                    background-position: 20px 20px;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

    add_logo()

if __name__ == "__main__":
    main()
    
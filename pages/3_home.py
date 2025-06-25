import streamlit as st
from utils import login_required, valid_session, delete_session
from datetime import datetime

# Apply CSS styling
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

@login_required
def main():
    # Page configuration
    st.set_page_config(
        page_title="Dashboard",
        page_icon="🏠",
        layout="centered"
    )

    # Sidebar - Only visible to authenticated users
    with st.sidebar:
        st.title(f"Welcome, {st.session_state.user_name}!")
        st.markdown(f"Logged in as: `{st.session_state.user_email}`")
        
        # Session information
        st.divider()
        st.markdown("**Session Information**")
        st.write(f"Last login: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Logout button
        if st.button("Logout", type="primary", use_container_width=True):
            delete_session(st.session_state.session_id)
            st.session_state.clear()
            st.success("Logged out successfully!")
            st.switch_page("pages/1_login.py")

    # Main content area
    st.title(f"Dashboard Overview")
    st.markdown(f'<div class="container">', unsafe_allow_html=True)
    
    # Welcome message
    st.subheader(f"Hello, {st.session_state.user_name}!")
    st.markdown("""
        Welcome to your personalized dashboard. Here's what's happening today:
    """)
    
    # Sample dashboard content
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown("### Your Stats")
            st.metric("Active Projects", "3", "+1 from last week")
            st.metric("Tasks Completed", "12", "80% completion rate")
    
    with col2:
        with st.container(border=True):
            st.markdown("### Recent Activity")
            st.write("✔️ Completed project setup")
            st.write("📅 Meeting at 2:00 PM today")
            st.write("🔔 3 new notifications")

    # Additional content sections
    st.divider()
    st.markdown("### Quick Actions")
    action_cols = st.columns(3)
    with action_cols[0]:
        if st.button("Create New Project", use_container_width=True):
            st.info("Project creation would be implemented here")
    with action_cols[1]:
        if st.button("View Reports", use_container_width=True):
            st.info("Reports would be implemented here")
    with action_cols[2]:
        if st.button("Account Settings", use_container_width=True):
            st.info("Settings would be implemented here")

    st.markdown('</div>', unsafe_allow_html=True)



if __name__ == "__main__":
    # Additional session validation on page load
    if 'session_id' not in st.session_state or not valid_session(st.session_state.session_id):
        # st.session_state.clear()
        # st.switch_page("pages/1_login.py")
        st.title("How are you")
    else:
        main()
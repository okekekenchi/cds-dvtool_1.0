import streamlit as st
from models.user import User
from database.database import get_db
from database.migration import init_db
from loader.css_loader import load_css
from utils import format_datetime,alert
from components.side_nav import side_nav
from util.auth_utils import authenticated
from util.auth_utils import get_user_by_id, change_password, is_password_strong

st.set_page_config(page_title="Account Settings", page_icon=":material/settings:",
                   layout="wide", initial_sidebar_state="expanded")
load_css('assets/css/account.css')

def init_session_var():
    if "reset_inputs" not in st.session_state:
        st.session_state.reset_inputs = False

def view_profile(user):
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Personal Information**")
        st.metric("Full Name", user.full_name)
        st.metric("Email", user.email)
    
    with col2:
        st.info("**Account Details**")
        st.metric("Role", user.role.capitalize())
        st.metric("Joined Since", format_datetime(str(user.created_at)))
        # st.metric("Last Login", user.last_login)
        st.metric("Last Updated", format_datetime(str(user.updated_at)))

def reset_form():
    st.session_state.update({
        "current": None,
        "new": None,
        "confirm": None
    })
    
def save_personal_data(old_name, new_name):
    if not new_name:
        return
    
    if old_name == new_name:
        return
    
    with get_db() as db:
        updated = User.update(db, st.session_state.user_id, { "full_name": new_name })
    
    if updated:
        st.toast("Record created successfully", icon=":material/check_circle:")
        st.rerun()
    else:
        alert('Error: Could not update record')

def edit_profile(user):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""<h5> Personal Info </h5>""", unsafe_allow_html=True)
        
    with col2:
        st.markdown("""<h5> Change Password </h5>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, border=True)
    with col1:
        new_full_name = st.text_input(
            "Full Name *", value=user.full_name,
            placeholder="Enter your full name"
        )
    
        st.text_input(
            "Email", value=user.email,
            disabled=True, help="Email cannot be changed"
        )
        
        if st.button("Update Personal Info", key="update_personal_info", icon=":material/save:"):
            save_personal_data(user.full_name, new_full_name)
    
    with col2:
        if st.session_state.reset_inputs:
            reset_form()
            st.session_state.reset_inputs = False
            
        st.text_input(
            "Current Password *", type="password",
            placeholder="Enter current password to verify", key="current"
        )
        
        st.text_input(
            "New Password *", type="password",
            placeholder="Enter new password", key="new"
        )
        
        st.text_input(
            "Confirm New Password *", type="password",
            placeholder="Confirm new password", key="confirm"
        )
        
        password = {
            "current": st.session_state.current,
            "new": st.session_state.new,
            "confirm": st.session_state.confirm
        }
        
        if st.button("Change Password", key="change_pword_btn", icon=":material/save:"):
            if password["confirm"] and password["current"] and password["new"]:
                if password["confirm"] == password["new"]:
                    is_strong, pwd_msg = is_password_strong(password["new"])
                    if is_strong:
                        change_password(user.id, password)
                        st.session_state.reset_inputs = True
                        st.rerun()
                    else:
                        st.warning(pwd_msg)
                else:
                    st.warning("Password mismatch")
            else:
                st.warning("Fill all required fields")

@authenticated
def main():
    init_session_var()
        
    tab1, tab2 = st.tabs(["View Profile", "Edit Profile"])
    user = get_user_by_id(st.session_state.user_id)
    
    with tab1:
        view_profile(user)
    
    with tab2:
        edit_profile(user)

if __name__ == "__main__":
    init_db()
    st.session_state.current_page = "pages/account.py"
    st.markdown("""<h2>My Account</h2>""", unsafe_allow_html=True)
    side_nav()
    main()
    
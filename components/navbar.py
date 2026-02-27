import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

"""components/navbar.py — Role-aware sidebar navigation."""
import streamlit as st
from auth import get_current_user, clear_session


def render_navbar() -> None:
    user = get_current_user()
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">🏥 AI Clinical DSS</div>',
            unsafe_allow_html=True,
        )
        st.divider()

        if user:
            st.markdown(f"👤 **{user['name']}**")
            st.caption(f"Role: {user['role'].title()}")
            st.divider()

            role = user["role"]
            if role == "patient":
                st.page_link("pages/4_Patient_Dashboard.py", label="📊 My Dashboard")
                st.page_link("pages/7_Assessment.py",        label="📋 New Assessment")
            elif role == "doctor":
                st.page_link("pages/5_Doctor_Dashboard.py",  label="🩺 Doctor Dashboard")
            elif role == "admin":
                st.page_link("pages/6_Admin_Dashboard.py",   label="⚙️ Admin Dashboard")
                st.page_link("pages/5_Doctor_Dashboard.py",  label="🩺 Doctor View")

            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                clear_session()
                st.switch_page("pages/2_Login.py")
        else:
            st.page_link("pages/1_Landing.py",  label="🏠 Home")
            st.page_link("pages/2_Login.py",    label="🔑 Login")
            st.page_link("pages/3_Register.py", label="📝 Register")

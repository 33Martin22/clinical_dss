"""pages/2_Login.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database import init_db
from auth     import seed_defaults, login_user, set_session, get_current_user
from utils    import global_css
from components.navbar import render_navbar

st.set_page_config(page_title="Login | AI Clinical DSS", page_icon="🔑", layout="wide")
init_db(); seed_defaults(); global_css(); render_navbar()

# Redirect if already logged in
user = get_current_user()
if user:
    dest = {
        "patient": "pages/4_Patient_Dashboard.py",
        "doctor":  "pages/5_Doctor_Dashboard.py",
        "admin":   "pages/6_Admin_Dashboard.py",
    }.get(user["role"], "pages/4_Patient_Dashboard.py")
    st.switch_page(dest)

_, mid, _ = st.columns([1, 1.8, 1])
with mid:
    st.markdown(
        "<h1 style='text-align:center;color:#1e1b4b;margin-bottom:.2rem'>🔑 Welcome Back</h1>"
        "<p style='text-align:center;color:#64748b;margin-bottom:1.5rem'>"
        "Sign in to your account</p>",
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        email    = st.text_input("Email Address", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button(
            "Sign In →", use_container_width=True, type="primary"
        )

    if submitted:
        if not email or not password:
            st.error("Please enter both email and password.")
        else:
            with st.spinner("Authenticating…"):
                u, err = login_user(email, password)
            if err:
                st.error(f"❌ {err}")
            else:
                set_session(u)
                st.success(f"✅ Welcome back, {u.name}!")
                dest = {
                    "patient": "pages/4_Patient_Dashboard.py",
                    "doctor":  "pages/5_Doctor_Dashboard.py",
                    "admin":   "pages/6_Admin_Dashboard.py",
                }.get(u.role, "pages/4_Patient_Dashboard.py")
                st.switch_page(dest)

    st.markdown("---")
    st.markdown("New to the platform?")
    if st.button("Create an Account →", use_container_width=True):
        st.switch_page("pages/3_Register.py")

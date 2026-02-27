"""pages/3_Register.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database import init_db
from auth     import seed_defaults, register_user, set_session, get_current_user
from utils    import global_css
from components.navbar import render_navbar

st.set_page_config(page_title="Register | AI Clinical DSS", page_icon="📝", layout="wide")
init_db(); seed_defaults(); global_css(); render_navbar()

user = get_current_user()
if user:
    st.switch_page("pages/4_Patient_Dashboard.py")

_, mid, _ = st.columns([1, 2, 1])
with mid:
    st.markdown(
        "<h1 style='text-align:center;color:#1e1b4b;margin-bottom:.2rem'>📝 Create Account</h1>"
        "<p style='text-align:center;color:#64748b;margin-bottom:1.5rem'>"
        "Join the platform</p>",
        unsafe_allow_html=True,
    )

    role = st.selectbox(
        "Account Type", ["patient", "doctor"],
        format_func=str.title,
    )

    with st.form("register_form"):
        name  = st.text_input("Full Name",
                              placeholder="Dr. Jane Smith" if role == "doctor" else "John Doe")
        email = st.text_input("Email Address", placeholder="you@example.com")
        pw1   = st.text_input("Password",          type="password",
                              placeholder="Minimum 8 characters")
        pw2   = st.text_input("Confirm Password",  type="password",
                              placeholder="Repeat your password")

        age, gender, conditions = None, None, None
        if role == "patient":
            st.markdown("#### 🩺 Health Profile")
            age        = st.number_input("Age", min_value=1, max_value=120, value=35)
            gender     = st.selectbox("Gender",
                                      ["Male", "Female", "Other", "Prefer not to say"])
            conditions = st.text_area(
                "Underlying Conditions (if any)", height=80,
                placeholder="e.g. Hypertension, Type 2 Diabetes, COPD…",
            )

        submitted = st.form_submit_button(
            "Create Account →", use_container_width=True, type="primary"
        )

    if submitted:
        if not all([name, email, pw1, pw2]):
            st.error("Please fill in all required fields.")
        elif pw1 != pw2:
            st.error("Passwords do not match.")
        elif len(pw1) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            with st.spinner("Creating your account…"):
                u, err = register_user(
                    name=name, email=email, password=pw1, role=role,
                    age=age, gender=gender, conditions=conditions,
                )
            if err:
                st.error(f"❌ {err}")
            else:
                set_session(u)
                st.success("✅ Account created! Redirecting…")
                dest = (
                    "pages/4_Patient_Dashboard.py"
                    if role == "patient"
                    else "pages/5_Doctor_Dashboard.py"
                )
                st.switch_page(dest)

    st.markdown("---")
    st.markdown("Already have an account?")
    if st.button("Sign In →", use_container_width=True):
        st.switch_page("pages/2_Login.py")

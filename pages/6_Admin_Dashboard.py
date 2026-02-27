"""pages/6_Admin_Dashboard.py — Admin dashboard."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from database import init_db, get_db, User, Patient, Assessment, AuditLog
from auth     import seed_defaults, require_auth, log_action
from utils    import global_css, kpi
from components.navbar import render_navbar
from components.charts import risk_distribution_pie

st.set_page_config(
    page_title="Admin Dashboard | AI Clinical DSS",
    page_icon="⚙️", layout="wide",
)
init_db(); seed_defaults(); global_css(); render_navbar()

user = require_auth(allowed_roles=["admin"])

with get_db() as db:

    all_users = db.query(User).all()
    patients  = [u for u in all_users if u.role == "patient"]
    doctors   = [u for u in all_users if u.role == "doctor"]
    admins_   = [u for u in all_users if u.role == "admin"]
    all_asms  = db.query(Assessment).all()
    inactive  = [u for u in all_users if not u.is_active]

    rc = {"Low": 0, "Medium": 0, "High": 0}
    for a in all_asms:
        rc[a.final_risk] = rc.get(a.final_risk, 0) + 1

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("# ⚙️ Admin Dashboard")
    st.caption(f"System Administrator: {user['name']}")
    st.divider()

    # ── KPI cards ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(kpi(len(all_users),  "Total Users",        "#4f46e5"), unsafe_allow_html=True)
    c2.markdown(kpi(len(patients),   "Patients",           "#0891b2"), unsafe_allow_html=True)
    c3.markdown(kpi(len(doctors),    "Doctors",            "#16a34a"), unsafe_allow_html=True)
    c4.markdown(kpi(len(all_asms),   "Assessments",        "#7c3aed"), unsafe_allow_html=True)
    c5.markdown(kpi(len(inactive),   "Inactive Accounts",  "#dc2626"), unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🥧 Risk Distribution")
        st.plotly_chart(risk_distribution_pie(rc), use_container_width=True)
    with col2:
        st.markdown("### 👥 User Role Breakdown")
        fig = go.Figure(go.Bar(
            x=["Patients", "Doctors", "Admins"],
            y=[len(patients), len(doctors), len(admins_)],
            marker_color=["#4f46e5", "#16a34a", "#d97706"],
            text=[len(patients), len(doctors), len(admins_)],
            textposition="auto",
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── User management ───────────────────────────────────────────────────────
    st.markdown("### 👥 User Management")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_role = st.selectbox(
            "Filter by role", ["All", "patient", "doctor", "admin"]
        )
    with col_f2:
        search = st.text_input("Search name or email", placeholder="Type to search…")

    filtered_users = [
        u for u in all_users
        if (filter_role == "All" or u.role == filter_role)
        and (
            not search
            or search.lower() in u.name.lower()
            or search.lower() in u.email.lower()
        )
    ]

    for u in filtered_users:
        status_icon = "✅" if u.is_active else "❌"
        with st.expander(
            f"{status_icon} {u.name} ({u.role.title()}) — {u.email}"
        ):
            ci, ca = st.columns([3, 1])
            with ci:
                st.write(f"**ID:** {u.id}  |  **Email:** {u.email}")
                st.write(f"**Role:** {u.role.title()}  |  "
                         f"**Status:** {'Active ✅' if u.is_active else 'Inactive ❌'}")
                ds = u.created_at.strftime("%b %d, %Y") if u.created_at else "N/A"
                st.write(f"**Created:** {ds}")
            with ca:
                if u.id != user["id"]:
                    label    = "🔒 Deactivate" if u.is_active else "🔓 Activate"
                    btn_type = "secondary" if u.is_active else "primary"
                    if st.button(label, key=f"tog_{u.id}", type=btn_type,
                                 use_container_width=True):
                        u.is_active = not u.is_active
                        db.commit()
                        action = "DEACTIVATE_USER" if not u.is_active else "ACTIVATE_USER"
                        log_action(user["id"], action, u.email)
                        st.rerun()
                else:
                    st.caption("(Your account)")

    st.divider()

    # ── Audit logs ────────────────────────────────────────────────────────────
    st.markdown("### 📋 Recent Audit Logs (last 100 entries)")
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(100)
        .all()
    )
    if logs:
        rows = []
        for lg in logs:
            lu = db.query(User).filter(User.id == lg.user_id).first()
            ts = lg.timestamp.strftime("%b %d, %Y %H:%M") if lg.timestamp else "N/A"
            rows.append({
                "Time":    ts,
                "User":    lu.name  if lu else "System",
                "Role":    lu.role.title() if lu else "—",
                "Action":  lg.action,
                "Details": (lg.details or "")[:100],
            })
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No audit log entries yet.")

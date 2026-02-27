"""pages/5_Doctor_Dashboard.py — Doctor dashboard."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database import init_db, get_db, Patient, Assessment, DoctorNote, User
from auth     import seed_defaults, require_auth, log_action
from utils    import global_css, kpi
from components.navbar import render_navbar
from components.charts import risk_distribution_pie, risk_trend_chart
from components.alerts import show_risk_alert

st.set_page_config(
    page_title="Doctor Dashboard | AI Clinical DSS",
    page_icon="🩺", layout="wide",
)
init_db(); seed_defaults(); global_css(); render_navbar()

user = require_auth(allowed_roles=["doctor", "admin"])

with get_db() as db:

    all_patients    = db.query(Patient).all()
    all_assessments = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
    pending_list    = [a for a in all_assessments if a.status == "pending"]
    high_list       = [a for a in all_assessments if a.final_risk == "High"]

    rc = {"Low": 0, "Medium": 0, "High": 0}
    for a in all_assessments:
        rc[a.final_risk] = rc.get(a.final_risk, 0) + 1

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("# 🩺 Doctor Dashboard")
    st.caption(f"Welcome, Dr. {user['name']} · Role: {user['role'].title()}")
    st.divider()

    # ── KPI cards ─────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi(len(all_patients),    "Total Patients",    "#4f46e5"), unsafe_allow_html=True)
    c2.markdown(kpi(len(pending_list),    "Pending Reviews",   "#d97706"), unsafe_allow_html=True)
    c3.markdown(kpi(len(high_list),       "High Risk Alerts",  "#dc2626"), unsafe_allow_html=True)
    c4.markdown(kpi(len(all_assessments), "Total Assessments", "#0891b2"), unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🥧 Risk Distribution")
        st.plotly_chart(risk_distribution_pie(rc), use_container_width=True)
    with col2:
        st.markdown("### 📈 Recent Trend (last 30 assessments)")
        st.plotly_chart(risk_trend_chart(all_assessments[:30]), use_container_width=True)

    st.divider()

    # ── Pending reviews ───────────────────────────────────────────────────────
    st.markdown("### ⏳ Pending Reviews")

    filter_risk = st.selectbox("Filter by risk level", ["All", "High", "Medium", "Low"])
    filtered = [
        a for a in pending_list
        if filter_risk == "All" or a.final_risk == filter_risk
    ]

    if not filtered:
        st.success("✅ No pending reviews — all assessments have been reviewed!")
    else:
        for a in filtered:
            pat     = db.query(Patient).filter(Patient.id == a.patient_id).first()
            pat_usr = db.query(User).filter(User.id == pat.user_id).first() if pat else None
            pname   = pat_usr.name if pat_usr else "Unknown Patient"
            ds      = a.created_at.strftime("%b %d, %Y %H:%M") if a.created_at else "N/A"

            with st.expander(
                f"🔔 {pname} — Risk: **{a.final_risk}** — {ds}"
            ):
                col_v, col_n = st.columns([2, 1])

                with col_v:
                    show_risk_alert(a.final_risk, a.recommendation)
                    v1, v2, v3 = st.columns(3)
                    v1.metric("Resp Rate",   f"{a.respiratory_rate} /min")
                    v1.metric("SpO₂",       f"{a.oxygen_saturation}%")
                    v2.metric("Sys BP",      f"{a.systolic_bp} mmHg")
                    v2.metric("Heart Rate",  f"{a.heart_rate} bpm")
                    v3.metric("Temperature", f"{a.temperature} °C")
                    v3.metric("On O₂",      "Yes" if a.on_oxygen else "No")

                    with st.expander("📖 AI Explanation & SHAP Analysis"):
                        st.markdown(a.explanation)

                with col_n:
                    st.markdown("#### 📝 Add Clinical Note")
                    note_txt = st.text_area(
                        "Your clinical note",
                        key=f"note_{a.id}",
                        height=140,
                        placeholder="Enter your clinical observations, diagnosis, and recommendations…",
                    )
                    if st.button(
                        "✅ Submit Note & Mark Reviewed",
                        key=f"btn_{a.id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        if not note_txt.strip():
                            st.error("Please enter a clinical note before submitting.")
                        else:
                            db.add(DoctorNote(
                                assessment_id = a.id,
                                doctor_id     = user["id"],
                                note          = note_txt.strip(),
                            ))
                            a.status = "reviewed"
                            db.commit()
                            log_action(
                                user["id"], "REVIEW_ASSESSMENT",
                                f"Reviewed assessment #{a.id} for patient {pname}",
                            )
                            st.success("✅ Note submitted and assessment marked as reviewed.")
                            st.rerun()

    st.divider()

    # ── All patients ──────────────────────────────────────────────────────────
    st.markdown("### 👥 All Patients")
    for pat in all_patients:
        pu   = db.query(User).filter(User.id == pat.user_id).first()
        pn   = pu.name if pu else "Unknown"
        pasm = (
            db.query(Assessment)
            .filter(Assessment.patient_id == pat.id)
            .order_by(Assessment.created_at.desc())
            .all()
        )
        lr = pasm[0].final_risk if pasm else "No data"
        lc = {"Low": "✅", "Medium": "⚠️", "High": "🚨"}.get(lr, "❓")

        with st.expander(
            f"{lc} {pn} — Latest risk: {lr} — {len(pasm)} total assessments"
        ):
            if pu:
                st.caption(
                    f"Email: {pu.email} · Age: {pat.age or 'N/A'} · "
                    f"Gender: {pat.gender or 'N/A'}"
                )
                st.caption(f"Conditions: {pat.underlying_conditions or 'None recorded'}")
            if pasm:
                st.plotly_chart(risk_trend_chart(pasm), use_container_width=True)
            else:
                st.info("No assessments submitted yet.")

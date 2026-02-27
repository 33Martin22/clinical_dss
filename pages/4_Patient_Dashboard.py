"""pages/4_Patient_Dashboard.py — Patient dashboard."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database import init_db, get_db, Patient, Assessment, DoctorNote, User
from auth     import seed_defaults, require_auth
from utils    import global_css, kpi
from components.navbar       import render_navbar
from components.alerts       import show_risk_alert
from components.charts       import (risk_trend_chart, risk_distribution_pie,
                                     vitals_radar, ml_probability_bar, shap_bar_chart)
from components.pdf_generator import generate_assessment_pdf

st.set_page_config(
    page_title="Patient Dashboard | AI Clinical DSS",
    page_icon="📊", layout="wide",
)
init_db(); seed_defaults(); global_css(); render_navbar()

user = require_auth(allowed_roles=["patient"])

with get_db() as db:
    patient = db.query(Patient).filter(Patient.user_id == user["id"]).first()
    if not patient:
        st.error("Patient profile not found. Please contact the administrator.")
        st.stop()

    assessments = (
        db.query(Assessment)
        .filter(Assessment.patient_id == patient.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )
    latest = assessments[0] if assessments else None

    # Pre-fetch doctor notes for latest (inside the session)
    latest_notes = []
    if latest:
        latest_notes = (
            db.query(DoctorNote, User)
            .join(User, DoctorNote.doctor_id == User.id)
            .filter(DoctorNote.assessment_id == latest.id)
            .all()
        )

    # Snapshot data needed after session closes
    pat_age        = patient.age
    pat_gender     = patient.gender
    pat_conditions = patient.underlying_conditions
    pat_id         = patient.id

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown("# 📊 My Health Dashboard")
    st.caption(
        f"👤 {user['name']} · Age: {pat_age or 'N/A'} · "
        f"Gender: {pat_gender or 'N/A'} · "
        f"Conditions: {pat_conditions or 'None recorded'}"
    )

    if st.button("➕ New Assessment", type="primary"):
        st.switch_page("pages/7_Assessment.py")

    st.divider()

    # ── KPI cards ─────────────────────────────────────────────────────────────
    total   = len(assessments)
    pending = sum(1 for a in assessments if a.status == "pending")
    rc = {"Low": 0, "Medium": 0, "High": 0}
    for a in assessments:
        rc[a.final_risk] = rc.get(a.final_risk, 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi(total,      "Total Assessments", "#4f46e5"), unsafe_allow_html=True)
    c2.markdown(kpi(pending,    "Pending Review",    "#d97706"), unsafe_allow_html=True)
    c3.markdown(kpi(rc["Low"],  "Low Risk",          "#16a34a"), unsafe_allow_html=True)
    c4.markdown(kpi(rc["High"], "High Risk",         "#dc2626"), unsafe_allow_html=True)

    st.divider()

    # ── Latest assessment ─────────────────────────────────────────────────────
    if latest:
        col_l, col_r = st.columns([3, 2])

        with col_l:
            st.markdown("### 📋 Latest Assessment")
            show_risk_alert(latest.final_risk, latest.recommendation)

            m1, m2, m3 = st.columns(3)
            m1.metric("NEWS2 Score",   latest.rule_score)
            m2.metric("AI Prediction", latest.ml_prediction)
            m3.metric("Final Risk",    latest.final_risk)

            with st.expander("📖 Full Clinical Explanation", expanded=False):
                st.markdown(latest.explanation)

            st.caption(
                f"Submitted: "
                f"{latest.created_at.strftime('%B %d, %Y at %H:%M') if latest.created_at else 'N/A'}"
                f" · Status: **{latest.status.title()}**"
            )

            # Doctor notes
            if latest_notes:
                st.markdown("#### 🩺 Doctor Feedback")
                for note, doc in latest_notes:
                    ds = note.created_at.strftime("%b %d, %Y") if note.created_at else ""
                    st.info(f"**Dr. {doc.name}** ({ds}):\n\n{note.note}")
            else:
                st.caption("⏳ Awaiting physician review…")

            # PDF download
            patient_info_dict = {
                "name":       user["name"],
                "email":      user["email"],
                "age":        pat_age,
                "gender":     pat_gender,
                "conditions": pat_conditions,
            }
            assessment_dict = {
                "id":                latest.id,
                "final_risk":        latest.final_risk,
                "rule_risk":         latest.final_risk,
                "respiratory_rate":  latest.respiratory_rate,
                "oxygen_saturation": latest.oxygen_saturation,
                "o2_scale":          latest.o2_scale,
                "systolic_bp":       latest.systolic_bp,
                "heart_rate":        latest.heart_rate,
                "temperature":       latest.temperature,
                "consciousness":     latest.consciousness,
                "on_oxygen":         latest.on_oxygen,
                "rule_score":        latest.rule_score,
                "ml_prediction":     latest.ml_prediction,
                "ml_probability":    latest.ml_probability,
                "explanation":       latest.explanation,
                "recommendation":    latest.recommendation,
            }
            notes_list = [
                {
                    "doctor_name": doc.name,
                    "created_at":  note.created_at.strftime("%b %d, %Y")
                                   if note.created_at else "",
                    "note":        note.note,
                }
                for note, doc in latest_notes
            ]
            pdf_bytes = generate_assessment_pdf(
                patient_info_dict, assessment_dict, notes_list
            )
            st.download_button(
                "📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"assessment_{latest.id}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        with col_r:
            st.markdown("### 🕸️ Vitals Radar")
            st.plotly_chart(vitals_radar({
                "respiratory_rate": latest.respiratory_rate,
                "oxygen_saturation": latest.oxygen_saturation,
                "systolic_bp":      latest.systolic_bp,
                "heart_rate":       latest.heart_rate,
                "temperature":      latest.temperature,
            }), use_container_width=True)

            if latest.ml_probability:
                ml_prob_val = latest.ml_probability
                st.metric("AI Confidence", f"{ml_prob_val:.1%}")
    else:
        st.info("📭 No assessments yet. Click **New Assessment** above to get started.")

    st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    if assessments:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📈 Risk Trend Over Time")
            st.plotly_chart(risk_trend_chart(assessments), use_container_width=True)
        with col2:
            st.markdown("### 🥧 Risk Distribution")
            st.plotly_chart(risk_distribution_pie(rc), use_container_width=True)

        # ── Assessment history ────────────────────────────────────────────────
        st.markdown("### 📋 Full Assessment History")
        for a in assessments:
            ds   = a.created_at.strftime("%b %d, %Y %H:%M") if a.created_at else "N/A"
            icon = {"Low": "✅", "Medium": "⚠️", "High": "🚨"}.get(a.final_risk, "❓")
            with st.expander(
                f"{icon} Assessment #{a.id} — {ds} "
                f"| Risk: {a.final_risk} | {a.status.title()}"
            ):
                v1, v2, v3 = st.columns(3)
                v1.metric("Resp Rate",   f"{a.respiratory_rate} /min")
                v1.metric("SpO₂",       f"{a.oxygen_saturation}%")
                v2.metric("Systolic BP", f"{a.systolic_bp} mmHg")
                v2.metric("Heart Rate",  f"{a.heart_rate} bpm")
                v3.metric("Temperature", f"{a.temperature} °C")
                v3.metric("Consciousness", a.consciousness)
                prob_val = a.ml_probability or 0.0
                st.caption(
                    f"NEWS2 Score: {a.rule_score} · "
                    f"AI: {a.ml_prediction} ({prob_val:.1%} confidence)"
                )
                st.markdown(f"**Recommendation:** {a.recommendation}")

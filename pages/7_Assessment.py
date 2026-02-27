"""pages/7_Assessment.py — Guided vital signs assessment form."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database    import init_db, get_db, Patient, Assessment
from auth        import seed_defaults, require_auth, log_action
from utils       import global_css, validate_hard, validate_soft
from components.navbar  import render_navbar
from components.alerts  import show_risk_alert, show_clinical_warnings
from components.charts  import ml_probability_bar, shap_bar_chart
from risk_engine        import run_full_assessment

st.set_page_config(
    page_title="Assessment | AI Clinical DSS",
    page_icon="📋", layout="wide",
)
init_db(); seed_defaults(); global_css(); render_navbar()

user = require_auth(allowed_roles=["patient"])

with get_db() as db:
    patient = db.query(Patient).filter(Patient.user_id == user["id"]).first()
    if not patient:
        st.error("Patient profile not found. Please contact the administrator.")
        st.stop()
    patient_id = patient.id

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("# 📋 New Health Assessment")
st.markdown(
    "Enter your current vital signs accurately. All fields are required. "
    "Your assessment will be **automatically forwarded to your doctor** for mandatory review."
)
st.divider()

# ── Measurement guide ─────────────────────────────────────────────────────────
with st.expander("ℹ️ How to measure your vitals correctly", expanded=False):
    st.markdown("""
| Vital Sign | Normal Range | How to Measure |
|-----------|-------------|----------------|
| **Respiratory Rate** | 12–20 breaths/min | Count chest rises for exactly 60 seconds |
| **Oxygen Saturation (SpO₂)** | 95–100% | Pulse oximeter fingertip clip |
| **Systolic Blood Pressure** | 90–120 mmHg | Top number on blood pressure monitor |
| **Heart Rate** | 60–100 bpm | Pulse oximeter or count wrist pulse for 60s |
| **Temperature** | 36.0–37.5 °C | Oral thermometer in degrees Celsius |
| **Consciousness (ACVPU)** | Alert (A) | See scale below |

**ACVPU Consciousness Scale:**
- **A** = Alert: fully awake, aware, and responding normally
- **C** = Confused: awake but disoriented or confused
- **V** = Voice: only responds when spoken to
- **P** = Pain: only responds to painful stimulus
- **U** = Unresponsive: no response to any stimulus
    """)

# ── Assessment form ───────────────────────────────────────────────────────────
with st.form("assessment_form", clear_on_submit=False):

    # Respiratory & Oxygen
    st.markdown("### 🫁 Respiratory & Oxygen Status")
    c1, c2, c3 = st.columns(3)
    with c1:
        rr   = st.number_input("Respiratory Rate (breaths/min)",
                               min_value=1, max_value=100, value=18, step=1)
    with c2:
        spo2 = st.number_input("Oxygen Saturation — SpO₂ (%)",
                               min_value=50, max_value=100, value=98, step=1)
    with c3:
        o2s  = st.selectbox(
            "O₂ Measurement Scale", [1, 2],
            format_func=lambda x: (
                "Scale 1 — Standard (most patients)"
                if x == 1
                else "Scale 2 — COPD / Hypercapnic respiratory failure"
            ),
        )
    on_o2 = st.checkbox(
        "☑️ I am currently using supplemental oxygen (nasal cannula, mask, etc.)"
    )

    # Cardiovascular
    st.markdown("### 💓 Cardiovascular")
    c4, c5 = st.columns(2)
    with c4:
        sbp = st.number_input("Systolic Blood Pressure (mmHg)",
                              min_value=50, max_value=300, value=120, step=1)
    with c5:
        hr  = st.number_input("Heart Rate (bpm)",
                              min_value=20, max_value=250, value=75, step=1)

    # Temperature & Consciousness
    st.markdown("### 🌡️ Temperature & Consciousness")
    c6, c7 = st.columns(2)
    with c6:
        temp = st.number_input("Body Temperature (°C)",
                               min_value=30.0, max_value=44.0,
                               value=37.0, step=0.1, format="%.1f")
    with c7:
        cons = st.selectbox(
            "Level of Consciousness (ACVPU Scale)",
            ["A", "C", "V", "P", "U"],
            format_func=lambda x: {
                "A": "A — Alert: fully awake and oriented",
                "C": "C — Confused: awake but disoriented",
                "V": "V — Voice: responds only to voice",
                "P": "P — Pain: responds only to painful stimulus",
                "U": "U — Unresponsive: no response to any stimulus",
            }[x],
        )

    st.divider()
    st.warning(
        "⚠️ **Declaration:** By submitting this form you confirm that all readings above "
        "are accurate to the best of your knowledge. This assessment will be "
        "**mandatorily and automatically** sent to your doctor for review."
    )
    submitted = st.form_submit_button(
        "🚀 Submit Assessment for AI Analysis",
        use_container_width=True,
        type="primary",
    )

# ── Processing ────────────────────────────────────────────────────────────────
if submitted:
    vitals = {
        "respiratory_rate":  rr,
        "oxygen_saturation": spo2,
        "o2_scale":          o2s,
        "systolic_bp":       sbp,
        "heart_rate":        hr,
        "temperature":       temp,
        "consciousness":     cons,
        "on_oxygen":         1 if on_o2 else 0,
    }

    # Hard validation — block impossible values
    hard_errors = validate_hard(vitals)
    if hard_errors:
        for e in hard_errors:
            st.error(f"❌ {e}")
        st.stop()

    # Soft warnings — show but proceed
    soft_warnings = validate_soft(vitals)
    show_clinical_warnings(soft_warnings)

    # Run hybrid assessment
    with st.spinner("🤖 Running hybrid AI risk analysis — NEWS2 rules + Keras DNN…"):
        result = run_full_assessment(vitals)

    # Persist to PostgreSQL (mandatory — no bypass)
    with get_db() as db:
        new_a = Assessment(
            patient_id        = patient_id,
            respiratory_rate  = rr,
            oxygen_saturation = spo2,
            o2_scale          = o2s,
            systolic_bp       = sbp,
            heart_rate        = hr,
            temperature       = temp,
            consciousness     = cons,
            on_oxygen         = 1 if on_o2 else 0,
            rule_score        = result["rule_score"],
            ml_prediction     = result["ml_prediction"],
            ml_probability    = result["ml_probability"],
            final_risk        = result["final_risk"],
            explanation       = result["explanation"],
            recommendation    = result["recommendation"],
            status            = "pending",
        )
        db.add(new_a)
        db.commit()
        assessment_id = new_a.id

    log_action(
        user["id"], "SUBMIT_ASSESSMENT",
        f"Assessment #{assessment_id} — "
        f"NEWS2: {result['rule_score']} | "
        f"AI: {result['ml_prediction']} ({result['ml_probability']:.1%}) | "
        f"Final: {result['final_risk']}",
    )

    # ── Results display ───────────────────────────────────────────────────────
    st.divider()
    st.markdown("## ✅ Assessment Complete")

    show_risk_alert(result["final_risk"], result["recommendation"])

    # Summary metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("NEWS2 Score",       result["rule_score"])
    m2.metric("AI Prediction",     result["ml_prediction"])
    m3.metric("AI Confidence",     f"{result['ml_probability']:.1%}")
    m4.metric("Final Risk",        result["final_risk"])

    # Charts row
    if result.get("ml_class_probs"):
        col_p, col_s = st.columns(2)
        with col_p:
            st.plotly_chart(
                ml_probability_bar(result["ml_class_probs"]),
                use_container_width=True,
            )
        with col_s:
            if result.get("shap_features"):
                st.plotly_chart(
                    shap_bar_chart(result["shap_features"]),
                    use_container_width=True,
                )

    with st.expander("📖 Full Clinical Explanation", expanded=True):
        st.markdown(result["explanation"])

    st.info(
        f"📤 Assessment **#{assessment_id}** has been saved to the database and "
        f"automatically forwarded to your doctor. "
        f"You will see their feedback in your dashboard once reviewed."
    )

    ca, cb = st.columns(2)
    with ca:
        if st.button("📊 Go to My Dashboard", use_container_width=True, type="primary"):
            st.switch_page("pages/4_Patient_Dashboard.py")
    with cb:
        if st.button("📋 Submit Another Assessment", use_container_width=True):
            st.rerun()

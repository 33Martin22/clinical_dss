"""pages/1_Landing.py — Professional landing page."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database import init_db
from auth     import seed_defaults, get_current_user
from utils    import global_css
from components.navbar import render_navbar

st.set_page_config(page_title="Home | AI Clinical DSS", page_icon="🏥", layout="wide")
init_db(); seed_defaults(); global_css(); render_navbar()

st.markdown("""
<style>
.hero {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 45%, #4338ca 100%);
    border-radius: 22px; padding: 4.5rem 3rem 4rem;
    color: white; text-align: center; margin-bottom: 2rem;
}
.hero h1 { font-size: 3rem; font-weight: 900; margin-bottom: 1rem; }
.hero p  { font-size: 1.15rem; opacity: .9; max-width: 700px;
            margin: 0 auto 2.5rem; line-height: 1.75; }
.step-card { background: white; border-radius: 14px; padding: 1.2rem .9rem;
             text-align: center; box-shadow: 0 2px 12px rgba(0,0,0,.06); }
.step-num  { width: 36px; height: 36px; border-radius: 50%;
             background: linear-gradient(135deg,#4f46e5,#7c3aed);
             color: white; font-weight: 800;
             display: flex; align-items: center; justify-content: center;
             margin: 0 auto .75rem; font-size: .95rem; }
.about-box { background: linear-gradient(135deg,#eef2ff,#f5f3ff);
             border-radius: 18px; padding: 2.5rem;
             border-left: 5px solid #4f46e5; }
</style>
""", unsafe_allow_html=True)

user = get_current_user()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🏥 AI-Powered Hybrid<br>Clinical Decision Support</h1>
    <p>
        Real-time health risk assessment combining evidence-based NEWS2 clinical
        scoring rules with a trained Keras deep neural network — delivering
        explainable, transparent risk predictions for patients and clinicians.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Stats row ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
for col, (v, l) in zip([c1, c2, c3, c4], [
    ("11",       "Model Input Features"),
    ("3-Class",  "Risk Engine Output"),
    ("Keras DNN","AI Backend"),
    ("PostgreSQL","Persistent Database"),
]):
    col.markdown(
        f'<div class="kpi-card" style="--accent:#4f46e5">'
        f'<div class="kpi-value" style="font-size:1.7rem">{v}</div>'
        f'<div class="kpi-label">{l}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── CTA buttons ───────────────────────────────────────────────────────────────
if user:
    st.info(f"👋 Welcome back, **{user['name']}**! Role: **{user['role'].title()}**")
    target = {
        "patient": "pages/4_Patient_Dashboard.py",
        "doctor":  "pages/5_Doctor_Dashboard.py",
        "admin":   "pages/6_Admin_Dashboard.py",
    }.get(user["role"], "pages/4_Patient_Dashboard.py")
    if st.button("Go to My Dashboard →", type="primary"):
        st.switch_page(target)
else:
    ca, cb, _ = st.columns([1, 1, 4])
    with ca:
        if st.button("🔑 Sign In", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Login.py")
    with cb:
        if st.button("📝 Register", use_container_width=True):
            st.switch_page("pages/3_Register.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── Features ──────────────────────────────────────────────────────────────────
st.markdown(
    "<h2 style='color:#1e1b4b'>✨ Platform Features</h2>"
    "<p style='color:#64748b;margin-bottom:1.5rem'>"
    "Everything needed for intelligent remote health monitoring</p>",
    unsafe_allow_html=True,
)

features = [
    ("🧠", "Keras Deep Neural Network",
     "Dense(64→32→16→3) MLP with Dropout regularisation and softmax output trained on clinical vitals data."),
    ("⚖️", "Hybrid Rule + AI Engine",
     "NEWS2 clinical rules combined with Keras DNN. When they disagree, the higher risk is adopted for patient safety."),
    ("🔍", "SHAP Explainability",
     "Every assessment shows SHAP feature importances — making AI decisions transparent and interpretable."),
    ("🩺", "Mandatory Doctor Review",
     "Every assessment is automatically queued for physician review. Patients cannot bypass this step."),
    ("📄", "Clinical PDF Reports",
     "ReportLab PDF exports with vitals, risk level, AI explanation, SHAP analysis, and doctor notes."),
    ("🔒", "Secure & Role-Based",
     "Bcrypt hashing, role-protected routes, PostgreSQL persistence, and full audit logging."),
]
cols = st.columns(3)
for i, (icon, title, desc) in enumerate(features):
    with cols[i % 3]:
        st.markdown(
            f'<div class="feat-card">'
            f'<div style="font-size:2.2rem;margin-bottom:.7rem">{icon}</div>'
            f'<div style="font-weight:700;color:#1e1b4b;margin-bottom:.5rem">{title}</div>'
            f'<div style="color:#64748b;font-size:.9rem;line-height:1.6">{desc}</div>'
            f'</div><br>',
            unsafe_allow_html=True,
        )

# ── Workflow steps ────────────────────────────────────────────────────────────
st.markdown("<h2 style='color:#1e1b4b'>🔄 How It Works</h2>", unsafe_allow_html=True)
steps = [
    ("1", "📝", "Register",      "Create account & health profile"),
    ("2", "🌡️", "Submit Vitals", "Enter vitals in the guided form"),
    ("3", "🤖", "AI Analysis",   "NEWS2 rules + Keras DNN"),
    ("4", "📋", "Auto-Queue",    "Sent to doctor — mandatory"),
    ("5", "💬", "Doctor Review", "Physician adds clinical notes"),
    ("6", "📥", "Download PDF",  "Export your clinical report"),
]
for col, (num, icon, title, desc) in zip(st.columns(6), steps):
    with col:
        st.markdown(
            f'<div class="step-card">'
            f'<div class="step-num">{num}</div>'
            f'<div style="font-size:1.5rem">{icon}</div>'
            f'<div style="font-weight:700;font-size:.82rem;color:#1e1b4b;margin:.4rem 0">{title}</div>'
            f'<div style="font-size:.74rem;color:#64748b">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── About ─────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div class="about-box">
    <h2 style="color:#1e1b4b;margin-top:0">🏥 About the System</h2>
    <p style="color:#374151;line-height:1.85">
    The system uses a <strong>two-stage hybrid pipeline</strong>:
    <strong>Stage 1</strong> applies NEWS2-style clinical rules (Royal College of Physicians, 2017)
    to each vital sign, generating a numerical score and human-readable abnormality flags.
    <strong>Stage 2</strong> runs a trained Keras DNN
    (11 inputs → Dense(64,ReLU) → Dropout(0.3) → Dense(32,ReLU) → Dropout(0.3) → Dense(16,ReLU) → Dense(3,Softmax)).
    When the two stages disagree, the <em>higher</em> risk level is adopted.
    SHAP GradientExplainer then identifies the top features driving the prediction.
    All assessments are mandatorily routed through physician review before any
    clinical action is communicated to the patient.
    </p>
</div>
""", unsafe_allow_html=True)

# ── Demo credentials ──────────────────────────────────────────────────────────
with st.expander("🔑 Demo Login Credentials"):
    st.markdown("""
| Role   | Email              | Password    |
|--------|--------------------|-------------|
| Admin  | admin@clinic.com   | Admin@1234  |
| Doctor | doctor@clinic.com  | Doctor@1234 |
| Patient | Register a new account | — |
    """)
    st.caption(
        "⚠️ These are demonstration credentials for academic evaluation only. "
        "Do not use real patient data with this system."
    )

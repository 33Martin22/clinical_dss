"""
utils.py
--------
Clinical validation, global CSS injection, and shared UI helper functions.
"""
import streamlit as st
from config import CLINICAL_LIMITS, CLINICAL_WARNINGS


# ── Clinical validation ───────────────────────────────────────────────────────

def validate_hard(data: dict) -> list[str]:
    """
    Hard validation — block physiologically impossible values.
    Returns a list of error strings (empty list = all values valid).
    """
    errors = []
    for field, (lo, hi) in CLINICAL_LIMITS.items():
        val = data.get(field)
        if val is not None and not (lo <= val <= hi):
            label = field.replace("_", " ").title()
            errors.append(
                f"{label} = {val} is outside the physiologically "
                f"possible range ({lo}–{hi})."
            )
    return errors


def validate_soft(data: dict) -> list[str]:
    """
    Soft validation — warn about dangerous-but-possible values.
    Returns a list of warning strings.
    """
    warnings = []
    for field, (lo, hi) in CLINICAL_WARNINGS.items():
        val = data.get(field)
        if val is not None and not (lo <= val <= hi):
            label = field.replace("_", " ").title()
            warnings.append(
                f"{label} ({val}) is outside the normal clinical "
                f"range ({lo}–{hi}). Please verify this reading."
            )
    return warnings


# ── Global CSS ────────────────────────────────────────────────────────────────

def global_css() -> None:
    """Inject shared CSS. Must be called once per page."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background: linear-gradient(135deg, #eef2ff 0%, #f0fdf4 50%, #fafafa 100%);
    }

    /* ── KPI cards ── */
    .kpi-card {
        background: white;
        border-radius: 14px;
        padding: 1.3rem 1rem;
        text-align: center;
        box-shadow: 0 2px 16px rgba(0,0,0,.07);
        border-top: 4px solid var(--accent, #4f46e5);
        margin-bottom: .75rem;
    }
    .kpi-value { font-size: 2.1rem; font-weight: 800; color: var(--accent, #4f46e5); }
    .kpi-label { font-size: .82rem; color: #64748b; margin-top: .25rem; }

    /* ── Risk badges ── */
    .risk-badge  { display: inline-block; padding: .35rem 1rem;
                   border-radius: 20px; font-weight: 700; font-size: .95rem; }
    .risk-high   { background: #fee2e2; color: #991b1b; }
    .risk-medium { background: #fef3c7; color: #92400e; }
    .risk-low    { background: #dcfce7; color: #166534; }

    /* ── Feature cards ── */
    .feat-card {
        background: white;
        border-radius: 16px;
        padding: 1.6rem;
        box-shadow: 0 4px 24px rgba(0,0,0,.06);
        border-top: 4px solid #4f46e5;
        height: 100%;
        transition: transform .2s, box-shadow .2s;
    }
    .feat-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 36px rgba(0,0,0,.12);
    }

    /* ── Sidebar brand ── */
    .sidebar-brand {
        font-size: 1.1rem; font-weight: 800;
        color: #1e1b4b; text-align: center;
        padding: .6rem .5rem; letter-spacing: -.3px;
    }

    /* ── Buttons ── */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        transition: transform .15s, box-shadow .15s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(0,0,0,.15);
    }

    /* ── Expanders ── */
    div[data-testid="stExpander"] {
        background: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }

    /* ── Dividers ── */
    hr { border-color: #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)


# ── HTML snippet helpers ──────────────────────────────────────────────────────

def kpi(value, label: str, accent: str = "#4f46e5") -> str:
    """Return HTML for a KPI metric card."""
    return (
        f'<div class="kpi-card" style="--accent:{accent}">'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'</div>'
    )


def risk_badge(risk: str) -> str:
    """Return an inline HTML risk level badge."""
    cls  = {"High": "risk-high", "Medium": "risk-medium",
            "Low": "risk-low"}.get(risk, "")
    icon = {"High": "🚨", "Medium": "⚠️", "Low": "✅"}.get(risk, "")
    return f'<span class="risk-badge {cls}">{icon} {risk}</span>'

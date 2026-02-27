"""components/alerts.py — Risk alert banners and clinical warning helpers."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

_CFG = {
    "Low":    ("success", "✅ LOW RISK"),
    "Medium": ("warning", "⚠️ MEDIUM RISK — Clinical Attention Advised"),
    "High":   ("error",   "🚨 HIGH RISK — URGENT ATTENTION REQUIRED"),
}


def show_risk_alert(risk_level: str, message: str = "") -> None:
    """Display a colour-coded risk alert banner."""
    kind, label = _CFG.get(risk_level, ("info", f"RISK: {risk_level}"))
    text = f"**{label}**" + (f"\n\n{message}" if message else "")
    getattr(st, kind)(text)


def show_clinical_warnings(warnings: list) -> None:
    """Display soft clinical warnings inside a collapsible expander."""
    if warnings:
        with st.expander(
            f"⚠️ {len(warnings)} Clinical Warning(s) — values outside normal range",
            expanded=True,
        ):
            for w in warnings:
                st.warning(w)

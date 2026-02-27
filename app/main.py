"""
main.py
-------
Application entry point.

Local:            streamlit run app/main.py
Streamlit Cloud:  Main file path = app/main.py
"""
import sys
import os

# Add app/ to the Python path so every page can import modules directly.
# This is set once here so no page ever needs sys.path.insert().
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from database import init_db
from auth     import seed_defaults
from utils    import global_css
from components.navbar import render_navbar

# Warm-up the Keras model at startup so the first assessment
# does not appear to hang (TF takes 20-40 s on cold start).
from risk_engine.ml_model import load_keras_model, load_scaler

st.set_page_config(
    page_title = "AI Clinical Decision Support",
    page_icon  = "🏥",
    layout     = "wide",
    initial_sidebar_state = "expanded",
)


@st.cache_resource(show_spinner=False)
def _startup() -> bool:
    """
    Run once per server process:
      1. Create / verify all PostgreSQL tables.
      2. Seed default admin + doctor accounts.
      3. Pre-load the Keras model and scaler into memory.

    Returns True so st.cache_resource can store the result.
    """
    init_db()
    seed_defaults()
    return True


# ── Startup sequence ──────────────────────────────────────────────────────────
_startup()

# Pre-load model (shows spinner on first cold start)
load_keras_model()
load_scaler()

global_css()
render_navbar()

# Redirect to landing page
st.switch_page("pages/1_Landing.py")

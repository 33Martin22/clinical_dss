"""
main.py
-------
Application entry point.

Local:            streamlit run app/main.py
Streamlit Cloud:  Main file path = app/main.py
"""
# ── Path setup — must be FIRST, before any local imports ──────────────────────
# This ensures app/ is on sys.path whether running locally or on Streamlit Cloud.
import sys
import os

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

# ── Standard imports ───────────────────────────────────────────────────────────
import streamlit as st

from database              import init_db
from auth                  import seed_defaults
from utils                 import global_css
from components.navbar     import render_navbar
from risk_engine.ml_model  import load_keras_model, load_scaler

st.set_page_config(
    page_title            = "AI Clinical Decision Support",
    page_icon             = "🏥",
    layout                = "wide",
    initial_sidebar_state = "expanded",
)


@st.cache_resource(show_spinner=False)
def _startup() -> bool:
    """
    Run once per server process:
      1. Create / verify all PostgreSQL tables.
      2. Seed default admin + doctor accounts.
    Returns True so st.cache_resource stores the result.
    """
    init_db()
    seed_defaults()
    return True


# ── Startup ───────────────────────────────────────────────────────────────────
_startup()

# Pre-warm Keras model (shows spinner; avoids freeze on first assessment)
load_keras_model()
load_scaler()

global_css()
render_navbar()

st.switch_page("pages/1_Landing.py")

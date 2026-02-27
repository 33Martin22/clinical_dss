"""
config.py
---------
Single source of truth for all application settings.
Reads secrets from .streamlit/secrets.toml (local) or
Streamlit Cloud secrets panel (production).
No hardcoded credentials anywhere.
"""
import os
import streamlit as st


def _secret(key: str, default: str = "") -> str:
    """Read from st.secrets with a safe fallback."""
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.environ.get(key, default)


# ── Database ────────────────────────────────────────────────────────────────
DATABASE_URL = _secret("DATABASE_URL")

# ── Security ────────────────────────────────────────────────────────────────
SECRET_KEY    = _secret("SECRET_KEY", "dev-only-insecure-key-change-in-production")
BCRYPT_ROUNDS = 12

# ── App metadata ────────────────────────────────────────────────────────────
APP_NAME    = "AI-Powered Hybrid Clinical Decision Support System"
APP_VERSION = "3.0.0"
APP_ICON    = "🏥"

# ── Risk levels (3-class model output) ─────────────────────────────────────
RISK_LEVELS = {
    "Low":    {"color": "#16a34a", "bg": "#dcfce7", "icon": "✅"},
    "Medium": {"color": "#d97706", "bg": "#fef3c7", "icon": "⚠️"},
    "High":   {"color": "#dc2626", "bg": "#fee2e2", "icon": "🚨"},
}

# ── Keras model class mapping ────────────────────────────────────────────────
# Training used LabelEncoder (alphabetical) → High=0, Low=1, Medium=2
ML_CLASS_LABELS = {0: "High", 1: "Low", 2: "Medium"}

# ── Feature engineering — must mirror training exactly ──────────────────────
SCALER_FEATURES = [
    "Respiratory_Rate", "Oxygen_Saturation", "O2_Scale",
    "Systolic_BP", "Heart_Rate", "Temperature",
]
# OHE consciousness drop_first=True → base = 'A'
CONSCIOUSNESS_OHE_COLS = [
    "consciousness_C", "consciousness_P",
    "consciousness_U", "consciousness_V",
]
MODEL_FEATURE_COUNT = 11  # 6 scaled + 4 OHE + 1 On_Oxygen

# ── Model file paths ────────────────────────────────────────────────────────
_MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
MODEL_PATH  = os.path.join(_MODELS_DIR, "risk_model.h5")
SCALER_PATH = os.path.join(_MODELS_DIR, "scaler.pkl")

# ── Clinical hard-limit validation (block impossible values) ────────────────
CLINICAL_LIMITS = {
    "respiratory_rate":  (1,    70),
    "oxygen_saturation": (50,  100),
    "systolic_bp":       (50,  300),
    "heart_rate":        (20,  250),
    "temperature":       (30.0, 44.0),
}

# ── Clinical soft-warning thresholds (warn but allow) ───────────────────────
CLINICAL_WARNINGS = {
    "respiratory_rate":  (8,   30),
    "oxygen_saturation": (85, 100),
    "systolic_bp":       (80, 220),
    "heart_rate":        (40, 180),
    "temperature":       (35.0, 40.5),
}

# ── Session state keys ───────────────────────────────────────────────────────
S_UID   = "user_id"
S_ROLE  = "user_role"
S_NAME  = "user_name"
S_EMAIL = "user_email"

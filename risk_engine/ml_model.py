"""
risk_engine/ml_model.py
-----------------------
Keras model loading, feature engineering, prediction, and SHAP explainability.

Model details (verified from H5 metadata):
  Input  : 11 features
           [RR, SpO2, O2Scale, SBP, HR, Temp  ← MinMaxScaled
            consciousness_C, _P, _U, _V       ← OHE drop_first (base=A)
            On_Oxygen]                         ← binary
  Arch   : Dense(64,relu) → Dropout(0.3) → Dense(32,relu) →
           Dropout(0.3) → Dense(16,relu) → Dense(3,softmax)
  Output : {0: High, 1: Low, 2: Medium}  (alphabetical LabelEncoder)
  Scaler : MinMaxScaler on 6 numeric vitals
"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import os
import pickle
import logging

import numpy as np
import streamlit as st

from config import MODEL_PATH, SCALER_PATH, ML_CLASS_LABELS, MODEL_FEATURE_COUNT

log = logging.getLogger(__name__)

# Fallback bounds from fitted scaler (used if scaler.pkl cannot be loaded)
_DATA_MIN = np.array([12.,  74.,  1.,  50.,  64., 35.6])
_DATA_MAX = np.array([40., 100.,  2., 144., 163., 41.8])

FEATURE_NAMES = [
    "Respiratory Rate", "Oxygen Saturation", "O2 Scale",
    "Systolic BP",      "Heart Rate",        "Temperature",
    "Consciousness (C)", "Consciousness (P)",
    "Consciousness (U)", "Consciousness (V)",
    "On Oxygen",
]


# ── Model + Scaler loading (cached per server process) ──────────────────────

@st.cache_resource(show_spinner="🧠 Loading AI model — first load only, please wait...")
def load_keras_model():
    """
    Load the Keras model once per server process.
    st.cache_resource shares the loaded model across all users and sessions,
    so the 20–40 second TensorFlow initialisation only happens once.
    Returns the model or None if TensorFlow is not available.
    """
    try:
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
        import tensorflow as tf
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        log.info("Keras model loaded and cached.")
        return model
    except ImportError:
        log.warning("TensorFlow not installed — ML predictions disabled.")
        return None
    except Exception as e:
        log.error(f"Model load failed: {e}")
        return None


@st.cache_resource(show_spinner=False)
def load_scaler():
    """Load and cache the MinMaxScaler."""
    try:
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
        log.info("MinMaxScaler loaded and cached.")
        return scaler
    except Exception as e:
        log.error(f"Scaler load failed: {e}")
        return None


# ── Feature engineering ──────────────────────────────────────────────────────

def build_feature_vector(vitals: dict, scaler) -> np.ndarray:
    """
    Convert raw vitals to the 11-dim float32 feature vector the model expects.

    Layout:
      [0]  Respiratory_Rate   (MinMaxScaled)
      [1]  Oxygen_Saturation  (MinMaxScaled)
      [2]  O2_Scale           (MinMaxScaled)
      [3]  Systolic_BP        (MinMaxScaled)
      [4]  Heart_Rate         (MinMaxScaled)
      [5]  Temperature        (MinMaxScaled)
      [6]  consciousness_C    (OHE, base=A)
      [7]  consciousness_P
      [8]  consciousness_U
      [9]  consciousness_V
      [10] On_Oxygen          (binary 0/1)
    """
    cons = str(vitals.get("consciousness", "A")).upper()

    numeric = np.array([[
        vitals["respiratory_rate"],
        vitals["oxygen_saturation"],
        vitals["o2_scale"],
        vitals["systolic_bp"],
        vitals["heart_rate"],
        vitals["temperature"],
    ]], dtype=float)

    # Scale numeric vitals
    if scaler is not None:
        try:
            scaled = scaler.transform(numeric)[0]
        except Exception:
            scaled = np.clip(
                (numeric[0] - _DATA_MIN) / (_DATA_MAX - _DATA_MIN + 1e-8), 0, 1
            )
    else:
        scaled = np.clip(
            (numeric[0] - _DATA_MIN) / (_DATA_MAX - _DATA_MIN + 1e-8), 0, 1
        )

    # One-hot encode consciousness (drop_first → base = A)
    ohe = [
        1 if cons == "C" else 0,
        1 if cons == "P" else 0,
        1 if cons == "U" else 0,
        1 if cons == "V" else 0,
    ]

    vec = np.concatenate(
        [scaled, ohe, [int(vitals.get("on_oxygen", 0))]]
    ).astype(np.float32)

    assert vec.shape == (MODEL_FEATURE_COUNT,), (
        f"Feature vector shape mismatch: expected ({MODEL_FEATURE_COUNT},), "
        f"got {vec.shape}"
    )

    return vec.reshape(1, -1)


# ── Prediction ───────────────────────────────────────────────────────────────

def predict(vitals: dict, model, scaler) -> tuple:
    """
    Run the Keras model.
    Returns (risk_label: str, confidence: float, probs: list[float])
    or      (None, None, None) on failure.
    """
    try:
        x     = build_feature_vector(vitals, scaler)
        probs = model.predict(x, verbose=0)[0]   # shape (3,)
        idx   = int(np.argmax(probs))
        label = ML_CLASS_LABELS.get(idx, "Low")
        return label, float(probs[idx]), probs.tolist()
    except Exception as e:
        log.error(f"Prediction failed: {e}")
        return None, None, None


# ── SHAP Explainability ───────────────────────────────────────────────────────

def shap_explanation(vitals: dict, model, scaler, top_n: int = 4) -> list[tuple]:
    """
    Compute SHAP feature importances using GradientExplainer.
    Returns [(feature_name, importance_value), ...] for the top_n features,
    or an empty list if SHAP is unavailable.
    """
    try:
        import shap

        x          = build_feature_vector(vitals, scaler)
        background = np.zeros((1, MODEL_FEATURE_COUNT), dtype=np.float32)
        explainer  = shap.GradientExplainer(model, background)
        shap_vals  = explainer.shap_values(x)

        if isinstance(shap_vals, list):
            importance = np.abs(np.array(shap_vals)).mean(axis=0)[0]
        else:
            importance = np.abs(shap_vals[0])

        top_idx = np.argsort(importance)[::-1][:top_n]
        return [(FEATURE_NAMES[i], float(importance[i])) for i in top_idx]

    except Exception as e:
        log.warning(f"SHAP explanation unavailable: {e}")
        return []

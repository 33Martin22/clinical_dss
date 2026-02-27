"""
risk_engine/hybrid.py
---------------------
Combines the NEWS2 rule engine and the Keras ML model into a single
hybrid decision.  When the two sources disagree, the higher risk is
adopted — the conservative clinical choice.
"""
from .rules    import compute_rule_score, score_to_risk
from .ml_model import load_keras_model, load_scaler, predict, shap_explanation

# Risk ordinal for comparison
_RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2}

# Clinical recommendations per risk level
_RECOMMENDATIONS = {
    "Low": (
        "✅ Vital signs are within an acceptable range. "
        "Continue routine self-monitoring. "
        "Reassess if new symptoms develop or your condition changes."
    ),
    "Medium": (
        "⚠️ Some vital signs require clinical attention. "
        "Increase monitoring frequency and contact your care team. "
        "A review within 24 hours is advised."
    ),
    "High": (
        "🚨 Urgent clinical attention is required. "
        "Contact your doctor or emergency services immediately. "
        "Do not delay — critical vital sign abnormalities have been detected."
    ),
}


def _hybrid_decision(rule_risk: str, ml_risk: str | None) -> str:
    """Return the higher of the two risk levels (conservative choice)."""
    if ml_risk is None:
        return rule_risk
    return (
        rule_risk
        if _RISK_ORDER[rule_risk] >= _RISK_ORDER.get(ml_risk, 0)
        else ml_risk
    )


def run_full_assessment(vitals: dict) -> dict:
    """
    Execute the complete hybrid risk assessment pipeline.

    Pipeline:
      1. NEWS2 rule scoring
      2. Keras DNN prediction
      3. Hybrid decision (higher risk wins)
      4. SHAP feature importance
      5. Structured explanation text
      6. Clinical recommendation

    Parameters
    ----------
    vitals : dict
        Keys: respiratory_rate, oxygen_saturation, o2_scale,
              systolic_bp, heart_rate, temperature,
              consciousness (A/C/V/P/U), on_oxygen (0/1)

    Returns
    -------
    dict with keys:
        rule_score, ml_prediction, ml_probability, ml_class_probs,
        final_risk, explanation, recommendation, shap_features
    """
    # ── Step 1: NEWS2 rule scoring ───────────────────────────────────────────
    rule_score, abnormals = compute_rule_score(vitals)
    rule_risk             = score_to_risk(rule_score)

    # ── Step 2: Keras model ──────────────────────────────────────────────────
    model  = load_keras_model()
    scaler = load_scaler()

    if model is not None:
        ml_risk, ml_conf, ml_probs = predict(vitals, model, scaler)
    else:
        ml_risk, ml_conf, ml_probs = None, None, None

    # ── Step 3: Hybrid decision ──────────────────────────────────────────────
    final_risk = _hybrid_decision(rule_risk, ml_risk)

    # ── Step 4: SHAP explanation ─────────────────────────────────────────────
    shap_feats = []
    if model is not None:
        shap_feats = shap_explanation(vitals, model, scaler, top_n=4)

    # ── Step 5: Build explanation text ──────────────────────────────────────
    parts = []

    # Rule section
    if abnormals:
        parts.append(
            "**🔬 Rule-Based Analysis (NEWS2) — Abnormal Vitals Detected:**\n" +
            "\n".join(f"- {a}" for a in abnormals)
        )
    else:
        parts.append(
            "**🔬 Rule-Based Analysis (NEWS2):** "
            "All vital signs are within normal clinical ranges."
        )

    parts.append(f"\n**NEWS2 Score: {rule_score}** → Rule Risk: **{rule_risk}**")

    # ML section
    if ml_risk is not None and ml_probs is not None:
        prob_str = (
            f"High: {ml_probs[0]:.1%} | "
            f"Low: {ml_probs[1]:.1%} | "
            f"Medium: {ml_probs[2]:.1%}"
        )
        parts.append(
            f"\n**🤖 AI Model (Keras DNN):** Predicted **{ml_risk}** "
            f"with {ml_conf:.1%} confidence.\n"
            f"Class probabilities — {prob_str}"
        )

        if rule_risk != ml_risk:
            parts.append(
                f"\n**⚖️ Hybrid Resolution:** "
                f"Rules predicted **{rule_risk}** · AI predicted **{ml_risk}** · "
                f"Final decision: **{final_risk}** "
                f"(higher risk adopted for patient safety)."
            )

        if shap_feats:
            parts.append(
                "\n**📊 Top SHAP Feature Importances "
                "(features most influential on this prediction):**\n" +
                "\n".join(
                    f"- {name}: {val:.4f}" for name, val in shap_feats
                )
            )
    else:
        parts.append(
            "\n**🤖 AI Model:** Unavailable — "
            "assessment based on rule engine only. "
            "Ensure TensorFlow is installed and risk_model.h5 is present."
        )

    return {
        "rule_score":     rule_score,
        "ml_prediction":  ml_risk  or "N/A",
        "ml_probability": ml_conf  or 0.0,
        "ml_class_probs": ml_probs or [],
        "final_risk":     final_risk,
        "explanation":    "\n".join(parts),
        "recommendation": _RECOMMENDATIONS[final_risk],
        "shap_features":  shap_feats,
    }

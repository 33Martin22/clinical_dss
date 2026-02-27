"""
risk_engine/rules.py
--------------------
Pure NEWS2-style clinical rule scoring.

Zero framework dependencies — no Streamlit, no TensorFlow, no SQLAlchemy.
This means the clinical logic can be read, tested, and verified
completely independently of the application stack.

NEWS2 reference:
  Royal College of Physicians. National Early Warning Score (NEWS) 2.
  London: RCP, 2017.
"""


def compute_rule_score(vitals: dict) -> tuple[int, list[str]]:
    """
    Apply NEWS2-style scoring to a vitals dictionary.

    Parameters
    ----------
    vitals : dict
        Keys: respiratory_rate, oxygen_saturation, o2_scale,
              systolic_bp, heart_rate, temperature,
              consciousness, on_oxygen

    Returns
    -------
    score     : int           — aggregate NEWS2 score
    abnormals : list[str]     — human-readable flag for each abnormal vital
    """
    score:     int       = 0
    abnormals: list[str] = []

    rr    = vitals.get("respiratory_rate",  18)
    spo2  = vitals.get("oxygen_saturation", 98)
    sbp   = vitals.get("systolic_bp",      120)
    hr    = vitals.get("heart_rate",        80)
    temp  = vitals.get("temperature",       37.0)
    cons  = str(vitals.get("consciousness", "A")).upper()
    on_o2 = int(vitals.get("on_oxygen",     0))
    o2_sc = int(vitals.get("o2_scale",      1))

    # ── Respiratory Rate ────────────────────────────────────────────────────
    if rr <= 8:
        score += 3
        abnormals.append(f"Respiratory rate critically low ({rr} breaths/min)")
    elif rr <= 11:
        score += 1
        abnormals.append(f"Respiratory rate low ({rr} breaths/min)")
    elif rr <= 20:
        pass   # normal range
    elif rr <= 24:
        score += 2
        abnormals.append(f"Respiratory rate elevated ({rr} breaths/min)")
    else:
        score += 3
        abnormals.append(f"Respiratory rate critically high ({rr} breaths/min)")

    # ── SpO2 (Scale-aware — NEWS2 Scale 1 vs Scale 2) ──────────────────────
    if o2_sc == 2:
        # Scale 2: COPD / hypercapnic respiratory failure target 88–92 %
        if spo2 <= 83:
            score += 3
            abnormals.append(f"SpO₂ critically low for COPD scale ({spo2}%)")
        elif spo2 <= 85:
            score += 2
            abnormals.append(f"SpO₂ low for COPD scale ({spo2}%)")
        elif spo2 <= 87:
            score += 1
            abnormals.append(f"SpO₂ borderline for COPD scale ({spo2}%)")
        elif spo2 <= 92:
            pass   # target range for COPD
        else:
            score += 2
            abnormals.append(
                f"SpO₂ above COPD target — hypercapnia risk ({spo2}%)"
            )
    else:
        # Scale 1: standard patients target ≥ 96 %
        if spo2 <= 91:
            score += 3
            abnormals.append(f"Oxygen saturation critically low ({spo2}%)")
        elif spo2 <= 93:
            score += 2
            abnormals.append(f"Oxygen saturation low ({spo2}%)")
        elif spo2 <= 95:
            score += 1
            abnormals.append(f"Oxygen saturation borderline ({spo2}%)")

    # ── Supplemental Oxygen ─────────────────────────────────────────────────
    if on_o2 == 1:
        score += 2
        abnormals.append("Patient is on supplemental oxygen")

    # ── Systolic Blood Pressure ─────────────────────────────────────────────
    if sbp <= 90:
        score += 3
        abnormals.append(f"Systolic BP critically low ({sbp} mmHg)")
    elif sbp <= 100:
        score += 2
        abnormals.append(f"Systolic BP low ({sbp} mmHg)")
    elif sbp <= 110:
        score += 1
        abnormals.append(f"Systolic BP borderline low ({sbp} mmHg)")
    elif sbp <= 219:
        pass   # normal range
    else:
        score += 3
        abnormals.append(f"Systolic BP critically high ({sbp} mmHg)")

    # ── Heart Rate ──────────────────────────────────────────────────────────
    if hr <= 40:
        score += 3
        abnormals.append(f"Heart rate critically low ({hr} bpm)")
    elif hr <= 50:
        score += 1
        abnormals.append(f"Heart rate low ({hr} bpm)")
    elif hr <= 90:
        pass   # normal range
    elif hr <= 110:
        score += 1
        abnormals.append(f"Heart rate elevated ({hr} bpm)")
    elif hr <= 130:
        score += 2
        abnormals.append(f"Heart rate high ({hr} bpm)")
    else:
        score += 3
        abnormals.append(f"Heart rate critically high ({hr} bpm)")

    # ── Temperature ─────────────────────────────────────────────────────────
    if temp <= 35.0:
        score += 3
        abnormals.append(f"Temperature critically low — hypothermia risk ({temp} °C)")
    elif temp <= 36.0:
        score += 1
        abnormals.append(f"Temperature low ({temp} °C)")
    elif temp <= 38.0:
        pass   # normal range
    elif temp <= 39.0:
        score += 1
        abnormals.append(f"Temperature elevated — fever ({temp} °C)")
    else:
        score += 2
        abnormals.append(f"Temperature high — high fever ({temp} °C)")

    # ── Consciousness (ACVPU scale) ─────────────────────────────────────────
    if cons == "A":
        pass   # Alert — normal
    elif cons == "C":
        score += 3
        abnormals.append("Consciousness: Confused (new confusion is a medical emergency)")
    elif cons == "V":
        score += 3
        abnormals.append("Consciousness: responds only to Voice")
    elif cons == "P":
        score += 3
        abnormals.append("Consciousness: responds only to Pain")
    elif cons == "U":
        score += 3
        abnormals.append("Consciousness: Unresponsive")

    return score, abnormals


def score_to_risk(score: int) -> str:
    """
    Map aggregate NEWS2 score to clinical risk level.

    NEWS2 thresholds (RCP 2017):
      0–4   → Low    (routine monitoring)
      5–6   → Medium (urgent response)
      ≥ 7   → High   (emergency response)
    """
    if score <= 4:
        return "Low"
    elif score <= 6:
        return "Medium"
    else:
        return "High"

"""
components/pdf_generator.py
---------------------------
Generates a professional clinical assessment PDF report using ReportLab.
"""
from io import BytesIO
from datetime import datetime

from reportlab.lib              import colors
from reportlab.lib.enums        import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes    import A4
from reportlab.lib.styles       import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units        import cm
from reportlab.platypus         import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable,
)

_RISK_COLOR = {
    "Low":    colors.HexColor("#16a34a"),
    "Medium": colors.HexColor("#d97706"),
    "High":   colors.HexColor("#dc2626"),
}
_RISK_BG = {
    "Low":    colors.HexColor("#dcfce7"),
    "Medium": colors.HexColor("#fef3c7"),
    "High":   colors.HexColor("#fee2e2"),
}


def generate_assessment_pdf(
    patient_info:  dict,
    assessment:    dict,
    doctor_notes:  list = None,
) -> bytes:
    """
    Build and return a clinical assessment PDF as bytes.

    Parameters
    ----------
    patient_info  : {name, email, age, gender, conditions}
    assessment    : {id, final_risk, respiratory_rate, oxygen_saturation,
                     o2_scale, systolic_bp, heart_rate, temperature,
                     consciousness, on_oxygen, rule_score, ml_prediction,
                     ml_probability, explanation, recommendation}
    doctor_notes  : [{doctor_name, created_at, note}, ...]
    """
    buf  = BytesIO()
    doc  = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    story  = []

    # ── Header ───────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=20, textColor=colors.HexColor("#1e1b4b"),
        spaceAfter=4, alignment=TA_CENTER,
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=10, textColor=colors.grey,
        alignment=TA_CENTER, spaceAfter=10,
    )
    story.append(Paragraph("🏥 Clinical Assessment Report", title_style))
    story.append(Paragraph(
        "AI-Powered Hybrid Clinical Decision Support System — v3.0.0", sub_style
    ))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", sub_style
    ))
    story.append(HRFlowable(
        width="100%", thickness=2, color=colors.HexColor("#1e1b4b"),
    ))
    story.append(Spacer(1, 0.4*cm))

    # ── Risk badge ────────────────────────────────────────────────────────────
    risk = assessment.get("final_risk", "Unknown")
    story.append(Paragraph(
        f"Overall Risk Level: {risk.upper()}",
        ParagraphStyle(
            "Risk", fontSize=18, alignment=TA_CENTER,
            textColor=_RISK_COLOR.get(risk, colors.grey),
            fontName="Helvetica-Bold", spaceAfter=6,
        ),
    ))
    story.append(Spacer(1, 0.4*cm))

    # ── Section style ─────────────────────────────────────────────────────────
    sec = ParagraphStyle(
        "Sec", parent=styles["Heading2"],
        textColor=colors.HexColor("#1e1b4b"), fontSize=13, spaceAfter=6,
    )

    # ── Patient information ───────────────────────────────────────────────────
    story.append(Paragraph("Patient Information", sec))
    pt_data = [
        ["Name",        patient_info.get("name",   "N/A"),
         "Age",         str(patient_info.get("age", "N/A"))],
        ["Email",       patient_info.get("email",  "N/A"),
         "Gender",      patient_info.get("gender", "N/A")],
        ["Conditions",  patient_info.get("conditions", "None recorded"),
         "Assessment",  f"#{assessment.get('id', 'N/A')}"],
    ]
    _table(story, pt_data, col_widths=[3.5*cm, 6.5*cm, 2.5*cm, 4*cm])
    story.append(Spacer(1, 0.4*cm))

    # ── AI engine summary ─────────────────────────────────────────────────────
    story.append(Paragraph("Risk Engine Summary", sec))
    ml_prob = assessment.get("ml_probability", 0.0) or 0.0
    eng_data = [
        ["NEWS2 Score", str(assessment.get("rule_score", "N/A")),
         "Rule Risk",   assessment.get("rule_risk", "N/A")],
        ["AI Prediction", assessment.get("ml_prediction", "N/A"),
         "AI Confidence", f"{ml_prob:.1%}"],
        ["Final Risk", risk, "Method", "Hybrid (higher risk adopted)"],
    ]
    _table(story, eng_data, col_widths=[3.5*cm, 4*cm, 3.5*cm, 5.5*cm])
    story.append(Spacer(1, 0.4*cm))

    # ── Vital signs ───────────────────────────────────────────────────────────
    story.append(Paragraph("Vital Signs Recorded", sec))
    v_data = [
        ["Parameter", "Value", "Parameter", "Value"],
        ["Respiratory Rate",
         f"{assessment.get('respiratory_rate', 'N/A')} breaths/min",
         "Heart Rate",
         f"{assessment.get('heart_rate', 'N/A')} bpm"],
        ["Oxygen Saturation",
         f"{assessment.get('oxygen_saturation', 'N/A')}%",
         "Temperature",
         f"{assessment.get('temperature', 'N/A')} °C"],
        ["Systolic BP",
         f"{assessment.get('systolic_bp', 'N/A')} mmHg",
         "On Oxygen",
         "Yes" if assessment.get("on_oxygen") else "No"],
        ["Consciousness",
         assessment.get("consciousness", "N/A"),
         "O2 Scale",
         f"Scale {assessment.get('o2_scale', 'N/A')}"],
    ]
    vt = Table(v_data, colWidths=[4*cm, 5.5*cm, 4*cm, 3*cm])
    vt.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f5f3ff")]),
        ("GRID",  (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(vt)
    story.append(Spacer(1, 0.4*cm))

    # ── Explanation ───────────────────────────────────────────────────────────
    story.append(Paragraph("Clinical Analysis & Explanation", sec))
    exp_text = (assessment.get("explanation", "No explanation.") or "").replace("\n", "<br/>")
    story.append(Paragraph(
        exp_text,
        ParagraphStyle("Exp", parent=styles["Normal"], fontSize=9, spaceAfter=4),
    ))
    story.append(Spacer(1, 0.3*cm))

    # ── Recommendation ────────────────────────────────────────────────────────
    story.append(Paragraph("Clinical Recommendation", sec))
    rec_t = Table([[assessment.get("recommendation", "No recommendation.")]])
    rec_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _RISK_BG.get(risk, colors.white)),
        ("PADDING",    (0, 0), (-1, -1), 10),
        ("FONTSIZE",   (0, 0), (-1, -1), 10),
    ]))
    story.append(rec_t)
    story.append(Spacer(1, 0.4*cm))

    # ── Doctor notes ──────────────────────────────────────────────────────────
    if doctor_notes:
        story.append(Paragraph("Physician Review Notes", sec))
        note_style = ParagraphStyle(
            "Note", parent=styles["Normal"], fontSize=9, spaceAfter=4,
        )
        for n in doctor_notes:
            story.append(Paragraph(
                f"<b>Dr. {n.get('doctor_name', 'Unknown')}</b> "
                f"— {n.get('created_at', '')}<br/>{n.get('note', '')}",
                note_style,
            ))
            story.append(Spacer(1, 0.2*cm))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Paragraph(
        "⚠️ This report is generated by an AI-assisted clinical decision "
        "support system. All findings must be confirmed by a licensed "
        "medical professional before any clinical action is taken.",
        ParagraphStyle(
            "Footer", parent=styles["Normal"],
            fontSize=8, textColor=colors.grey, alignment=TA_CENTER,
        ),
    ))

    doc.build(story)
    return buf.getvalue()


def _table(story, data, col_widths):
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [colors.HexColor("#eef2ff"), colors.HexColor("#f5f3ff")]),
        ("GRID",    (0, 0), (-1, -1), 0.5, colors.white),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(t)

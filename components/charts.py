"""components/charts.py — Reusable Plotly chart components."""
import plotly.graph_objects as go
import pandas as pd

_C = {"Low": "#16a34a", "Medium": "#d97706", "High": "#dc2626"}
_N = {"Low": 1, "Medium": 2, "High": 3}


# ── Risk Trend ────────────────────────────────────────────────────────────────

def risk_trend_chart(assessments: list) -> go.Figure:
    """Line + scatter chart of risk level over time."""
    rows = [
        {"Date": a.created_at, "Risk": a.final_risk, "Num": _N.get(a.final_risk, 0)}
        for a in assessments if a.created_at
    ]
    if not rows:
        return _empty("No timestamped assessments found")

    df  = pd.DataFrame(rows)
    fig = go.Figure(go.Scatter(
        x=df["Date"], y=df["Num"],
        mode="lines+markers",
        marker=dict(
            color=[_C.get(r, "#999") for r in df["Risk"]],
            size=12,
            line=dict(color="white", width=2),
        ),
        line=dict(color="#4f46e5", width=2, dash="dot"),
        text=df["Risk"],
        hovertemplate="<b>%{text}</b><br>%{x|%b %d, %Y %H:%M}<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(
            tickvals=[1, 2, 3], ticktext=["Low", "Medium", "High"],
            range=[0, 4], gridcolor="#f0f0f0",
        ),
        xaxis=dict(gridcolor="#f0f0f0"),
        height=300,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


# ── Risk Distribution Pie ─────────────────────────────────────────────────────

def risk_distribution_pie(counts: dict) -> go.Figure:
    """Donut pie of risk level distribution."""
    filtered = {k: v for k, v in counts.items() if v > 0}
    if not filtered:
        return _empty("No assessment data yet")

    labels = list(filtered.keys())
    values = list(filtered.values())
    fig    = go.Figure(go.Pie(
        labels=labels, values=values,
        marker_colors=[_C.get(l, "#999") for l in labels],
        hole=0.44,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b>: %{value} assessments<extra></extra>",
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return fig


# ── Vitals Radar ──────────────────────────────────────────────────────────────

def vitals_radar(vitals: dict) -> go.Figure:
    """Normalised radar chart of key vitals."""
    norms = {
        "Resp Rate":  min(vitals.get("respiratory_rate",  18) / 30, 1.0),
        "SpO₂":       vitals.get("oxygen_saturation",     98) / 100,
        "Sys BP":     min(vitals.get("systolic_bp",      120) / 200, 1.0),
        "Heart Rate": min(vitals.get("heart_rate",        80) / 150, 1.0),
        "Temp":       min((vitals.get("temperature",      37) - 35) / 7, 1.0),
    }
    cats = list(norms.keys()) + [list(norms.keys())[0]]   # close polygon
    vals = list(norms.values()) + [list(norms.values())[0]]

    fig = go.Figure(go.Scatterpolar(
        r=vals, theta=cats,
        fill="toself",
        fillcolor="rgba(79,70,229,.18)",
        line=dict(color="#4f46e5", width=2),
        marker=dict(size=6, color="#1e1b4b"),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=9)),
        ),
        height=300,
        margin=dict(l=30, r=30, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


# ── AI Class Probability Bar ──────────────────────────────────────────────────

def ml_probability_bar(probs: list) -> go.Figure:
    """
    Bar chart of Keras softmax output probabilities.
    probs = [p_High, p_Low, p_Medium]  (alphabetical model output order)
    """
    labels = ["High", "Low", "Medium"]
    fig    = go.Figure(go.Bar(
        x=labels,
        y=[p * 100 for p in probs],
        marker_color=[_C[l] for l in labels],
        text=[f"{p:.1%}" for p in probs],
        textposition="auto",
    ))
    fig.update_layout(
        title=dict(text="AI Model — Class Probabilities", font=dict(size=14)),
        yaxis=dict(title="Probability (%)", range=[0, 100]),
        height=280,
        margin=dict(l=20, r=20, t=45, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── SHAP Feature Importance Bar ───────────────────────────────────────────────

def shap_bar_chart(shap_feats: list) -> go.Figure:
    """
    Horizontal bar chart of SHAP feature importances.
    shap_feats = [(feature_name, importance_value), ...]
    """
    if not shap_feats:
        return _empty("SHAP explanation not available")

    names  = [f[0] for f in shap_feats][::-1]
    values = [f[1] for f in shap_feats][::-1]

    fig = go.Figure(go.Bar(
        x=values, y=names,
        orientation="h",
        marker_color="#4f46e5",
        text=[f"{v:.4f}" for v in values],
        textposition="auto",
    ))
    fig.update_layout(
        title=dict(text="SHAP Feature Importance (this assessment)", font=dict(size=14)),
        xaxis_title="Mean |SHAP value|",
        height=280,
        margin=dict(l=20, r=20, t=45, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── Empty placeholder ─────────────────────────────────────────────────────────

def _empty(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=13, color="#888"),
    )
    fig.update_layout(
        height=250,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

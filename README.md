# 🏥 AI-Powered Hybrid Clinical Decision Support System

**Version 3.0.0** · Academic Project · Streamlit + PostgreSQL + Keras

A production-quality clinical decision support system combining
evidence-based NEWS2 clinical rule scoring with a trained Keras deep
neural network, delivering explainable, role-based health risk assessments
with persistent PostgreSQL storage.

---

## 🏗️ System Architecture

```
Patient Vitals Input
        │
        ├─► NEWS2 Rule Engine (rules.py)
        │       Respiratory Rate, SpO2, BP,
        │       Heart Rate, Temp, Consciousness
        │       → Aggregate Score → Risk Label
        │
        ├─► Keras DNN (ml_model.py)
        │       MinMaxScaler (6 vitals)
        │       + OHE Consciousness (base=A)
        │       + Binary On_Oxygen
        │       → 11 features → Dense(64)→Dense(32)→Dense(16)→Dense(3,softmax)
        │       → Class probabilities → Risk Label
        │       + SHAP GradientExplainer
        │
        └─► Hybrid Decision (hybrid.py)
                Higher risk adopted (conservative)
                        │
                        ▼
               Final Risk: Low / Medium / High
               + Full explanation text
               + SHAP feature importances
               + Clinical recommendation
                        │
                        ▼
              PostgreSQL (Neon) via SQLAlchemy
              → Pending review queue → Doctor review → Patient feedback
```

---

## 🤖 Model Details

| Property | Value |
|----------|-------|
| Framework | TensorFlow / Keras (`.h5`) |
| Architecture | Sequential MLP |
| Input features | 11 |
| Layers | Dense(64,ReLU) → Dropout(0.3) → Dense(32,ReLU) → Dropout(0.3) → Dense(16,ReLU) → Dense(3,Softmax) |
| Output classes | 3: High (0), Low (1), Medium (2) |
| Scaler | MinMaxScaler on 6 numeric vitals |
| Explainability | SHAP GradientExplainer |

### Feature Vector (11 inputs)

| Index | Feature | Preprocessing |
|-------|---------|---------------|
| 0–5 | RR, SpO2, O2Scale, SBP, HR, Temp | MinMaxScaled |
| 6–9 | consciousness_C, _P, _U, _V | OHE (base=A, drop_first=True) |
| 10 | On_Oxygen | Binary 0/1 |

---

## 📁 Project Structure

```
clinical_dss/
├── app/
│   ├── main.py                  ← Entry point (set as Main file in Streamlit Cloud)
│   ├── config.py                ← All settings, reads st.secrets
│   ├── database.py              ← ORM models, NullPool engine, context manager
│   ├── auth.py                  ← Bcrypt auth, sessions, seeding, audit
│   ├── utils.py                 ← Validation, CSS, UI helpers
│   ├── risk_engine/             ← Separated package (clean architecture)
│   │   ├── __init__.py          ← Public: run_full_assessment()
│   │   ├── rules.py             ← Pure NEWS2 scoring (no framework imports)
│   │   ├── ml_model.py          ← Keras load, predict, SHAP
│   │   └── hybrid.py            ← Combines rules + ML, returns result dict
│   ├── models/
│   │   ├── risk_model.h5        ← Trained Keras DNN
│   │   └── scaler.pkl           ← Fitted MinMaxScaler
│   ├── pages/                   ← 7 Streamlit pages
│   └── components/              ← navbar, charts, alerts, pdf_generator
├── .streamlit/
│   └── config.toml              ← Theme + server settings
├── requirements.txt
├── packages.txt                 ← libgomp1 for TensorFlow on Ubuntu
└── .gitignore                   ← secrets.toml excluded
```

---

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/33Martin22/clinical_dss.git
cd clinical_dss
```

### 2. Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create secrets file

Create `.streamlit/secrets.toml`:

```toml
DATABASE_URL = "postgresql://neondb_owner:YOUR_PASSWORD@YOUR_HOST/neondb?sslmode=require&channel_binding=require"
SECRET_KEY   = "your-secret-key-minimum-32-characters"
```

### 5. Run

```bash
streamlit run app/main.py
```

---

## ☁️ Streamlit Cloud Deployment

### 1. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Deploy

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. **New app** → Repository: `33Martin22/clinical_dss`
3. Branch: `main`
4. Main file path: `app/main.py`
5. Click **Deploy**

### 3. Add secrets

Settings → Secrets → paste:

```toml
DATABASE_URL = "postgresql://neondb_owner:npg_96CcwnDqfOWA@ep-snowy-cell-alm0evzs-pooler.c-3.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
SECRET_KEY   = "clinical-dss-academic-2025-secure-key"
```

---

## 👤 Default Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@clinic.com | Admin@1234 |
| Doctor | doctor@clinic.com | Doctor@1234 |
| Patient | Register via the app | — |

---

## 🔒 Security Design

- Bcrypt password hashing (12 rounds)
- Role-based access control (patient / doctor / admin)
- No hardcoded credentials — all secrets via `st.secrets`
- NullPool database connections (no connection leaks)
- Context-manager sessions (always closed, even on `st.stop()`)
- Full PostgreSQL audit logging (persistent)
- Two-layer vital sign validation (hard block + soft warn)

---

## ⚠️ Disclaimer

This system is an academic demonstration of AI-assisted clinical decision
support. It is not validated for real clinical use and must not be used
with real patients or to make real clinical decisions.

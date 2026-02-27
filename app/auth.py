"""
auth.py
-------
Authentication, password hashing, Streamlit session management,
audit logging, and default account seeding.
"""
import logging

import streamlit as st
from passlib.context import CryptContext

from config import S_UID, S_ROLE, S_NAME, S_EMAIL
from database import get_db, User, Patient, AuditLog

log  = logging.getLogger(__name__)
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(email: str, password: str):
    """
    Validate credentials.
    Returns (User, None) on success or (None, error_message) on failure.
    """
    with get_db() as db:
        u = db.query(User).filter(
            User.email == email.lower().strip()
        ).first()

        if not u:
            return None, "No account found with that email address."
        if not u.is_active:
            return None, "This account has been deactivated. Contact the administrator."
        if not verify_password(password, u.password_hash):
            return None, "Incorrect password. Please try again."

        _write_audit(db, u.id, "LOGIN", f"{u.email} signed in.")
        # Detach from session so caller can use returned object freely
        db.expunge(u)
        return u, None


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(name: str, email: str, password: str,
                  role: str = "patient",
                  age: int = None, gender: str = None,
                  conditions: str = None):
    """
    Create a new user (and patient profile if role == 'patient').
    Returns (User, None) on success or (None, error_message) on failure.
    """
    with get_db() as db:
        if db.query(User).filter(
            User.email == email.lower().strip()
        ).first():
            return None, "That email address is already registered."

        u = User(
            name          = name.strip(),
            email         = email.lower().strip(),
            password_hash = hash_password(password),
            role          = role,
        )
        db.add(u)
        db.flush()   # get u.id before commit

        if role == "patient":
            db.add(Patient(
                user_id               = u.id,
                age                   = age,
                gender                = gender,
                underlying_conditions = conditions,
            ))

        db.commit()
        _write_audit(db, u.id, "REGISTER", f"New {role} registered: {u.email}")
        db.expunge(u)
        return u, None


# ── Streamlit session state ───────────────────────────────────────────────────

def set_session(u: User) -> None:
    st.session_state[S_UID]   = u.id
    st.session_state[S_ROLE]  = u.role
    st.session_state[S_NAME]  = u.name
    st.session_state[S_EMAIL] = u.email


def clear_session() -> None:
    for k in (S_UID, S_ROLE, S_NAME, S_EMAIL):
        st.session_state.pop(k, None)


def get_current_user() -> dict | None:
    uid = st.session_state.get(S_UID)
    if not uid:
        return None
    return {
        "id":    uid,
        "role":  st.session_state.get(S_ROLE),
        "name":  st.session_state.get(S_NAME),
        "email": st.session_state.get(S_EMAIL),
    }


def require_auth(allowed_roles: list = None) -> dict:
    """
    Guard function for every protected page.
    Calls st.stop() (halts page render) if user is not authenticated
    or does not have the required role.
    """
    user = get_current_user()
    if not user:
        st.warning("🔒 Please log in to access this page.")
        st.stop()
    if allowed_roles and user["role"] not in allowed_roles:
        st.error(
            f"🚫 Access denied. "
            f"This page requires role: **{', '.join(allowed_roles)}**"
        )
        st.stop()
    return user


# ── Audit logging ─────────────────────────────────────────────────────────────

def log_action(user_id: int, action: str, details: str = "") -> None:
    """Write an audit log entry. Fire-and-forget — never raises."""
    try:
        with get_db() as db:
            db.add(AuditLog(user_id=user_id, action=action, details=details))
            db.commit()
    except Exception as e:
        log.error(f"Audit log failed: {e}")


def _write_audit(db, user_id, action, details="") -> None:
    """Internal audit within an already-open session."""
    try:
        db.add(AuditLog(user_id=user_id, action=action, details=details))
        db.commit()
    except Exception:
        pass


# ── Default account seeding ───────────────────────────────────────────────────

def seed_defaults() -> None:
    """
    Create the default admin and doctor accounts if they do not exist.
    Safe to call on every startup — checks before inserting.
    Because PostgreSQL is persistent, seeding only actually writes once.
    """
    with get_db() as db:
        if db.query(User).filter(User.role == "admin").first():
            return   # Already seeded — do nothing

        db.add(User(
            name          = "System Administrator",
            email         = "admin@clinic.com",
            password_hash = hash_password("Admin@1234"),
            role          = "admin",
        ))
        db.add(User(
            name          = "Dr. Sarah Johnson",
            email         = "doctor@clinic.com",
            password_hash = hash_password("Doctor@1234"),
            role          = "doctor",
        ))
        db.commit()
        log.info("Default admin and doctor accounts seeded.")

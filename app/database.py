"""
database.py
-----------
SQLAlchemy ORM models, PostgreSQL engine with NullPool,
and a context-manager session helper that guarantees
connections are always returned to the pool — even when
st.stop() is called mid-page.
"""
from contextlib import contextmanager

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Text, DateTime, ForeignKey, Boolean,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import func

from config import DATABASE_URL
import logging

log  = logging.getLogger(__name__)
Base = declarative_base()


# ═══════════════════════════════════════════════════════════════════════════
# ORM Models
# ═══════════════════════════════════════════════════════════════════════════

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(120), nullable=False)
    email         = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(20),  nullable=False, default="patient")
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    patient_profile = relationship(
        "Patient", back_populates="user", uselist=False,
        foreign_keys="Patient.user_id",
    )
    audit_logs = relationship("AuditLog", back_populates="user")


class Patient(Base):
    __tablename__ = "patients"

    id                    = Column(Integer, primary_key=True, index=True)
    user_id               = Column(Integer, ForeignKey("users.id"),
                                   nullable=False, unique=True)
    age                   = Column(Integer)
    gender                = Column(String(30))
    underlying_conditions = Column(Text)
    assigned_doctor_id    = Column(Integer, ForeignKey("users.id"), nullable=True)

    user            = relationship("User", back_populates="patient_profile",
                                   foreign_keys=[user_id])
    assigned_doctor = relationship("User", foreign_keys=[assigned_doctor_id])
    assessments     = relationship("Assessment", back_populates="patient",
                                   cascade="all, delete-orphan")


class Assessment(Base):
    __tablename__ = "assessments"

    id                = Column(Integer, primary_key=True, index=True)
    patient_id        = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Raw vitals
    respiratory_rate  = Column(Integer, nullable=False)
    oxygen_saturation = Column(Integer, nullable=False)
    o2_scale          = Column(Integer, nullable=False)
    systolic_bp       = Column(Integer, nullable=False)
    heart_rate        = Column(Integer, nullable=False)
    temperature       = Column(Float,   nullable=False)
    consciousness     = Column(String(5), nullable=False)
    on_oxygen         = Column(Integer, nullable=False)

    # Risk engine outputs
    rule_score        = Column(Integer)
    ml_prediction     = Column(String(20))
    ml_probability    = Column(Float)
    final_risk        = Column(String(20))
    explanation       = Column(Text)
    recommendation    = Column(Text)

    # Workflow
    status            = Column(String(20), default="pending")  # pending | reviewed
    created_at        = Column(DateTime(timezone=True), server_default=func.now())

    patient      = relationship("Patient", back_populates="assessments")
    doctor_notes = relationship("DoctorNote", back_populates="assessment",
                                cascade="all, delete-orphan")


class DoctorNote(Base):
    __tablename__ = "doctor_notes"

    id            = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    doctor_id     = Column(Integer, ForeignKey("users.id"),       nullable=False)
    note          = Column(Text, nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    assessment = relationship("Assessment", back_populates="doctor_notes")
    doctor     = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    action    = Column(String(200), nullable=False)
    details   = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="audit_logs")


# ═══════════════════════════════════════════════════════════════════════════
# Engine + Session helpers
# ═══════════════════════════════════════════════════════════════════════════

def _make_engine():
    """
    NullPool: every request opens a fresh connection and closes it immediately.
    This is the correct strategy for Streamlit Cloud + Neon's free tier
    because it avoids exceeding the connection limit and prevents the
    'SSL connection has been closed unexpectedly' error on idle connections.
    """
    return create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )


def init_db() -> None:
    """
    Create all tables if they do not already exist.
    Safe to call on every page load — SQLAlchemy's CREATE TABLE IF NOT EXISTS
    means repeated calls are a no-op.
    """
    engine = _make_engine()
    try:
        Base.metadata.create_all(bind=engine)
        log.info("PostgreSQL tables verified / created.")
    finally:
        engine.dispose()


@contextmanager
def get_db():
    """
    Context-manager session.  Always closes the connection — even if
    st.stop() or an exception fires mid-page.

    Usage in every page:
        with get_db() as db:
            results = db.query(User).all()
    """
    engine    = _make_engine()
    Session   = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session   = Session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()

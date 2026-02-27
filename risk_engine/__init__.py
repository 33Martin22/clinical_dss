"""
risk_engine package
-------------------
Public interface: import run_full_assessment from here.
Pages never touch rules.py, ml_model.py, or hybrid.py directly.
"""
from .hybrid import run_full_assessment

__all__ = ["run_full_assessment"]

"""
Compatibility wrapper allowing `uvicorn api.main:app` as well as `uvicorn app.main:app`.
"""
from app.main import app

__all__ = ["app"]

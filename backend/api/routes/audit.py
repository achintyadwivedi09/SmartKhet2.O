"""
SmartKhet 2.0 — Audit API Routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from models.schemas import AuditLogFilter
from services.audit_service import audit_service

router = APIRouter()


@router.get("/logs")
def get_logs(
    actor: str = None,
    action: str = None,
    resource_type: str = None,
    status: str = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    """Return paginated audit logs with optional filters."""
    filters = AuditLogFilter(
        actor=actor,
        action=action,
        resource_type=resource_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return audit_service.get_logs(db, filters)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """Return a statistical summary of the audit log."""
    return audit_service.get_summary(db)


@router.post("/export")
def export_csv(db: Session = Depends(get_db)):
    """Export all audit logs to docs/SMARTKHET_PROJECT_AUDIT_LOG.csv."""
    path = audit_service.export_csv(db)
    return {"status": "exported", "file_path": path}

"""
SmartKhet 2.0 — Audit Service
Logs system events to the database and can export them as CSV.
"""
from __future__ import annotations
import csv
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import AUDIT_LOG_PATH
from models.db_models import AuditLog
from models.schemas import AuditLogCreate, AuditLogFilter, AuditLogResponse


class AuditService:
    """Central audit-trail service for SmartKhet 2.0."""

    def log(
        self,
        action: str,
        actor: str = "system",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        ip_address: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[AuditLog]:
        """Convenience wrapper for logging an audit event."""
        if db is None:
            return None
        return self.log_event(
            db=db,
            action=action,
            actor=actor,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            status=status,
            ip_address=ip_address,
        )

    def log_event(
        self,
        db: Session,
        action: str,
        actor: str = "system",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Persist an audit event to the database."""
        entry = AuditLog(
            timestamp=datetime.utcnow(),
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            status=status,
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def get_logs(
        self,
        db: Session,
        filters: AuditLogFilter,
    ) -> Dict[str, Any]:
        """Return paginated audit log records matching optional filters."""
        query = db.query(AuditLog)

        if filters.actor:
            query = query.filter(AuditLog.actor == filters.actor)
        if filters.action:
            query = query.filter(AuditLog.action.ilike(f"%{filters.action}%"))
        if filters.resource_type:
            query = query.filter(AuditLog.resource_type == filters.resource_type)
        if filters.status:
            query = query.filter(AuditLog.status == filters.status)
        if filters.start_date:
            query = query.filter(AuditLog.timestamp >= filters.start_date)
        if filters.end_date:
            query = query.filter(AuditLog.timestamp <= filters.end_date)

        total = query.count()
        offset = (filters.page - 1) * filters.page_size
        items = (
            query.order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(filters.page_size)
            .all()
        )

        return {
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size,
            "items": [AuditLogResponse.model_validate(i) for i in items],
        }

    def export_csv(self, db: Optional[Session] = None) -> str:
        """Export all audit logs to SMARTKHET_PROJECT_AUDIT_LOG.csv.

        Returns the absolute path of the written file.
        """
        close_needed = False
        if db is None:
            from app.database import SessionLocal
            db = SessionLocal()
            close_needed = True

        try:
            logs: List[AuditLog] = (
                db.query(AuditLog).order_by(AuditLog.timestamp.asc()).all()
            )
        finally:
            if close_needed:
                db.close()

        # Ensure docs/ directory exists
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)

        fieldnames = [
            "id", "timestamp", "actor", "action",
            "resource_type", "resource_id", "details", "status", "ip_address",
        ]

        with open(AUDIT_LOG_PATH, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for log in logs:
                writer.writerow(
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat() if log.timestamp else "",
                        "actor": log.actor,
                        "action": log.action,
                        "resource_type": log.resource_type or "",
                        "resource_id": log.resource_id or "",
                        "details": str(log.details) if log.details else "",
                        "status": log.status,
                        "ip_address": log.ip_address or "",
                    }
                )

        return AUDIT_LOG_PATH

    def get_summary(self, db: Session) -> Dict[str, Any]:
        """Return a brief summary of audit log statistics."""
        total = db.query(AuditLog).count()
        successes = db.query(AuditLog).filter(AuditLog.status == "success").count()
        warnings = db.query(AuditLog).filter(AuditLog.status == "warning").count()
        errors = db.query(AuditLog).filter(AuditLog.status == "error").count()
        latest = (
            db.query(AuditLog).order_by(AuditLog.timestamp.desc()).first()
        )
        return {
            "total_events": total,
            "successes": successes,
            "warnings": warnings,
            "errors": errors,
            "latest_event_at": latest.timestamp.isoformat() if latest else None,
        }


# Module-level singleton
audit_service = AuditService()

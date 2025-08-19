from fastapi import Request, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
import json

import crud
import models
import schemas
from security import get_current_user, get_db

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def get_changed_fields(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    """Compares two dictionaries and returns the fields that have changed."""
    changed = {}
    all_keys = set(before.keys()) | set(after.keys())
    for key in all_keys:
        before_val = before.get(key)
        after_val = after.get(key)
        if before_val != after_val:
            changed[key] = {"before": before_val, "after": after_val}
    return changed

class AuditLogger:
    def __init__(
        self,
        request: Request,
        db: Session = Depends(get_db),
        current_user: Optional[models.User] = None,
    ):
        self.db = db
        self.request = request
        self.current_user = current_user

    async def log(
        self,
        action: str,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        before_values: Optional[dict] = None,
        after_values: Optional[dict] = None,
        risk_level: str = 'low'
    ):
        changed_fields = get_changed_fields(before_values or {}, after_values or {}) if before_values or after_values else None

        # Serialize dictionaries with our custom handler to manage datetimes
        serializable_before = json.loads(json.dumps(before_values, default=json_serial)) if before_values else None
        serializable_after = json.loads(json.dumps(after_values, default=json_serial)) if after_values else None
        serializable_changed = json.loads(json.dumps(changed_fields, default=json_serial)) if changed_fields else None


        log_data = schemas.AuditLogCreate(
            user_type="staff" if self.current_user else "anonymous",
            user_id=self.current_user.id if self.current_user else None,
            user_name=self.current_user.full_name if self.current_user else "N/A",
            action=action,
            table_name=table_name,
            record_id=record_id,
            before_values=serializable_before,
            after_values=serializable_after,
            changed_fields=serializable_changed,
            ip_address=self.request.client.host if self.request.client else "N/A",
            user_agent=self.request.headers.get("user-agent", "N/A"),
            request_url=str(self.request.url),
            request_method=self.request.method,
            risk_level=risk_level,
        )
        crud.create_audit_log(self.db, log_data)

async def get_audit_logger(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
) -> AuditLogger:
    return AuditLogger(request=request, db=db, current_user=current_user)
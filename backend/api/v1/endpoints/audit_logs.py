from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db
import crud, schemas, security

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])

@router.get("/", response_model=schemas.PaginatedAuditLogResponse, dependencies=[Depends(security.require_permission("system.view_audit_logs"))])
def read_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logs = crud.get_audit_logs(db, skip=skip, limit=limit)
    total = crud.get_audit_logs_count(db)
    return {"items": logs, "total": total}

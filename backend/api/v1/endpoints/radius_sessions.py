from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from ..deps import get_db
from .... import crud, schemas, security, audit, freeradius_schemas

router = APIRouter()

@router.get("/", response_model=schemas.PaginatedResponse[freeradius_schemas.RadAcctResponse], dependencies=[Depends(security.require_permission("network.view_sessions"))])
def read_radius_sessions(skip: int = 0, limit: int = 100, active_only: bool = True, db: Session = Depends(get_db)):
    sessions = crud.get_radius_sessions(db, skip=skip, limit=limit, active_only=active_only)
    total = crud.get_radius_sessions_count(db, active_only=active_only)
    return schemas.PaginatedResponse(items=sessions, total=total)

@router.get("/{session_id}", response_model=freeradius_schemas.RadAcctResponse, dependencies=[Depends(security.require_permission("network.view_sessions"))])
def read_radius_session(session_id: int, db: Session = Depends(get_db)):
    """
    Get a specific RADIUS session by ID.
    """
    session = crud.get_radius_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="RADIUS session not found")
    return session

@router.post("/{session_id}/disconnect", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(security.require_permission("network.disconnect_sessions"))])
async def disconnect_radius_session(
    session_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Triggers a RADIUS Change of Authorization (CoA) or Disconnect-Message to terminate a user session.
    """
    db_session = crud.get_radius_session(db, session_id=session_id)
    if not db_session or db_session.acctstoptime is not None:
        raise HTTPException(status_code=404, detail="Active session not found")

    message = f"Triggered disconnect for session {db_session.acctsessionid} for user '{db_session.username}' on NAS {db_session.nasipaddress or 'Unknown'}"
    await logger.log("update", "radius_session", db_session.radacctid, after_values={"action": "disconnect"}, risk_level='high', business_context=message)

    print(f"INFO: Triggering disconnect for session {db_session.acctsessionid} for user {db_session.username} on NAS {db_session.nasipaddress or 'Unknown'}")
    return {"message": "Disconnect request sent to NAS."}

@router.get("/online/list", response_model=schemas.PaginatedResponse[schemas.CustomerOnlineStatus], dependencies=[Depends(security.require_permission("network.view_sessions"))])
def read_online_customers(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve currently online customers.
    """
    online_users = crud.get_online_customers(db, skip=skip, limit=limit)
    total = crud.get_online_customers_count(db)
    return schemas.PaginatedResponse(items=online_users, total=total)
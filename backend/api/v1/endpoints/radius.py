"""
RADIUS Session Management API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

import crud, schemas, security
from ..deps import get_db

router = APIRouter()

@router.get("/sessions", response_model=schemas.PaginatedResponse[schemas.RadiusSessionResponse], dependencies=[Depends(security.require_permission("network.view_sessions"))])
def get_radius_sessions(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(False)
):
    """
    Retrieve RADIUS sessions.
    """
    sessions = crud.get_radius_sessions(db, skip=skip, limit=limit, active_only=active_only)
    total = crud.get_radius_sessions_count(db, active_only=active_only)
    return schemas.PaginatedResponse(items=sessions, total=total)

@router.get("/sessions/{session_id}", response_model=schemas.RadiusSessionResponse, dependencies=[Depends(security.require_permission("network.view_sessions"))])
def get_radius_session(session_id: int, db: Session = Depends(get_db)):
    """
    Get a specific RADIUS session by ID.
    """
    session = crud.get_radius_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="RADIUS session not found")
    return session

@router.post("/sessions/{session_id}/disconnect", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(security.require_permission("network.disconnect_sessions"))])
def disconnect_radius_session(session_id: int, db: Session = Depends(get_db)):
    """
    Disconnect a RADIUS session (CoA - Change of Authorization).
    NOTE: This is a placeholder for the actual disconnection logic which would
    interact with the NAS/Router.
    """
    session = crud.get_radius_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="RADIUS session not found")
    if session.session_status != 'active':
        raise HTTPException(status_code=400, detail="Session is not active")

    # Placeholder for actual disconnection logic
    # e.g., radius_service.disconnect_session(session.session_id, session.nas.ip)
    
    return {"message": "Disconnection request sent", "session_id": session.session_id}

@router.get("/online", response_model=schemas.PaginatedResponse[schemas.CustomerOnlineResponse], dependencies=[Depends(security.require_permission("network.view_sessions"))])
def get_online_customers(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Retrieve currently online customers.
    """
    online_users = crud.get_online_customers(db, skip=skip, limit=limit)
    total = crud.get_online_customers_count(db)
    return schemas.PaginatedResponse(items=online_users, total=total)
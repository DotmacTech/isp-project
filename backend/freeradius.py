from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, literal
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from . import freeradius_crud
from . import schemas as main_schemas
from . import freeradius_schemas as fr_schemas
from .api.v1.deps import get_db
from .models import RadAcct, RadPostAuth, RadCheck, RadReply, InternetService
from . import security

router = APIRouter()

# --- User Management ---

@router.get(
    "/users/{username}",
    response_model=fr_schemas.RadiusUserResponse,
    dependencies=[Depends(security.require_permission("network.view_devices"))]
)
def get_radius_user(username: str, db: Session = Depends(get_db)):
    """
    Get a RADIUS user's attributes from radcheck and radreply.
    """
    user = freeradius_crud.get_radius_user(db, username=username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post(
    "/users/",
    response_model=fr_schemas.RadiusUserResponse,
    dependencies=[Depends(security.require_permission("network.manage_devices"))]
)
def create_or_update_radius_user(user: fr_schemas.RadiusUserCreate, db: Session = Depends(get_db)):
    """
    Create a new RADIUS user or update an existing one.
    This will replace all existing check and reply attributes for the user.
    """
    result = freeradius_crud.create_or_update_radius_user(db, user=user)
    db.commit()
    # Refresh the objects to get DB-assigned IDs before returning
    for attr in result["check_attributes"]:
        db.refresh(attr)
    for attr in result["reply_attributes"]:
        db.refresh(attr)
    return result

@router.delete(
    "/users/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(security.require_permission("network.manage_devices"))]
)
def delete_radius_user(username: str, db: Session = Depends(get_db)):
    """
    Delete a RADIUS user and all their attributes.
    """
    deleted = freeradius_crud.delete_radius_user_attributes(db, username=username)
    db.commit()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found, nothing to delete.")
    return

# --- Log Viewing ---

@router.get(
    "/logs/online/",
    response_model=main_schemas.PaginatedResponse[fr_schemas.RadAcctResponse],
    dependencies=[Depends(security.require_permission("network.view_sessions"))]
)
def get_online_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get a list of currently online users (active sessions).
    """
    query = db.query(RadAcct).filter(RadAcct.acctstoptime.is_(None))
    total = query.count()
    online_users = query.order_by(RadAcct.acctstarttime.desc()).offset(skip).limit(limit).all()
    return main_schemas.PaginatedResponse(items=online_users, total=total)

class SessionStats(BaseModel):
    online_count: int
    offline_count: int
    total_services: int

@router.get(
    "/sessions/stats",
    response_model=SessionStats,
    dependencies=[Depends(security.require_permission("network.view_sessions"))]
)
def get_session_stats(db: Session = Depends(get_db)):
    """Get statistics about online and offline sessions."""
    online_count = freeradius_crud.get_online_customers_count(db)
    total_services = db.query(InternetService).filter(InternetService.status == 'active').count()
    offline_count = total_services - online_count
    return SessionStats(
        online_count=online_count,
        offline_count=offline_count,
        total_services=total_services
    )

class ChartPoint(BaseModel):
    time: str
    value: int
    type: str = "Online Users"

@router.get(
    "/sessions/history-chart",
    response_model=List[ChartPoint],
    dependencies=[Depends(security.require_permission("network.view_sessions"))]
)
def get_session_history_chart_data(db: Session = Depends(get_db), hours: int = Query(24, ge=1, le=168), points: int = Query(24, ge=1, le=100)):
    """Returns time-series data for online users over the last N hours."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)
    interval_seconds = (hours * 3600) / points
    
    chart_data = []

    initial_count = db.query(func.count(RadAcct.radacctid)).filter(RadAcct.acctstarttime < since, RadAcct.acctstoptime.is_(None)).scalar() or 0
    
    starts = db.query(RadAcct.acctstarttime.label("time"), literal(1).label("change")).filter(RadAcct.acctstarttime > since).all()
    stops = db.query(RadAcct.acctstoptime.label("time"), literal(-1).label("change")).filter(RadAcct.acctstoptime > since).all()
    events = sorted(starts + stops, key=lambda x: x.time)

    current_count = initial_count
    event_index = 0
    for i in range(points):
        interval_end_time = since + timedelta(seconds=(i + 1) * interval_seconds)
        while event_index < len(events) and events[event_index].time <= interval_end_time:
            current_count += events[event_index].change
            event_index += 1
        chart_data.append({"time": interval_end_time.strftime('%Y-%m-%d %H:%M'), "value": current_count})
    return chart_data

@router.get(
    "/sessions/online/detailed/",
    response_model=main_schemas.PaginatedResponse[main_schemas.CustomerOnlineStatus],
    dependencies=[Depends(security.require_permission("network.view_sessions"))]
)
def get_online_customers_detailed(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get a list of currently online users with their associated customer and service details.
    """
    online_users = freeradius_crud.get_online_customers(db, skip=skip, limit=limit)
    total = freeradius_crud.get_online_customers_count(db)
    return main_schemas.PaginatedResponse(items=online_users, total=total)

@router.get(
    "/logs/accounting/",
    response_model=main_schemas.PaginatedResponse[fr_schemas.RadAcctResponse],
    dependencies=[Depends(security.require_permission("network.view_sessions"))]
)
def get_accounting_logs(
    skip: int = 0, limit: int = 100,
    username: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get historical accounting logs with filtering.
    """
    query = db.query(RadAcct)
    if username:
        query = query.filter(RadAcct.username.ilike(f"%{username}%"))
    if start_date:
        query = query.filter(RadAcct.acctstarttime >= start_date)
    if end_date:
        query = query.filter(RadAcct.acctstarttime <= end_date)
        
    total = query.count()
    logs = query.order_by(RadAcct.acctstarttime.desc()).offset(skip).limit(limit).all()
    return main_schemas.PaginatedResponse(items=logs, total=total)

@router.get(
    "/logs/postauth/",
    response_model=main_schemas.PaginatedResponse[fr_schemas.RadPostAuthResponse],
    dependencies=[Depends(security.require_permission("network.view_sessions"))]
)
def read_postauth_logs(username: Optional[str] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve RADIUS post-authentication (radpostauth) logs."""
    logs, total = freeradius_crud.get_postauth_logs(db, skip=skip, limit=limit, username=username)
    return main_schemas.PaginatedResponse(items=logs, total=total)

# --- Group Management Endpoints ---

class RadiusGroupCreateBody(BaseModel):
    checks: List[fr_schemas.RadGroupCheckCreateBody] = []
    replies: List[fr_schemas.RadGroupReplyCreateBody] = []

@router.post(
    "/groups/{groupname}",
    response_model=fr_schemas.RadiusGroupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(security.require_permission("network.manage_devices"))]
)
def create_or_update_radius_group(
    groupname: str,
    group_data: RadiusGroupCreateBody,
    db: Session = Depends(get_db)
):
    """Create or update a RADIUS group with its check and reply attributes."""
    result = freeradius_crud.create_or_update_radius_group(db, groupname=groupname, checks=group_data.checks, replies=group_data.replies)
    db.commit()
    for attr in result["check_attributes"]:
        db.refresh(attr)
    for attr in result["reply_attributes"]:
        db.refresh(attr)
    return result

@router.get(
    "/groups/{groupname}",
    response_model=fr_schemas.RadiusGroupResponse,
    dependencies=[Depends(security.require_permission("network.view_devices"))]
)
def read_radius_group(groupname: str, db: Session = Depends(get_db)):
    """Get a RADIUS group by name, including all its check and reply attributes."""
    db_group = freeradius_crud.get_radius_group(db, groupname=groupname)
    if db_group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RADIUS group not found")
    return db_group

@router.delete(
    "/groups/{groupname}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(security.require_permission("network.manage_devices"))]
)
def delete_radius_group(groupname: str, db: Session = Depends(get_db)):
    """Delete a RADIUS group, all its attributes, and unassign all users from it."""
    deleted = freeradius_crud.delete_radius_group(db, groupname=groupname)
    db.commit()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RADIUS group not found")
    return

# --- User-Group Assignment Endpoints ---

@router.post(
    "/users/{username}/groups",
    response_model=fr_schemas.RadUserGroupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(security.require_permission("network.manage_devices"))]
)
def assign_user_to_group(username: str, assignment: fr_schemas.RadUserGroupCreate, db: Session = Depends(get_db)):
    """Assign a RADIUS user to a group."""
    if username != assignment.username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username in path does not match username in body")
    db_assignment = freeradius_crud.assign_user_to_group(db, assignment=assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@router.delete(
    "/users/{username}/groups/{groupname}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(security.require_permission("network.manage_devices"))]
)
def remove_user_from_group(username: str, groupname: str, db: Session = Depends(get_db)):
    """Remove a RADIUS user from a group."""
    deleted = freeradius_crud.remove_user_from_group(db, username=username, groupname=groupname)
    db.commit()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User-group assignment not found")
    return
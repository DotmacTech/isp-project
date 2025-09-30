from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from .. import models

def get_radius_sessions(db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[models.RadAcct]:
    """Get RADIUS accounting sessions."""
    query = db.query(models.RadAcct)
    if active_only:
        query = query.filter(models.RadAcct.acctstoptime.is_(None))
    return query.order_by(models.RadAcct.radacctid.desc()).offset(skip).limit(limit).all()

def get_radius_sessions_count(db: Session, active_only: bool = False) -> int:
    """Get the total count of RADIUS accounting sessions."""
    query = db.query(models.RadAcct)
    if active_only:
        query = query.filter(models.RadAcct.acctstoptime.is_(None))
    return query.count()

def get_radius_session(db: Session, session_id: int) -> Optional[models.RadAcct]:
    """Get a specific RADIUS session by its radacctid."""
    return db.query(models.RadAcct).filter(models.RadAcct.radacctid == session_id).first()
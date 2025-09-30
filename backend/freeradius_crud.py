from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from . import models
from . import freeradius_schemas
from . import schemas as main_schemas

# --- User Management ---

def get_radius_user_check_attributes(db: Session, username: str) -> List[models.RadCheck]:
    """Get all check attributes for a given user."""
    return db.query(models.RadCheck).filter(models.RadCheck.username == username).all()

def get_radius_user_reply_attributes(db: Session, username: str) -> List[models.RadReply]:
    """Get all reply attributes for a given user."""
    return db.query(models.RadReply).filter(models.RadReply.username == username).all()

def get_radius_user(db: Session, username: str) -> Optional[dict]:
    """Get a RADIUS user with their attributes."""
    check_attrs = get_radius_user_check_attributes(db, username)
    if not check_attrs:
        return None
    reply_attrs = get_radius_user_reply_attributes(db, username)
    return {"username": username, "check_attributes": check_attrs, "reply_attributes": reply_attrs}

def delete_radius_user_attributes(db: Session, username: str) -> bool:
    """Delete all attributes for a given user from radcheck and radreply. Does not commit. Returns True if rows were deleted."""
    check_deleted = db.query(models.RadCheck).filter(models.RadCheck.username == username).delete(synchronize_session=False)
    reply_deleted = db.query(models.RadReply).filter(models.RadReply.username == username).delete(synchronize_session=False)
    return (check_deleted + reply_deleted) > 0
def create_or_update_radius_user(db: Session, user: freeradius_schemas.RadiusUserCreate) -> dict:
    """
    Creates or updates a RADIUS user by managing their attributes in radcheck and radreply.
    This function is destructive and replaces all existing attributes for the user.
    """
    username = user.username
    # First, remove all existing attributes for the user to ensure a clean state
    db.query(models.RadCheck).filter(models.RadCheck.username == username).delete(synchronize_session=False)
    db.query(models.RadReply).filter(models.RadReply.username == username).delete(synchronize_session=False)

    # Define attribute mappings to make the function more data-driven and easier to extend.
    attribute_map = {
        'check': {
            'Cleartext-Password': (user.password, ':=')
        },
        'reply': {
            'Mikrotik-Rate-Limit': (user.rate_limit, '='),
            'Framed-IP-Address': (user.framed_ip_address, '=')
        }
    }

    new_check_attrs = []
    new_reply_attrs = []

    for attr_name, (value, op) in attribute_map['check'].items():
        if value:
            new_check_attrs.append(models.RadCheck(username=username, attribute=attr_name, op=op, value=value))
    
    for attr_name, (value, op) in attribute_map['reply'].items():
        if value:
            new_reply_attrs.append(models.RadReply(username=username, attribute=attr_name, op=op, value=value))

    db.add_all(new_check_attrs + new_reply_attrs)

    return {
        "username": user.username,
        "check_attributes": new_check_attrs,
        "reply_attributes": new_reply_attrs
    }

# --- NAS Management (for internal sync) ---

def get_nas(db: Session, nas_id: int) -> Optional[models.Nas]:
    return db.query(models.Nas).filter(models.Nas.id == nas_id).first()

def get_nas_by_shortname(db: Session, shortname: str) -> Optional[models.Nas]:
    """Get a NAS entry by its shortname, which is linked to the router's title."""
    return db.query(models.Nas).filter(models.Nas.shortname == shortname).first()

def create_nas(db: Session, nas: freeradius_schemas.NasCreate) -> models.Nas:
    """Creates a NAS entry. Does not commit."""
    db_nas = models.Nas(**nas.model_dump())
    db.add(db_nas)
    return db_nas

def update_nas(db: Session, nas_id: int, nas_update_data: dict) -> Optional[models.Nas]:
    """Updates a NAS entry from a dictionary. Does not commit."""
    db_nas = get_nas(db, nas_id)
    if not db_nas:
        return None

    for key, value in nas_update_data.items():
        if hasattr(db_nas, key):
            setattr(db_nas, key, value)
        
    return db_nas

def delete_nas(db: Session, nas_id: int) -> Optional[models.Nas]:
    """Deletes a NAS entry. Does not commit."""
    db_nas = get_nas(db, nas_id)
    if not db_nas:
        return None
    db.delete(db_nas)
    return db_nas

# --- Group Management ---

def get_radius_group_check_attributes(db: Session, groupname: str) -> List[models.RadGroupCheck]:
    """Get all check attributes for a given group."""
    return db.query(models.RadGroupCheck).filter(models.RadGroupCheck.groupname == groupname).all()

def get_radius_group_reply_attributes(db: Session, groupname: str) -> List[models.RadGroupReply]:
    """Get all reply attributes for a given group."""
    return db.query(models.RadGroupReply).filter(models.RadGroupReply.groupname == groupname).all()

def create_or_update_radius_group(db: Session, groupname: str, checks: List[freeradius_schemas.RadGroupCheckCreateBody], replies: List[freeradius_schemas.RadGroupReplyCreateBody]) -> dict:
    """Creates or updates a RADIUS group by managing its attributes."""
    db.query(models.RadGroupCheck).filter(models.RadGroupCheck.groupname == groupname).delete(synchronize_session=False)
    db.query(models.RadGroupReply).filter(models.RadGroupReply.groupname == groupname).delete(synchronize_session=False)

    new_checks = [models.RadGroupCheck(groupname=groupname, **c.model_dump()) for c in checks]
    new_replies = [models.RadGroupReply(groupname=groupname, **r.model_dump()) for r in replies]

    # Add all new attributes in a single bulk operation for efficiency.
    db.add_all(new_checks + new_replies)

    return {"groupname": groupname, "check_attributes": new_checks, "reply_attributes": new_replies}

def get_radius_group(db: Session, groupname: str) -> Optional[dict]:
    """Get a RADIUS group with its attributes."""
    checks = get_radius_group_check_attributes(db, groupname)
    replies = get_radius_group_reply_attributes(db, groupname)
    if not checks and not replies:
        return None
    return {"groupname": groupname, "check_attributes": checks, "reply_attributes": replies}

def delete_radius_group(db: Session, groupname: str) -> bool:
    """Deletes a group, its attributes, and unassigns users."""
    check_count = db.query(models.RadGroupCheck).filter(models.RadGroupCheck.groupname == groupname).delete(synchronize_session=False)
    reply_count = db.query(models.RadGroupReply).filter(models.RadGroupReply.groupname == groupname).delete(synchronize_session=False)
    user_group_count = db.query(models.RadUserGroup).filter(models.RadUserGroup.groupname == groupname).delete(synchronize_session=False)
    
    if check_count > 0 or reply_count > 0 or user_group_count > 0:
        return True
    return False

# --- User-Group Assignment ---

def assign_user_to_group(db: Session, assignment: freeradius_schemas.RadUserGroupCreate) -> models.RadUserGroup:
    """Assigns a user to a group. Does not commit."""
    db_assignment = models.RadUserGroup(**assignment.model_dump())
    db.add(db_assignment)
    return db_assignment

def remove_user_from_group(db: Session, username: str, groupname: str) -> bool:
    """Removes a user from a group. Does not commit."""
    deleted_count = db.query(models.RadUserGroup).filter_by(username=username, groupname=groupname).delete(synchronize_session=False)
    return deleted_count > 0

# --- Log Viewing ---

def get_postauth_logs(db: Session, skip: int, limit: int, username: Optional[str] = None) -> (List[models.RadPostAuth], int):
    """Retrieve post-authentication logs."""
    query = db.query(models.RadPostAuth)
    if username:
        query = query.filter(models.RadPostAuth.username.ilike(f"%{username}%"))
    
    total = query.count()
    logs = query.order_by(models.RadPostAuth.authdate.desc()).offset(skip).limit(limit).all()
    return logs, total

def get_online_customers(db: Session, skip: int = 0, limit: int = 100) -> List[dict]:
    """Get currently online customers with their service details."""
    query = db.query(
        models.RadAcct,
        models.Customer,
        models.InternetService
    ).join(
        models.InternetService, models.RadAcct.username == models.InternetService.login
    ).join(
        models.Customer, models.InternetService.customer_id == models.Customer.id
    ).filter(
        models.RadAcct.acctstoptime.is_(None)
    )
    
    results = query.order_by(models.RadAcct.acctstarttime.desc()).offset(skip).limit(limit).all()
    
    online_customers = []
    for session, customer, service in results:
        session_start_time = session.acctstarttime if session.acctstarttime else datetime.utcnow()
        online_customers.append({
            "customer_id": customer.id, "customer_name": customer.name, "service_description": service.description,
            "login": session.username, "ip_address": session.framedipaddress, "mac_address": service.mac,
            "session_start_time": session_start_time, "session_time": (datetime.utcnow() - session_start_time).total_seconds(),
            "data_uploaded_mb": (session.acctoutputoctets or 0) / (1024*1024), "data_downloaded_mb": (session.acctinputoctets or 0) / (1024*1024),
        })
    return online_customers

def get_online_customers_count(db: Session) -> int:
    """Get the total count of online customers."""
    return db.query(models.RadAcct).join(
        models.InternetService, models.RadAcct.username == models.InternetService.login
    ).filter(models.RadAcct.acctstoptime.is_(None)).count()
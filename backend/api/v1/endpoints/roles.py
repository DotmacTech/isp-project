from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
import crud, schemas, security, audit

router = APIRouter(prefix="/roles", tags=["roles"])

@router.post("/", response_model=schemas.RoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_roles"))])
async def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db), logger: audit.AuditLogger = Depends(audit.get_audit_logger)):
    db_role = crud.get_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    new_role = crud.create_role(db=db, role=role)
    after_dict = schemas.RoleResponse.model_validate(new_role).model_dump()
    await logger.log("create", "roles", new_role.id, after_values=after_dict, risk_level='medium')
    return new_role

@router.get("/{role_id}", response_model=schemas.RoleResponse, dependencies=[Depends(security.require_permission("system.manage_roles"))])
def read_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud.get_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return db_role

@router.get("/", response_model=list[schemas.RoleResponse], dependencies=[Depends(security.require_permission("system.manage_roles"))])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    roles = crud.get_roles(db, skip=skip, limit=limit)
    return roles

@router.put("/{role_id}", response_model=schemas.RoleResponse, dependencies=[Depends(security.require_permission("system.manage_roles"))])
async def update_role(
    role_id: int, 
    role: schemas.RoleUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    # Capture state before the update
    db_role_before = crud.get_role(db, role_id)
    if not db_role_before:
        raise HTTPException(status_code=404, detail="Role not found")
    before_dict = schemas.RoleResponse.model_validate(db_role_before).model_dump()
    # Expire the object to ensure it's reloaded from the DB after the update
    db.expire(db_role_before)

    # Perform the update
    updated_role = crud.update_role(db=db, role_id=role_id, role_update=role)
    if not updated_role:
         raise HTTPException(status_code=404, detail="Role not found after update.")
    after_dict = schemas.RoleResponse.model_validate(updated_role).model_dump()

    # Log the action
    await logger.log("update", "roles", role_id, before_values=before_dict, after_values=after_dict, risk_level='medium')
    return updated_role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_roles"))])
async def delete_role(
    role_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_role_before = crud.get_role(db, role_id)
    if not db_role_before:
        raise HTTPException(status_code=404, detail="Role not found")
    before_dict = schemas.RoleResponse.model_validate(db_role_before).model_dump()

    deleted_role = crud.delete_role(db, role_id=role_id)
    if deleted_role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    await logger.log("delete", "roles", role_id, before_values=before_dict, risk_level='high')
    return None

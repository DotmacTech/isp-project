from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db
from .... import crud, schemas, security, audit

router = APIRouter()

@router.post("/", response_model=schemas.PermissionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_roles"))])
async def create_permission(
    permission: schemas.PermissionCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_permission = crud.get_permission_by_code(db, code=permission.code)
    if db_permission:
        raise HTTPException(status_code=400, detail="Permission code already exists")
    new_permission = crud.create_permission(db=db, permission=permission)
    after_dict = schemas.PermissionResponse.model_validate(new_permission).model_dump()
    await logger.log("create", "permissions", new_permission.id, after_values=after_dict, risk_level='medium')
    return new_permission

@router.get("/", response_model=List[schemas.PermissionResponse], dependencies=[Depends(security.require_permission("system.manage_roles"))])
def read_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    permissions = crud.get_permissions(db, skip=skip, limit=limit)
    return permissions

@router.put("/{permission_id}", response_model=schemas.PermissionResponse, dependencies=[Depends(security.require_permission("system.manage_roles"))])
async def update_permission(
    permission_id: int, 
    permission: schemas.PermissionUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_permission_before = crud.get_permission(db, permission_id=permission_id)
    if db_permission_before is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    before_dict = schemas.PermissionResponse.model_validate(db_permission_before).model_dump()
    db.expire(db_permission_before)

    updated_permission = crud.update_permission(db=db, permission_id=permission_id, permission_update=permission)
    if not updated_permission:
        raise HTTPException(status_code=404, detail="Permission not found after update.")
    after_dict = schemas.PermissionResponse.model_validate(updated_permission).model_dump()

    await logger.log("update", "permissions", permission_id, before_values=before_dict, after_values=after_dict, risk_level='medium')
    return updated_permission

@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.manage_roles"))])
async def delete_permission(
    permission_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_permission = crud.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    before_dict = schemas.PermissionResponse.model_validate(db_permission).model_dump()

    deleted_permission = crud.delete_permission(db=db, permission_id=permission_id)
    if deleted_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    await logger.log("delete", "permissions", permission_id, before_values=before_dict, risk_level='high')
    return None
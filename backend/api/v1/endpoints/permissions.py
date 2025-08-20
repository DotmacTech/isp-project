from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db
import crud, schemas, security

router = APIRouter(prefix="/permissions", tags=["permissions"])

@router.post("/", response_model=schemas.PermissionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.manage_roles"))])
def create_permission(permission: schemas.PermissionCreate, db: Session = Depends(get_db)):
    db_permission = crud.get_permission_by_code(db, code=permission.code)
    if db_permission:
        raise HTTPException(status_code=400, detail="Permission code already exists")
    return crud.create_permission(db=db, permission=permission)

@router.get("/", response_model=List[schemas.PermissionResponse], dependencies=[Depends(security.require_permission("system.manage_roles"))])
def read_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    permissions = crud.get_permissions(db, skip=skip, limit=limit)
    return permissions

@router.put("/{permission_id}", response_model=schemas.PermissionResponse, dependencies=[Depends(security.require_permission("system.manage_roles"))])
def update_permission(permission_id: int, permission: schemas.PermissionUpdate, db: Session = Depends(get_db)):
    db_permission = crud.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return crud.update_permission(db=db, permission_id=permission_id, permission_update=permission)

@router.delete("/{permission_id}", response_model=schemas.PermissionResponse, dependencies=[Depends(security.require_permission("system.manage_roles"))])
def delete_permission(permission_id: int, db: Session = Depends(get_db)):
    db_permission = crud.get_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return crud.delete_permission(db=db, permission_id=permission_id)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
from .... import crud, schemas, security

# Framework Permissions (Renamed endpoints)
router = APIRouter(prefix="/framework-permissions", tags=["framework-permissions"])

@router.post("/", response_model=schemas.FrameworkPermissionResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.configure_security"))])
def create_framework_permission(permission: schemas.FrameworkPermissionCreate, db: Session = Depends(get_db)):
    db_permission = crud.get_framework_permission_by_code(db, code=permission.code)
    if db_permission:
        raise HTTPException(status_code=400, detail="Framework Permission with this code already exists")
    return crud.create_framework_permission(db=db, permission=permission)

@router.get("/", response_model=list[schemas.FrameworkPermissionResponse], dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_framework_permissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    permissions = crud.get_framework_permissions(db, skip=skip, limit=limit)
    return permissions

@router.get("/{permission_id}", response_model=schemas.FrameworkPermissionResponse, dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_framework_permission(permission_id: int, db: Session = Depends(get_db)):
    db_permission = crud.get_framework_permission(db, permission_id=permission_id)
    if db_permission is None:
        raise HTTPException(status_code=404, detail="Framework Permission not found")
    return db_permission

# Framework Roles (Renamed endpoints)
framework_role_router = APIRouter(prefix="/framework-roles", tags=["framework-roles"])

@framework_role_router.post("/", response_model=schemas.FrameworkRoleResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.configure_security"))])
def create_framework_role(role: schemas.FrameworkRoleCreate, db: Session = Depends(get_db)):
    db_role = crud.get_framework_role_by_name(db, name=role.name)
    if db_role:
        raise HTTPException(status_code=400, detail="Framework Role with this name already exists")
    return crud.create_framework_role(db=db, role=role)

@framework_role_router.get("/", response_model=list[schemas.FrameworkRoleResponse], dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_framework_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    roles = crud.get_framework_roles(db, skip=skip, limit=limit)
    return roles

@framework_role_router.get("/{role_id}", response_model=schemas.FrameworkRoleResponse, dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_framework_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud.get_framework_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Framework Role not found")
    return db_role

@framework_role_router.put("/{role_id}", response_model=schemas.FrameworkRoleResponse, dependencies=[Depends(security.require_permission("system.configure_security"))])
def update_framework_role(role_id: int, role: schemas.FrameworkRoleUpdate, db: Session = Depends(get_db)):
    return crud.update_framework_role(db=db, role_id=role_id, role_update=role)

@framework_role_router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.configure_security"))])
def delete_framework_role(role_id: int, db: Session = Depends(get_db)):
    db_role = crud.delete_framework_role(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Framework Role not found")
    return

router.include_router(framework_role_router)

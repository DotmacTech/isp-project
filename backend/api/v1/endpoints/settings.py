from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
from .... import crud, schemas, security

router = APIRouter()

@router.post("/", response_model=schemas.Setting, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("system.configure_security"))])
def create_setting(setting: schemas.SettingCreate, db: Session = Depends(get_db)):
    db_setting = crud.get_setting_by_key(db, key=setting.config_key)
    if db_setting:
        raise HTTPException(status_code=400, detail="Setting with this key already exists")
    return crud.create_setting(db=db, setting=setting)

@router.get("/", response_model=list[schemas.Setting], dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_settings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    settings = crud.get_settings(db, skip=skip, limit=limit)
    return settings

@router.get("/{setting_id}", response_model=schemas.Setting, dependencies=[Depends(security.require_permission("system.configure_security"))])
def read_setting(setting_id: int, db: Session = Depends(get_db)):
    db_setting = crud.get_setting(db, setting_id=setting_id)
    if db_setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return db_setting

@router.put("/{setting_id}", response_model=schemas.Setting, dependencies=[Depends(security.require_permission("system.configure_security"))])
def update_setting(setting_id: int, setting: schemas.SettingUpdate, db: Session = Depends(get_db)):
    return crud.update_setting(db=db, setting_id=setting_id, setting=setting)

@router.delete("/{setting_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("system.configure_security"))])
def delete_setting(setting_id: int, db: Session = Depends(get_db)):
    db_setting = crud.delete_setting(db, setting_id=setting_id)
    if db_setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return

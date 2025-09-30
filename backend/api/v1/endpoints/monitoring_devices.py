from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Type, Any

from ..deps import get_db 
from .... import crud, schemas, models, security, audit

router = APIRouter()

@router.post("/devices/", response_model=schemas.MonitoringDeviceResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_devices"))])
async def create_monitoring_device(
    device: schemas.MonitoringDeviceCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    new_device = crud.create_monitoring_device(db=db, device=device)
    after_dict = schemas.MonitoringDeviceResponse.model_validate(new_device).model_dump()
    await logger.log("create", "monitoring_device", new_device.id, after_values=after_dict, risk_level='medium', business_context=f"Monitoring device '{new_device.title}' created.")
    return new_device

@router.get("/devices/", response_model=schemas.PaginatedMonitoringDeviceResponse, dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_monitoring_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    devices = crud.get_monitoring_devices(db, skip=skip, limit=limit)
    total = crud.get_monitoring_devices_count(db)
    return {"items": devices, "total": total}

@router.put("/devices/{device_id}", response_model=schemas.MonitoringDeviceResponse, dependencies=[Depends(security.require_permission("network.manage_devices"))])
async def update_monitoring_device(
    device_id: int, 
    device_update: schemas.MonitoringDeviceUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_device_before = crud.get_monitoring_device(db, device_id=device_id)
    if db_device_before is None:
        raise HTTPException(status_code=404, detail="Monitoring device not found")
    before_dict = schemas.MonitoringDeviceResponse.model_validate(db_device_before).model_dump()
    db.expire(db_device_before)

    updated_device = crud.update_monitoring_device(db, device_id=device_id, device_update=device_update)
    if updated_device is None:
        raise HTTPException(status_code=404, detail="Monitoring device not found after update.")
    after_dict = schemas.MonitoringDeviceResponse.model_validate(updated_device).model_dump()
    await logger.log("update", "monitoring_device", device_id, before_values=before_dict, after_values=after_dict, risk_level='medium', business_context=f"Monitoring device '{updated_device.title}' updated.")
    return updated_device

@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("network.manage_devices"))])
async def delete_monitoring_device(
    device_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_device_before = crud.get_monitoring_device(db, device_id=device_id)
    if db_device_before is None:
        raise HTTPException(status_code=404, detail="Monitoring device not found")
    before_dict = schemas.MonitoringDeviceResponse.model_validate(db_device_before).model_dump()

    deleted_device = crud.delete_monitoring_device(db, device_id=device_id)
    if not deleted_device:
        raise HTTPException(status_code=404, detail="Monitoring device not found")
    await logger.log("delete", "monitoring_device", device_id, before_values=before_dict, risk_level='high', business_context=f"Monitoring device '{before_dict.get('title')}' deleted.")
    return None

# --- Monitoring Configuration (Lookup Tables) ---
monitoring_config_router = APIRouter(dependencies=[Depends(security.require_permission("network.manage_devices"))])

def add_lookup_endpoints(model: Type[Any], tag: str):
    @monitoring_config_router.post(f"/{tag}/", response_model=schemas.NetworkLookupResponse, status_code=status.HTTP_201_CREATED)
    async def create_item(item: schemas.NetworkLookupCreate, db: Session = Depends(get_db), logger: audit.AuditLogger = Depends(audit.get_audit_logger)):
        new_item = crud.create_network_lookup(db, model, item)
        await logger.log("create", f"monitoring_config_{tag}", new_item.id, after_values={"name": new_item.name}, risk_level='low', business_context=f"Created monitoring config '{tag}': {new_item.name}")
        return new_item

    @monitoring_config_router.get(f"/{tag}/", response_model=List[schemas.NetworkLookupResponse])
    def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
        return crud.get_network_lookups(db, model, skip, limit)

    @monitoring_config_router.delete(f"/{tag}/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_item(item_id: int, db: Session = Depends(get_db), logger: audit.AuditLogger = Depends(audit.get_audit_logger)):
        item_before = crud.get_network_lookup(db, model, item_id)
        if not item_before:
            raise HTTPException(status_code=404, detail=f"{tag.capitalize()} not found")
        
        if not crud.delete_network_lookup(db, model, item_id):
            raise HTTPException(status_code=404, detail=f"{tag.capitalize()} not found")
        await logger.log("delete", f"monitoring_config_{tag}", item_id, before_values={"name": item_before.name}, risk_level='medium', business_context=f"Deleted monitoring config '{tag}': {item_before.name}")

add_lookup_endpoints(models.MonitoringDeviceType, "types")
add_lookup_endpoints(models.MonitoringGroup, "groups")
add_lookup_endpoints(models.MonitoringProducer, "producers")

router.include_router(monitoring_config_router)
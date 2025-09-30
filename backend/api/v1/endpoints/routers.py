from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..deps import get_db
from .... import crud, models, schemas, security, audit

router = APIRouter()

class RouterConnectionTest(BaseModel):
    ip: str
    api_login: str
    api_password: str
    api_port: int = 8728

@router.post("/test-connection", status_code=status.HTTP_200_OK, dependencies=[Depends(security.require_permission("network.manage_devices"))])
def test_router_connection(conn_data: RouterConnectionTest):
    """
    Tests the API connection to a router using the provided credentials.
    This is a non-database operation used to verify settings before saving.
    """
    # Placeholder for actual connection logic (e.g., using routeros-api)
    if conn_data.api_password:
        return {"status": "ok", "message": "Connection successful (Simulated)."}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Connection failed: Password is required for API connection.")

@router.post("/", response_model=schemas.RouterResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_devices"))])
async def create_router(
    router: schemas.RouterCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    if crud.get_router_by_ip(db, ip=router.ip):
        raise HTTPException(status_code=400, detail="Router with this IP already exists")
    if not crud.get_location(db, location_id=router.location_id):
        raise HTTPException(status_code=404, detail=f"Location with ID {router.location_id} not found")
    
    # Validate that all provided partner IDs exist
    if router.partners_ids:
        partners_count = db.query(models.Partner).filter(models.Partner.id.in_(router.partners_ids)).count()
        if partners_count != len(router.partners_ids):
            raise HTTPException(status_code=400, detail="One or more provided partner IDs are invalid.")
    new_router = crud.create_router(db=db, router=router)
    after_dict = schemas.RouterResponse.model_validate(new_router).model_dump()
    await logger.log("create", "router", new_router.id, after_values=after_dict, risk_level='high', business_context=f"Router '{new_router.title}' ({new_router.ip}) created.")
    return new_router

@router.get("/", response_model=schemas.PaginatedRouterResponse, dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_routers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    routers = crud.get_routers(db, skip=skip, limit=limit)
    total = crud.get_routers_count(db)
    return {"items": routers, "total": total}

@router.get("/{router_id}/", response_model=schemas.RouterResponse, dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_router(router_id: int, db: Session = Depends(get_db)):
    db_router = crud.get_router(db, router_id=router_id)
    if db_router is None:
        raise HTTPException(status_code=404, detail="Router not found")
    return db_router

@router.put("/{router_id}/", response_model=schemas.RouterResponse, dependencies=[Depends(security.require_permission("network.manage_devices"))])
async def update_router(
    router_id: int, 
    router_update: schemas.RouterUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_router_before = crud.get_router(db, router_id=router_id)
    if db_router_before is None:
        raise HTTPException(status_code=404, detail="Router not found")
    before_dict = schemas.RouterResponse.model_validate(db_router_before).model_dump()
    db.expire(db_router_before)

    # Validate that all provided partner IDs exist if they are being updated
    if router_update.partners_ids:
        partners_count = db.query(models.Partner).filter(models.Partner.id.in_(router_update.partners_ids)).count()
        if partners_count != len(router_update.partners_ids):
            raise HTTPException(status_code=400, detail="One or more provided partner IDs are invalid.")

    updated_router = crud.update_router(db, router_id=router_id, router_update=router_update)
    if updated_router is None:
        raise HTTPException(status_code=404, detail="Router not found after update.")
    after_dict = schemas.RouterResponse.model_validate(updated_router).model_dump()
    await logger.log("update", "router", router_id, before_values=before_dict, after_values=after_dict, risk_level='high', business_context=f"Router '{updated_router.title}' ({updated_router.ip}) updated.")
    return updated_router

@router.delete("/{router_id}/", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("network.manage_devices"))])
async def delete_router(
    router_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_router_before = crud.get_router(db, router_id=router_id)
    if db_router_before is None:
        raise HTTPException(status_code=404, detail="Router not found")
    before_dict = schemas.RouterResponse.model_validate(db_router_before).model_dump()

    deleted_router = crud.delete_router(db, router_id=router_id)
    if not deleted_router:
        raise HTTPException(status_code=404, detail="Router not found")
    await logger.log("delete", "router", router_id, before_values=before_dict, risk_level='critical', business_context=f"Router '{before_dict.get('title')}' ({before_dict.get('ip')}) deleted.")
    return None
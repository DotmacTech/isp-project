from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
from .... import crud, schemas, security, audit

router = APIRouter()

@router.post("/", response_model=schemas.NetworkSiteResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("network.manage_devices"))])
async def create_network_site(
    site: schemas.NetworkSiteCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    if not crud.get_location(db, location_id=site.location_id):
        raise HTTPException(status_code=404, detail=f"Location with ID {site.location_id} not found")
    new_site = crud.create_network_site(db=db, site=site)
    after_dict = schemas.NetworkSiteResponse.model_validate(new_site).model_dump()
    await logger.log("create", "network_site", new_site.id, after_values=after_dict, risk_level='medium', business_context=f"Network site '{new_site.title}' created.")
    return new_site

@router.get("/", response_model=schemas.PaginatedNetworkSiteResponse, dependencies=[Depends(security.require_permission("network.view_devices"))])
def read_network_sites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    sites = crud.get_network_sites(db, skip=skip, limit=limit)
    total = crud.get_network_sites_count(db)
    return {"items": sites, "total": total}

@router.put("/{site_id}", response_model=schemas.NetworkSiteResponse, dependencies=[Depends(security.require_permission("network.manage_devices"))])
async def update_network_site(
    site_id: int, 
    site_update: schemas.NetworkSiteUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_site_before = crud.get_network_site(db, site_id=site_id)
    if db_site_before is None:
        raise HTTPException(status_code=404, detail="Network site not found")
    before_dict = schemas.NetworkSiteResponse.model_validate(db_site_before).model_dump()
    db.expire(db_site_before)

    updated_site = crud.update_network_site(db, site_id=site_id, site_update=site_update)
    if updated_site is None:
        raise HTTPException(status_code=404, detail="Network site not found after update.")
    after_dict = schemas.NetworkSiteResponse.model_validate(updated_site).model_dump()
    await logger.log("update", "network_site", site_id, before_values=before_dict, after_values=after_dict, risk_level='medium', business_context=f"Network site '{updated_site.title}' updated.")
    return updated_site

@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("network.manage_devices"))])
async def delete_network_site(
    site_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_site_before = crud.get_network_site(db, site_id=site_id)
    if db_site_before is None:
        raise HTTPException(status_code=404, detail="Network site not found")
    before_dict = schemas.NetworkSiteResponse.model_validate(db_site_before).model_dump()

    deleted_site = crud.delete_network_site(db, site_id=site_id)
    if not deleted_site:
        raise HTTPException(status_code=404, detail="Network site not found")
    await logger.log("delete", "network_site", site_id, before_values=before_dict, risk_level='high', business_context=f"Network site '{before_dict.get('title')}' deleted.")
    return None
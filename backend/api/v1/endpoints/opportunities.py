from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from .... import crud
from .... import schemas, security, audit
from ..deps import get_db

router = APIRouter(
    dependencies=[Depends(security.require_permission("crm.manage_opportunities"))]
)

@router.get("/", response_model=schemas.PaginatedOpportunityResponse)
def read_opportunities(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    stage: Optional[str] = None
):
    """
    Retrieve opportunities with pagination.
    """
    opportunities = crud.get_opportunities(db, skip=skip, limit=limit, search=search, stage=stage)
    total = crud.get_opportunities_count(db, search=search, stage=stage)
    return {"items": opportunities, "total": total}

@router.post("/", response_model=schemas.OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    opportunity: schemas.OpportunityCreate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Create a new opportunity.
    """
    new_opportunity = crud.create_opportunity(db=db, opportunity=opportunity)
    after_dict = schemas.OpportunityResponse.model_validate(new_opportunity).model_dump()
    await logger.log("create", "opportunity", new_opportunity.id, after_values=after_dict, risk_level='low', business_context=f"Opportunity '{new_opportunity.name}' created.")
    return new_opportunity

@router.get("/{opportunity_id}", response_model=schemas.OpportunityResponse)
def read_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    db_opportunity = crud.get_opportunity(db, opportunity_id=opportunity_id)
    if db_opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return db_opportunity

@router.put("/{opportunity_id}", response_model=schemas.OpportunityResponse)
async def update_opportunity(
    opportunity_id: int,
    opportunity: schemas.OpportunityUpdate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_opportunity_before = crud.get_opportunity(db, opportunity_id=opportunity_id)
    if db_opportunity_before is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    before_dict = schemas.OpportunityResponse.model_validate(db_opportunity_before).model_dump()
    db.expire(db_opportunity_before)

    updated_opportunity = crud.update_opportunity(db=db, db_obj=db_opportunity_before, obj_in=opportunity)
    after_dict = schemas.OpportunityResponse.model_validate(updated_opportunity).model_dump()
    await logger.log("update", "opportunity", updated_opportunity.id, before_values=before_dict, after_values=after_dict, risk_level='low', business_context=f"Opportunity '{updated_opportunity.name}' updated.")
    return updated_opportunity

@router.delete("/{opportunity_id}", response_model=schemas.OpportunityResponse)
async def delete_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_opportunity_before = crud.get_opportunity(db, opportunity_id=opportunity_id)
    if db_opportunity_before is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    before_dict = schemas.OpportunityResponse.model_validate(db_opportunity_before).model_dump()

    db_opportunity = crud.delete_opportunity(db, opportunity_id=opportunity_id)
    if db_opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    await logger.log("delete", "opportunity", opportunity_id, before_values=before_dict, risk_level='medium', business_context=f"Opportunity '{before_dict.get('name')}' deleted.")
    return db_opportunity

@router.post("/{opportunity_id}/convert", response_model=schemas.CustomerResponse)
async def convert_opportunity(
    opportunity_id: int,
    conversion_data: schemas.OpportunityConvert,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_opportunity_before = crud.get_opportunity(db, opportunity_id=opportunity_id)
    if db_opportunity_before is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if db_opportunity_before.stage != "Closed Won":
        raise HTTPException(status_code=400, detail="Only 'Closed Won' opportunities can be converted.")
    if db_opportunity_before.customer_id:
        raise HTTPException(status_code=400, detail="This opportunity has already been converted.")
    
    try:
        customer = crud.convert_opportunity_to_customer(db, opportunity=db_opportunity_before, conversion_data=conversion_data)
        message = f"Opportunity '{db_opportunity_before.name}' converted to Customer '{customer.login}' (ID: {customer.id})."
        await logger.log("update", "opportunity", opportunity_id, after_values={"status": "converted", "customer_id": customer.id}, risk_level='high', business_context=message)
        return customer
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
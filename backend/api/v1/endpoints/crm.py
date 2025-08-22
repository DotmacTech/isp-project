from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_db
import crud, schemas, models, security

router = APIRouter(prefix="/crm", tags=["crm"])

# Lead Endpoints
@router.post("/leads/", response_model=schemas.LeadResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("crm.manage_leads"))])
def create_lead(
    lead: schemas.LeadCreate,
    db: Session = Depends(get_db)
):
    return crud.create_lead(db, lead)

@router.get("/leads/", response_model=schemas.PaginatedLeadResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_leads(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    leads = crud.get_leads(db, skip=skip, limit=limit, search=search, status=status)
    total = crud.get_leads_count(db, search=search, status=status)
    return {"items": leads, "total": total}

@router.get("/leads/{lead_id}", response_model=schemas.LeadResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    lead = crud.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

@router.put("/leads/{lead_id}", response_model=schemas.LeadResponse, dependencies=[Depends(security.require_permission("crm.manage_leads"))])
def update_lead(
    lead_id: int,
    lead_update: schemas.LeadUpdate,
    db: Session = Depends(get_db)
):
    db_lead = crud.get_lead(db, lead_id)
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return crud.update_lead(db=db, db_obj=db_lead, obj_in=lead_update)

@router.delete("/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("crm.manage_leads"))])
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    deleted_lead = crud.delete_lead(db, lead_id)
    if not deleted_lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return

# Opportunity Endpoints
@router.post("/opportunities/", response_model=schemas.OpportunityResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("crm.manage_opportunities"))])
def create_opportunity(
    opportunity: schemas.OpportunityCreate,
    db: Session = Depends(get_db)
):
    lead = crud.get_lead(db, opportunity.lead_id)
    if not lead:
        raise HTTPException(status_code=400, detail="Lead not found")
    return crud.create_opportunity(db, opportunity)

@router.get("/opportunities/", response_model=schemas.PaginatedOpportunityResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_opportunities(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    stage: Optional[str] = None,
    db: Session = Depends(get_db)
):
    opportunities = crud.get_opportunities(db, skip=skip, limit=limit, search=search, stage=stage)
    total = crud.get_opportunities_count(db, search=search, stage=stage)
    return {"items": opportunities, "total": total}

@router.get("/opportunities/{opportunity_id}", response_model=schemas.OpportunityResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    opportunity = crud.get_opportunity(db, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity

@router.put("/opportunities/{opportunity_id}", response_model=schemas.OpportunityResponse, dependencies=[Depends(security.require_permission("crm.manage_opportunities"))])
def update_opportunity(
    opportunity_id: int,
    opportunity_update: schemas.OpportunityUpdate,
    db: Session = Depends(get_db)
):
    db_opportunity = crud.get_opportunity(db, opportunity_id)
    if not db_opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return crud.update_opportunity(db=db, db_obj=db_opportunity, obj_in=opportunity_update)

@router.delete("/opportunities/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("crm.manage_opportunities"))])
def delete_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    deleted_opportunity = crud.delete_opportunity(db, opportunity_id)
    if not deleted_opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return

@router.post("/opportunities/{opportunity_id}/convert", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("crm.create_accounts"))])
def convert_opportunity(
    opportunity_id: int,
    conversion_data: schemas.OpportunityConvert,
    db: Session = Depends(get_db)
):
    """
    Converts a won opportunity into a new customer account.
    """
    opportunity = crud.get_opportunity(db, opportunity_id)
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    if opportunity.stage == "Closed Won" and opportunity.customer_id:
        raise HTTPException(status_code=400, detail="This opportunity has already been converted to a customer.")

    return crud.convert_opportunity_to_customer(db, opportunity, conversion_data)
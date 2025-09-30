from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .... import crud, schemas, security, audit
from ..deps import get_db

router = APIRouter()

@router.post("/", response_model=schemas.LeadResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("crm.manage_leads"))])
async def create_lead(
    lead: schemas.LeadCreate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Create a new lead.
    Requires 'crm.manage_leads' permission.
    """
    new_lead = crud.create_lead(db, lead)
    after_dict = schemas.LeadResponse.model_validate(new_lead).model_dump()
    await logger.log("create", "lead", new_lead.id, after_values=after_dict, risk_level='low', business_context=f"Lead '{new_lead.full_name}' created.")
    return new_lead

@router.get("/", response_model=schemas.PaginatedLeadResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_leads(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    search: Optional[str] = Query(None, description="Search by name, email, phone, or login"),
    status: Optional[str] = Query(None, description="Filter by lead status"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of leads with optional pagination and filtering.
    Requires 'crm.view_accounts' permission.
    """
    leads = crud.get_leads(db, skip=skip, limit=limit, search=search, status=status)
    total = crud.get_leads_count(db, search=search, status=status)
    return {"items": leads, "total": total}

@router.get("/{lead_id}", response_model=schemas.LeadResponse, dependencies=[Depends(security.require_permission("crm.view_accounts"))])
def read_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single lead by ID.
    Requires 'crm.view_accounts' permission.
    """
    lead = crud.get_lead(db, lead_id)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead

@router.put("/{lead_id}", response_model=schemas.LeadResponse, dependencies=[Depends(security.require_permission("crm.manage_leads"))])
async def update_lead(
    lead_id: int,
    lead_update: schemas.LeadUpdate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Update an existing lead.
    Requires 'crm.manage_leads' permission.
    """
    db_lead_before = crud.get_lead(db, lead_id)
    if not db_lead_before:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    before_dict = schemas.LeadResponse.model_validate(db_lead_before).model_dump()
    db.expire(db_lead_before)

    updated_lead = crud.update_lead(db=db, db_obj=db_lead_before, obj_in=lead_update)
    after_dict = schemas.LeadResponse.model_validate(updated_lead).model_dump()
    await logger.log("update", "lead", updated_lead.id, before_values=before_dict, after_values=after_dict, risk_level='low', business_context=f"Lead '{updated_lead.full_name}' updated.")
    return updated_lead

@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("crm.manage_leads"))])
async def delete_lead(
    lead_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Delete a lead.
    Requires 'crm.manage_leads' permission.
    """
    db_lead_before = crud.get_lead(db, lead_id)
    if not db_lead_before:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    before_dict = schemas.LeadResponse.model_validate(db_lead_before).model_dump()

    deleted_lead = crud.delete_lead(db, lead_id)
    if not deleted_lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    await logger.log("delete", "lead", lead_id, before_values=before_dict, risk_level='medium', business_context=f"Lead '{before_dict.get('full_name')}' deleted.")
    return None
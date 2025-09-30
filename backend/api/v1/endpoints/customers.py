from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .... import crud, schemas, security, audit
from ..deps import get_db # Assuming deps.py is in the same parent directory as endpoints

router = APIRouter()

@router.get(
    "/",
    response_model=schemas.PaginatedCustomerResponse,
    dependencies=[Depends(security.require_permission("crm.view_accounts"))]
)
def read_customers(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    search: Optional[str] = Query(None, description="Search by name, email, phone, or login"),
    status: Optional[str] = Query(None, description="Filter by customer status (e.g., active, blocked)"),
    db: Session = Depends(get_db)
):
    """
    Retrieve a list of customers with optional pagination and filtering.
    Requires 'crm.view_accounts' permission.
    """
    customers = crud.get_customers(db, skip=skip, limit=limit, search=search, status=status)
    total_customers = crud.get_customers_count(db, search=search, status=status)
    return {"total": total_customers, "items": customers}

@router.post(
    "/",
    response_model=schemas.CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(security.require_permission("crm.create_accounts"))]
)
async def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Create a new customer.
    Requires 'crm.create_accounts' permission.
    """
    # Check if login or email already exists to prevent duplicates
    if crud.get_customer_by_login(db, login=customer.login):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer with this login already exists")
    if customer.email and crud.get_customer_by_email(db, email=customer.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer with this email already exists")
    
    # Ensure partner_id and location_id exist
    if not crud.get_partner(db, partner_id=customer.partner_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    if not crud.get_location(db, location_id=customer.location_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    new_customer = crud.create_customer(db=db, customer=customer)
    after_dict = schemas.CustomerResponse.model_validate(new_customer).model_dump()
    await logger.log("create", "customer", new_customer.id, after_values=after_dict, risk_level='medium', business_context=f"Customer '{new_customer.login}' created.")
    return new_customer

@router.get(
    "/{customer_id}/",
    response_model=schemas.CustomerResponse,
    dependencies=[Depends(security.require_permission("crm.view_accounts"))]
)
def read_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a single customer by ID.
    Requires 'crm.view_accounts' permission.
    """
    db_customer = crud.get_customer(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return db_customer

@router.put(
    "/{customer_id}/",
    response_model=schemas.CustomerResponse,
    dependencies=[Depends(security.require_permission("crm.edit_accounts"))]
)
async def update_customer(
    customer_id: int,
    customer: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Update an existing customer.
    Requires 'crm.edit_accounts' permission.
    """
    db_customer_before = crud.get_customer(db, customer_id=customer_id)
    if db_customer_before is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    before_dict = schemas.CustomerResponse.model_validate(db_customer_before).model_dump()
    db.expire(db_customer_before)
    
    # Check for duplicate login/email if they are being updated
    if customer.login and customer.login != db_customer_before.login and crud.get_customer_by_login(db, login=customer.login):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer with this login already exists")
    if customer.email and customer.email != db_customer_before.email and crud.get_customer_by_email(db, email=customer.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Customer with this email already exists")

    # Ensure partner_id and location_id exist if they are being updated
    if customer.partner_id is not None and not crud.get_partner(db, partner_id=customer.partner_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    if customer.location_id is not None and not crud.get_location(db, location_id=customer.location_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    updated_customer = crud.update_customer(db=db, customer_id=customer_id, customer_update=customer)
    after_dict = schemas.CustomerResponse.model_validate(updated_customer).model_dump()
    await logger.log("update", "customer", updated_customer.id, before_values=before_dict, after_values=after_dict, risk_level='medium', business_context=f"Customer '{updated_customer.login}' updated.")
    return updated_customer

@router.delete(
    "/{customer_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(security.require_permission("crm.delete_accounts"))]
)
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Delete a customer.
    Requires 'crm.delete_accounts' permission.
    """
    db_customer_before = crud.get_customer(db, customer_id=customer_id)
    if db_customer_before is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    before_dict = schemas.CustomerResponse.model_validate(db_customer_before).model_dump()

    db_customer = crud.delete_customer(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    
    await logger.log("delete", "customer", customer_id, before_values=before_dict, risk_level='high', business_context=f"Customer '{before_dict.get('login')}' deleted.")
    return None

# Additional endpoints for customer-related resources (billing config, documents, etc.)

@router.get(
    "/{customer_id}/billing-config/",
    response_model=schemas.CustomerBillingResponse,
    dependencies=[Depends(security.require_permission("crm.view_accounts"))]
)
def get_customer_billing_config(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve a customer's billing configuration.
    Requires 'crm.view_accounts' permission.
    """
    db_customer = crud.get_customer(db, customer_id=customer_id)
    if db_customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if not db_customer.billing_config:
        # Return a default or empty billing config if none exists
        return schemas.CustomerBillingResponse(customer_id=customer_id, enabled=False)
    return db_customer.billing_config

@router.put(
    "/{customer_id}/billing-config/",
    response_model=schemas.CustomerBillingResponse,
    dependencies=[Depends(security.require_permission("crm.edit_accounts"))]
)
async def update_customer_billing_config(
    customer_id: int,
    billing_config: schemas.CustomerBillingBase,
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    """
    Update a customer's billing configuration.
    Requires 'crm.edit_accounts' permission.
    """
    db_customer_before = crud.get_customer(db, customer_id=customer_id)
    if db_customer_before is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    
    before_dict = {}
    if db_customer_before.billing_config:
        before_dict = schemas.CustomerBillingResponse.model_validate(db_customer_before.billing_config).model_dump()
    db.expire(db_customer_before)

    # The crud.update_customer function already handles nested billing_config updates
    # We can reuse it by creating a CustomerUpdate schema with only billing_config set
    customer_update_schema = schemas.CustomerUpdate(billing_config=billing_config)
    updated_customer = crud.update_customer(db=db, customer_id=customer_id, customer_update=customer_update_schema)
    
    if not updated_customer or not updated_customer.billing_config:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update billing configuration")

    after_dict = schemas.CustomerBillingResponse.model_validate(updated_customer.billing_config).model_dump()
    await logger.log("update", "customer_billing_config", customer_id, before_values=before_dict, after_values=after_dict, risk_level='medium', business_context=f"Updated billing configuration for customer ID {customer_id}.")

    return updated_customer.billing_config
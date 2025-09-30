from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_db 
from .... import crud, schemas, security, models, audit

router = APIRouter()

@router.get("/", response_model=List[schemas.PaymentMethodResponse], dependencies=[Depends(security.require_permission("billing.process_payments"))])
def read_payment_methods(
    db: Session = Depends(get_db), 
    is_active: Optional[bool] = True, 
    current_user: models.User = Depends(security.get_current_active_user)
):
    # If a user wants to see all methods (is_active=False), they need higher permissions.
    if is_active is False:
        # This re-uses the permission for managing tariffs, which is appropriate for this level of config.
        if not security.has_permission(db, user_id=current_user.id, permission_code="billing.manage_tariffs"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view all payment methods")

    return crud.get_payment_methods(db, is_active=is_active)

@router.post("/", response_model=schemas.PaymentMethodResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
async def create_payment_method(
    method: schemas.PaymentMethodCreate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    new_method = crud.create_payment_method(db, method)
    after_dict = schemas.PaymentMethodResponse.model_validate(new_method).model_dump()
    await logger.log("create", "payment_method", new_method.id, after_values=after_dict, risk_level='medium')
    return new_method

@router.put("/{method_id}", response_model=schemas.PaymentMethodResponse, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
async def update_payment_method(
    method_id: int, 
    method_update: schemas.PaymentMethodUpdate, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_method_before = crud.get_payment_method(db, method_id)
    if not db_method_before:
        raise HTTPException(status_code=404, detail="Payment method not found")
    before_dict = schemas.PaymentMethodResponse.model_validate(db_method_before).model_dump()
    db.expire(db_method_before)

    updated_method = crud.update_payment_method(db, method_id, method_update)
    if not updated_method:
        raise HTTPException(status_code=404, detail="Payment method not found after update.")
    after_dict = schemas.PaymentMethodResponse.model_validate(updated_method).model_dump()

    await logger.log("update", "payment_method", method_id, before_values=before_dict, after_values=after_dict, risk_level='medium')
    return updated_method

@router.delete("/{method_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(security.require_permission("billing.manage_tariffs"))])
async def delete_payment_method(
    method_id: int, 
    db: Session = Depends(get_db),
    logger: audit.AuditLogger = Depends(audit.get_audit_logger)
):
    db_method_before = crud.get_payment_method(db, method_id)
    if not db_method_before:
        raise HTTPException(status_code=404, detail="Payment method not found")
    before_dict = schemas.PaymentMethodResponse.model_validate(db_method_before).model_dump()

    try:
        if not crud.delete_payment_method(db, method_id):
            raise HTTPException(status_code=404, detail="Payment method not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    
    await logger.log("delete", "payment_method", method_id, before_values=before_dict, risk_level='high')
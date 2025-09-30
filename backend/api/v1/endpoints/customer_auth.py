from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from ..deps import get_db
from .... import schemas, security, crud, auth_utils
from typing import Optional

router = APIRouter()

@router.post("/token", response_model=schemas.Token)
async def login_customer_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a customer and provide an access token.
    """
    # Authenticate customer by login (email) and password
    customer = authenticate_customer(db, form_data.username, form_data.password)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token for customer
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": str(customer.id), "customer": True}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def authenticate_customer(db: Session, login: str, password: str) -> Optional[crud.models.Customer]:
    """
    Authenticate a customer by login and password.
    """
    customer = crud.get_customer_by_login(db, login=login)
    if not customer or not customer.password_hash:
        return None
    if not auth_utils.verify_password(password, customer.password_hash):
        return None
    return customer
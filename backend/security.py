from datetime import datetime, timedelta
from typing import Optional # Removed List from typing import
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import schemas, models
from api.v1.deps import get_db
from auth_utils import verify_password
# Configuration for JWT
import os

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Authenticate user (for /token endpoint)
def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    import crud
    user = crud.get_user_by_email(db, email=email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    import crud
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception
    return user

# Get current active user (requires user to be active)
async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

# Get current administrator profile (requires user to be an admin)
async def get_current_administrator(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> models.Administrator:
    import crud
    admin_profile = crud.get_administrator_by_user_id(db=db, user_id=current_user.id)
    if not admin_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not an administrator")
    return admin_profile

# RBAC: Check for specific permission
def require_permission(permission_code: str):
    async def permission_checker(current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        import crud
        user_permissions = crud.get_user_permissions(db, current_user.id)
        if permission_code not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {permission_code}",
            )
        return current_user
    return permission_checker

# RBAC: Check for specific roles
def require_roles(role_names: list[str]): # Changed List to list
    async def role_checker(current_user: models.User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        import crud
        # Efficiently fetch role names in a single query to avoid N+1 problem
        assigned_role_names_query = db.query(models.Role.name).join(models.UserRole).filter(models.UserRole.user_id == current_user.id)
        assigned_role_names = {name for name, in assigned_role_names_query}

        required_roles_set = set(role_names)

        # Check if there is any intersection between the roles the user has and the roles that are required.
        if not assigned_role_names.intersection(required_roles_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough roles. Required one of: {', '.join(role_names)}",
            )
        return current_user
    return role_checker

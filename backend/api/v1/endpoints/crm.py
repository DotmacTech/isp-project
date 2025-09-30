from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_db
import crud, schemas, models, security

router = APIRouter(prefix="/crm", tags=["crm"])
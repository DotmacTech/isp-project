from fastapi import APIRouter, Depends

from .... import security

router = APIRouter(
    prefix="/support/config",
    tags=["support-config"],
    dependencies=[Depends(security.require_permission("support.manage_config"))]
)

@router.get("/")
async def read_support_config():
    # Placeholder for support configuration endpoints like managing ticket statuses, types, etc.
    return {"message": "Support configuration endpoint is active."}
from fastapi import APIRouter

from .endpoints import (
    administrators, audit_logs, auth, customers, framework, locations,
    partners, permissions, roles, settings, user_roles, users
)

api_router = APIRouter()

api_router.include_router(administrators.router)
api_router.include_router(audit_logs.router)
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(framework.router)
api_router.include_router(locations.router)
api_router.include_router(partners.router)
api_router.include_router(permissions.router)
api_router.include_router(roles.router)
api_router.include_router(settings.router)
api_router.include_router(user_roles.router)
api_router.include_router(users.router)


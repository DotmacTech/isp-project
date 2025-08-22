import pytest
from fastapi import status
import crud
import schemas
import security

# Test API access control based on permissions

def test_unauthenticated_access_denied(test_client):
    """
    Tests that an unauthenticated request to a protected endpoint is denied.
    """
    response = test_client.get("/api/v1/billing/invoices/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_permission_denied_for_basic_user(basic_user, test_client):
    """
    Tests that a logged-in user with no roles/permissions is denied access.
    """
    token = security.create_access_token(data={"sub": str(basic_user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    
    response = test_client.get("/api/v1/billing/invoices/", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "Not enough permissions" in response.json()["detail"]
    assert "billing.view_invoices" in response.json()["detail"]

def test_permission_granted_for_authorized_user(test_client, billing_manager_auth_headers):
    """
    Tests that a user with the correct permission ('billing.view_invoices') is granted access.
    """
    response = test_client.get("/api/v1/billing/invoices/", headers=billing_manager_auth_headers)
    assert response.status_code == status.HTTP_200_OK

def test_super_admin_has_all_access(test_client, super_admin_auth_headers):
    """
    Tests that the Super Admin can access any protected endpoint.
    """
    response = test_client.get("/api/v1/billing/invoices/", headers=super_admin_auth_headers)
    assert response.status_code == status.HTTP_200_OK

# Test Role and Permission Management

def test_role_management_permissions(test_client, super_admin_auth_headers, billing_manager_auth_headers):
    """
    Tests that only users with 'system.manage_roles' can manage roles.
    """
    # 1. Super Admin can create a role
    role_data = {
        "name": "Test Role From API",
        "description": "A test role",
        "permission_codes": ["crm.view_accounts"]
    }
    response = test_client.post("/api/v1/roles/", json=role_data, headers=super_admin_auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "Test Role From API"

    # 2. Billing Manager (without system.manage_roles) cannot create a role
    response = test_client.post("/api/v1/roles/", json=role_data, headers=billing_manager_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_user_role_assignment(test_client, super_admin_auth_headers, db_session, basic_user, billing_manager_role):
    """
    Tests assigning and removing roles from a user.
    """
    # 1. Assign role
    assignment_data = {
        "user_id": basic_user.id,
        "role_id": billing_manager_role.id
    }
    response = test_client.post("/api/v1/user-roles/", json=assignment_data, headers=super_admin_auth_headers)
    assert response.status_code == status.HTTP_201_CREATED

    # Verify assignment in DB
    user_roles = crud.get_user_roles(db_session, basic_user.id)
    assert len(user_roles) == 1
    assert user_roles[0].role_id == billing_manager_role.id

    # 2. Remove role
    response = test_client.delete(f"/api/v1/user-roles/?user_id={basic_user.id}&role_id={billing_manager_role.id}", headers=super_admin_auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify removal in DB
    user_roles_after_removal = crud.get_user_roles(db_session, basic_user.id)
    assert len(user_roles_after_removal) == 0

# Test CRUD logic for permissions

def test_permission_inheritance_logic(db_session, basic_user):
    """
    Tests that the permission logic correctly includes permissions from parent roles.
    This is a direct test of the CRUD function, not an API test.
    """
    # 1. Create permissions if they don't exist
    perm_parent_code = "test.parent.view"
    perm_child_code = "test.child.edit"
    if not crud.get_permission_by_code(db_session, perm_parent_code):
        crud.create_permission(db_session, schemas.PermissionCreate(code=perm_parent_code, description="Parent", module="test"))
    if not crud.get_permission_by_code(db_session, perm_child_code):
        crud.create_permission(db_session, schemas.PermissionCreate(code=perm_child_code, description="Child", module="test"))

    # 2. Create roles with hierarchy
    parent_role = crud.create_role(db_session, schemas.RoleCreate(name="Parent Test Role", permission_codes=[perm_parent_code]))
    child_role = crud.create_role(db_session, schemas.RoleCreate(name="Child Test Role", permission_codes=[perm_child_code], parent_role_id=parent_role.id))

    # 3. Assign child role to user
    crud.assign_role_to_user(db_session, schemas.UserRoleCreate(user_id=basic_user.id, role_id=child_role.id))

    # 4. Get effective permissions
    # We pass customer_id=None and reseller_id=None to check for system-scoped roles
    effective_permissions = crud.get_user_permissions(db_session, user_id=basic_user.id, customer_id=None, reseller_id=None)

    # 5. Assert that both parent and child permissions are present
    assert perm_parent_code in effective_permissions
    assert perm_child_code in effective_permissions
    assert len(effective_permissions) >= 2
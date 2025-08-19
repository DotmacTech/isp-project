import os
import sys
from sqlalchemy.orm import Session

# Add project root to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import SessionLocal
import crud
import schemas

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def fix_superadmin_role(admin_email: str):
    db: Session = next(get_db())
    print(f"Attempting to fix roles for user: {admin_email}")

    # 1. Find the user
    user = crud.get_user_by_email(db, email=admin_email)
    if not user:
        print(f"Error: User with email '{admin_email}' not found.")
        db.close()
        return

    print(f"Found user: {user.full_name} (ID: {user.id})")

    # 2. Find or create the "Super Admin" role
    super_admin_role = crud.get_role_by_name(db, name="Super Admin")
    if not super_admin_role:
        print("Super Admin role not found. Creating it now...")
        # Get all permissions to assign to the new role
        all_permissions = crud.get_permissions(db, limit=1000) # Assuming less than 1000 permissions
        all_permission_codes = [p.code for p in all_permissions]
        
        role_create_schema = schemas.RoleCreate(
            name="Super Admin",
            description="Full control of all system functions",
            scope=schemas.RoleScope.system,
            permission_codes=all_permission_codes
        )
        super_admin_role = crud.create_role(db, role=role_create_schema)
        print(f"Created 'Super Admin' role (ID: {super_admin_role.id}) with {len(all_permission_codes)} permissions.")
    else:
        print(f"Found 'Super Admin' role (ID: {super_admin_role.id})")

    # 3. Ensure the Super Admin role has ALL permissions (in case new ones were added)
    all_permission_codes = [p.code for p in crud.get_permissions(db, limit=1000)]
    # Eagerly load permissions to avoid extra queries
    current_role_permission_codes = {rp.permission.code for rp in super_admin_role.role_permissions}
    
    missing_permissions = set(all_permission_codes) - current_role_permission_codes
    
    if missing_permissions:
        print(f"Found {len(missing_permissions)} missing permissions for Super Admin role. Updating...")
        updated_permission_codes = list(current_role_permission_codes.union(missing_permissions))
        role_update_schema = schemas.RoleUpdate(permission_codes=updated_permission_codes)
        crud.update_role(db, role_id=super_admin_role.id, role_update=role_update_schema)
        print("Super Admin role permissions have been synchronized.")
    else:
        print("Super Admin role already has all permissions. No update needed.")

    # 4. Check if the user is already assigned this role
    user_has_role = any(
        ur.role_id == super_admin_role.id for ur in user.user_roles
    )

    if user_has_role:
        print(f"User '{admin_email}' already has the 'Super Admin' role. No changes needed for assignment.")
    else:
        print(f"User '{admin_email}' does not have the 'Super Admin' role. Assigning it now...")
        user_role_create = schemas.UserRoleCreate(user_id=user.id, role_id=super_admin_role.id)
        crud.assign_role_to_user(db, user_role=user_role_create)
        print("Successfully assigned 'Super Admin' role.")

    print("\nFix process complete.")
    db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_superadmin_role.py <admin_email>")
        sys.exit(1)
    
    email_to_fix = sys.argv[1]
    fix_superadmin_role(email_to_fix)
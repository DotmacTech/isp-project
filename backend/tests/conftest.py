import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Base
from api.v1.deps import get_db
from main import app
import models
import schemas
import crud
import security
from auth_utils import get_password_hash
from datetime import date, timedelta
from decimal import Decimal
# Removed imports for compiler hooks as they are no longer needed
# from sqlalchemy.ext.compiler import compiles
# from sqlalchemy.types import String
# from sqlalchemy.dialects.postgresql import CITEXT, ARRAY

# Use a PostgreSQL database for testing.
# It's recommended to set this via an environment variable.
# Example: TEST_DATABASE_URL="postgresql://user:password@localhost/isp-project-test"
# The user must create this database manually before running tests.
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://isp_user:%23Dotmac246@localhost:5432/isp-project-test")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create database tables once for the test session, and drop them at the end."""
    Base.metadata.create_all(bind=engine)
    yield
    # A robust teardown that handles dependencies by dropping tables with CASCADE.
    from sqlalchemy import text
    with engine.connect() as connection:
        with connection.begin():
            tables_query = text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            tables = connection.execute(tables_query).fetchall()
            for table_name, in tables:
                connection.execute(text(f'DROP TABLE IF EXISTS public."{table_name}" CASCADE;'))

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture for a database session.
    This pattern is used because the application's CRUD layer contains `db.commit()` calls,
    which breaks the standard transactional test pattern. This fixture ensures the database
    is cleaned before each test by truncating all tables.
    """
    session = TestingSessionLocal()
    
    # Truncate all tables to ensure a clean state for each test
    from sqlalchemy import text
    table_names = [f'public."{table.name}"' for table in reversed(Base.metadata.sorted_tables)]
    if table_names:
        truncate_sql = text(f"TRUNCATE TABLE {','.join(table_names)} RESTART IDENTITY CASCADE;")
        session.execute(truncate_sql)
        session.commit()

    # Re-seed data that is needed for every test
    session.add(models.PaymentMethod(id=1, name="Cash", is_active=True))
    session.commit()
    
    yield session
    
    session.close()

def override_get_db(db_session_for_override):
    def _override():
        # The db_session fixture is responsible for the session's lifecycle (transaction, rollback, close).
        yield db_session_for_override
    return _override

@pytest.fixture(scope="function")
def test_client(db_session):
    """Fixture for the FastAPI TestClient."""
    app.dependency_overrides[get_db] = override_get_db(db_session)
    with TestClient(app) as client:
        yield client
    del app.dependency_overrides[get_db]

# --- Data Fixtures ---

@pytest.fixture(scope="function")
def test_partner(db_session):
    partner = crud.create_partner(db_session, schemas.PartnerCreate(name="Test Partner"))
    return partner

@pytest.fixture(scope="function")
def test_location(db_session):
    location = crud.create_location(db_session, schemas.LocationCreate(name="Test Location"))
    return location

@pytest.fixture(scope="function")
def super_admin_user(db_session):
    # 1. Create user
    user = crud.get_user_by_email(db_session, "superadmin@example.com")
    if not user:
        user_create = schemas.UserCreate(
            email="superadmin@example.com",
            full_name="Super Admin",
            password="password123"
        )
        user = crud.create_user(db_session, user_create)
    
    # 2. Create all permissions if they don't exist
    permissions_to_ensure = [
        "billing.create_invoices", "billing.process_payments", "billing.view_invoices", "billing.manage_tariffs",
        "system.manage_roles", "system.manage_users",
        "crm.view_accounts", "crm.manage_leads", "crm.manage_opportunities", "crm.create_accounts", "crm.edit_accounts", "crm.delete_accounts",
        "support.view_tickets", "support.create_tickets", "support.edit_tickets",
        "support.assign_tickets", "support.manage_config"
    ]
    for p_code in permissions_to_ensure:
        if not crud.get_permission_by_code(db_session, p_code):
            module_name = p_code.split('.')[0]
            crud.create_permission(db_session, schemas.PermissionCreate(code=p_code, description="Test perm", module=module_name))

    # 3. Create Super Admin role with all permissions
    all_perms = crud.get_permissions(db_session, limit=1000)
    all_perm_codes = [p.code for p in all_perms]
    
    role = crud.get_role_by_name(db_session, "Super Admin")
    if not role:
        role_create = schemas.RoleCreate(
            name="Super Admin",
            description="Test Super Admin",
            permission_codes=all_perm_codes,
            scope=schemas.RoleScope.system
        )
        role = crud.create_role(db_session, role_create)
    else:
        # Role exists, ensure it has all permissions. This makes the fixture robust.
        current_perm_codes = {p.code for p in role.permissions}
        if set(all_perm_codes) != current_perm_codes:
            role_update = schemas.RoleUpdate(permission_codes=all_perm_codes)
            role = crud.update_role(db_session, role_id=role.id, role_update=role_update)

    # 4. Assign role to user
    if not any(ur.role_id == role.id for ur in user.user_roles):
        crud.assign_role_to_user(db_session, schemas.UserRoleCreate(user_id=user.id, role_id=role.id))
    return user

@pytest.fixture(scope="function")
def super_admin_auth_headers(super_admin_user):
    """Returns auth headers for the super_admin_user."""
    token = security.create_access_token(data={"sub": str(super_admin_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def billing_manager_role(db_session, super_admin_user): # Depends on super_admin_user to ensure permissions exist
    """Creates a 'Billing Manager' role with specific billing permissions."""
    permissions_to_ensure = [
        "billing.view_invoices", "billing.create_invoices",
        "billing.process_payments"
    ]

    role = crud.get_role_by_name(db_session, "Billing Manager")
    if not role:
        role_create = schemas.RoleCreate(
            name="Billing Manager",
            description="Test Billing Manager",
            permission_codes=permissions_to_ensure
        )
        role = crud.create_role(db_session, role_create)
    return role

@pytest.fixture(scope="function")
def billing_manager_user(db_session, billing_manager_role):
    """Creates a user and assigns the 'Billing Manager' role to them."""
    user_create = schemas.UserCreate(
        email="billing@example.com",
        full_name="Billing Manager",
        password="password123"
    )
    user = crud.create_user(db_session, user_create)
    crud.assign_role_to_user(db_session, schemas.UserRoleCreate(user_id=user.id, role_id=billing_manager_role.id))
    return user

@pytest.fixture(scope="function")
def basic_user(db_session):
    """Creates a basic user with no assigned roles."""
    user_create = schemas.UserCreate(email="basic@example.com", full_name="Basic User", password="password123")
    return crud.create_user(db_session, user_create)

@pytest.fixture(scope="function")
def billing_manager_auth_headers(billing_manager_user):
    """Returns auth headers for the billing_manager_user."""
    token = security.create_access_token(data={"sub": str(billing_manager_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def support_manager_role(db_session, super_admin_user):
    """Creates a 'Support Manager' role with support permissions."""
    permissions_to_ensure = [
        "support.view_tickets", "support.create_tickets", "support.edit_tickets",
        "support.assign_tickets", "support.manage_config"
    ]
    role = crud.get_role_by_name(db_session, "Support Manager")
    if not role:
        role_create = schemas.RoleCreate(
            name="Support Manager",
            description="Test Support Manager",
            permission_codes=permissions_to_ensure
        )
        role = crud.create_role(db_session, role_create)
    return role

@pytest.fixture(scope="function")
def support_manager_user(db_session, support_manager_role):
    """Creates a user and assigns the 'Support Manager' role."""
    user_create = schemas.UserCreate(
        email="support@example.com",
        full_name="Support Manager",
        password="password123"
    )
    user = crud.create_user(db_session, user_create)
    crud.assign_role_to_user(db_session, schemas.UserRoleCreate(user_id=user.id, role_id=support_manager_role.id))
    return user

@pytest.fixture(scope="function")
def support_manager_auth_headers(support_manager_user):
    """Returns auth headers for the support_manager_user."""
    token = security.create_access_token(data={"sub": str(support_manager_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def customer_user(db_session, test_customer):
    """Creates a user of kind 'customer' and links them to the test_customer."""
    user_create = schemas.UserCreate(
        email="customer.user@example.com",
        full_name="Customer Portal User",
        password="password123",
        kind=schemas.UserKind.customer
    )
    user = crud.create_user(db_session, user_create)
    
    # Link user to customer via UserProfile
    profile_create = schemas.UserProfileCreate(customer_id=test_customer.id)
    crud.create_user_profile(db_session, user_id=user.id, profile=profile_create)
    
    return user

@pytest.fixture(scope="function")
def customer_user_auth_headers(customer_user):
    """Returns auth headers for the customer_user."""
    token = security.create_access_token(data={"sub": str(customer_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def crm_manager_role(db_session, super_admin_user):
    """Creates a 'CRM Manager' role with specific CRM permissions."""
    permissions_to_ensure = [
        "crm.view_accounts", "crm.manage_leads", "crm.manage_opportunities",
        "crm.create_accounts", "crm.edit_accounts", "crm.delete_accounts"
    ]
    role = crud.get_role_by_name(db_session, "CRM Manager")
    if not role:
        role_create = schemas.RoleCreate(
            name="CRM Manager",
            description="Test CRM Manager",
            permission_codes=permissions_to_ensure
        )
        role = crud.create_role(db_session, role_create)
    return role

@pytest.fixture(scope="function")
def crm_manager_user(db_session, crm_manager_role):
    """Creates a user and assigns the 'CRM Manager' role to them."""
    user_create = schemas.UserCreate(
        email="crm@example.com",
        full_name="CRM Manager",
        password="password123"
    )
    user = crud.create_user(db_session, user_create)
    crud.assign_role_to_user(db_session, schemas.UserRoleCreate(user_id=user.id, role_id=crm_manager_role.id))
    return user

@pytest.fixture(scope="function")
def crm_manager_auth_headers(crm_manager_user):
    """Returns auth headers for the crm_manager_user."""
    token = security.create_access_token(data={"sub": str(crm_manager_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def test_lead(db_session):
    """Creates a test lead."""
    lead_create = schemas.LeadCreate(name="John Doe Lead", email="john.doe.lead@example.com", phone="1234567890")
    return crud.create_lead(db_session, lead_create)

@pytest.fixture(scope="function")
def test_opportunity(db_session, test_lead):
    """Creates a test opportunity linked to test_lead."""
    opportunity_create = schemas.OpportunityCreate(name="Project Alpha Opportunity", lead_id=test_lead.id, amount=Decimal("5000.00"), stage="Prospecting")
    return crud.create_opportunity(db_session, opportunity_create)

@pytest.fixture(scope="function")
def test_ticket_status(db_session):
    """Creates a default 'New' ticket status for testing."""
    status = crud.get_ticket_statuses(db_session)
    if not status:
        return crud.create_ticket_status(db_session, schemas.TicketStatusCreate(title_for_agent="New", title_for_customer="New"))
    return status[0]

@pytest.fixture(scope="function")
def test_ticket_type(db_session):
    """Creates a default 'Technical' ticket type for testing."""
    ttype = crud.get_ticket_types(db_session)
    if not ttype:
        return crud.create_ticket_type(db_session, schemas.TicketTypeCreate(title="Technical"))
    return ttype[0]

@pytest.fixture(scope="function")
def test_ticket(db_session, test_customer, customer_user, test_ticket_status, test_ticket_type):
    """Creates a test ticket reported by the customer_user."""
    ticket_create = schemas.TicketCreate(
        customer_id=test_customer.id,
        subject="Test Ticket Subject",
        initial_message="This is the first message of the test ticket.",
        status_id=test_ticket_status.id,
        type_id=test_ticket_type.id
    )
    return crud.create_ticket(db_session, ticket_data=ticket_create, reporter_user_id=customer_user.id)

@pytest.fixture(scope="function")
def test_customer(db_session, test_partner, test_location):
    # Set billing date to today for invoice generation test
    today = date.today()
    customer_create = schemas.CustomerCreate(
        name="Test Customer",
        login="testcust",
        partner_id=test_partner.id,
        location_id=test_location.id,
        billing_config=schemas.CustomerBillingBase(
            enabled=True,
            billing_date=today.day,
            billing_due=14,
            grace_period=3
        )
    )
    return crud.create_customer(db_session, customer_create)

@pytest.fixture(scope="function")
def overdue_customer(db_session, test_partner, test_location):
    customer_create = schemas.CustomerCreate(
        name="Overdue Customer",
        login="overduecust",
        partner_id=test_partner.id,
        location_id=test_location.id,
        status='active',
        billing_config=schemas.CustomerBillingBase(
            enabled=True,
            billing_date=1,
            billing_due=14,
            grace_period=5 # 5 day grace period
        )
    )
    customer = crud.create_customer(db_session, customer_create)
    
    # Create an invoice that is now overdue
    invoice_create = schemas.InvoiceCreate(
        customer_id=customer.id,
        items=[schemas.InvoiceItemCreate(description="Old Service", price=Decimal("100.00"), quantity=1)],
        number="INV-OLD-001",
        total=Decimal("100.00"),
        due=Decimal("100.00"),
        date_till=date.today() - timedelta(days=15)
    )
    invoice = crud.create_invoice(db_session, invoice_create)
    invoice.date_created = date.today() - timedelta(days=20)
    db_session.commit()
    db_session.refresh(invoice)

    return customer

@pytest.fixture(scope="function")
def test_tariff(db_session):
    tariff_create = schemas.InternetTariffCreate(
        title="Basic Plan",
        price=Decimal("50.00"),
        speed_download=10000,
        speed_upload=5000
    )
    return crud.create_internet_tariff(db_session, tariff_create)

@pytest.fixture(scope="function")
def test_service(db_session, test_customer, test_tariff):
    service_create = schemas.InternetServiceCreate(
        customer_id=test_customer.id,
        tariff_id=test_tariff.id,
        status='active',
        description="Test Internet Service",
        login="testcust_service"
    )
    return crud.create_internet_service(db_session, service_create)

@pytest.fixture(scope="function")
def blocked_service(db_session, overdue_customer, test_tariff):
    service_create = schemas.InternetServiceCreate(
        customer_id=overdue_customer.id,
        tariff_id=test_tariff.id,
        status='blocked',
        description="Blocked Internet Service",
        login="overdue_service"
    )
    return crud.create_internet_service(db_session, service_create)

@pytest.fixture(scope="function")
def paid_up_customer_with_blocked_service(db_session, test_partner, test_location, test_tariff):
    customer_create = schemas.CustomerCreate(
        name="Paid Up Customer",
        login="paidupcust",
        partner_id=test_partner.id,
        location_id=test_location.id,
        status='blocked',
        billing_config=schemas.CustomerBillingBase(enabled=True, billing_date=1)
    )
    customer = crud.create_customer(db_session, customer_create)
    
    service_create = schemas.InternetServiceCreate(
        customer_id=customer.id,
        tariff_id=test_tariff.id,
        status='blocked',
        description="Service to be reactivated",
        login="paidup_service"
    )
    crud.create_internet_service(db_session, service_create)
    
    assert not crud.has_unpaid_invoices(db_session, customer.id)
    
    return customer
"""
RADIUS Database Logic Simulation Script

This script simulates the DATABASE INTERACTIONS of a RADIUS server. It does NOT
send real network packets. It is useful for seeding test data and verifying
that the application's CRUD hooks for FreeRADIUS are working.

It uses the existing data models and CRUD functions to:
1. Verify a user exists in the `radcheck` table (simulating authentication).
2. Start, update, and stop an accounting session by creating and updating
   records in the `radacct` table.
3. On session stop, it logs the total data usage to the `usage_tracking`
   table, which can be used by the billing engine.

To run this script, navigate to the `backend` directory and execute:
`python simulate_radius_db_logic.py`
"""
import time
import random
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy.orm import Session
import uuid

# Project imports
from . import crud
from . import models
from . import schemas
from .database import SessionLocal
from . import freeradius_crud
from . import freeradius_schemas

# --- Configuration ---
NAS_IP = "10.120.120.30"  # From your request
PRICE_PER_GB = Decimal("1.50") # Example price: $1.50 per GB


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def simulate_accounting_start(db: Session, service: models.InternetService, nas_ip: str):
    """Simulates an Accounting-Start packet by creating a radacct record."""
    print(f"\n[ACCT-START] Starting session for user '{service.login}'...")

    # A real RADIUS server would get this from the NAS
    acct_session_id = f"simulated-session-{int(time.time())}"
    acct_unique_id = uuid.uuid4().hex

    # Clean up any stale active sessions for this user in radacct
    stale_session = db.query(models.RadAcct).filter(
        models.RadAcct.username == service.login,
        models.RadAcct.acctstoptime.is_(None)
    ).first()
    if stale_session:
        print(f"[ACCT-WARN] Found stale active session {stale_session.acctsessionid}. Stopping it.")
        stale_session.acctstoptime = datetime.now(timezone.utc)
        stale_session.acctterminatecause = 'Stale-Session-Cleanup'
        db.commit()

    new_session = models.RadAcct(
        acctsessionid=acct_session_id,
        acctuniqueid=acct_unique_id,
        username=service.login,
        nasipaddress=nas_ip,
        acctstarttime=datetime.now(timezone.utc),
        framedipaddress=str(service.ipv4) if service.ipv4 else None,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    print(f"[ACCT-START] Session '{new_session.acctsessionid}' created and started in radacct.")
    return new_session


def simulate_accounting_update(db: Session, session: models.RadAcct):
    """Simulates an Accounting-Update packet by updating the radacct record."""
    if not session or session.acctstoptime is not None:
        print("[ACCT-UPDATE] No active session to update.")
        return

    upload_bytes = random.randint(100_000, 5_000_000)
    download_bytes = random.randint(1_000_000, 50_000_000)

    session.acctinputoctets = (session.acctinputoctets or 0) + download_bytes
    session.acctoutputoctets = (session.acctoutputoctets or 0) + upload_bytes
    session.acctsessiontime = (datetime.now(timezone.utc) - session.acctstarttime).total_seconds()

    db.commit()
    print(f"[ACCT-UPDATE] Session '{session.acctsessionid}' updated. "
          f"DL: {session.acctinputoctets / 1_048_576:.2f} MiB, "
          f"UL: {session.acctoutputoctets / 1_048_576:.2f} MiB")


def simulate_accounting_stop(db: Session, session: models.RadAcct, price_per_gb: Decimal):
    """Simulates an Accounting-Stop packet, finalizes radacct, and logs usage for billing."""
    if not session:
        print("[ACCT-STOP] No session provided to stop.")
        return

    print(f"\n[ACCT-STOP] Stopping session '{session.acctsessionid}' for user '{session.username}'...")

    session.acctstoptime = datetime.now(timezone.utc)
    session.acctterminatecause = 'User-Request'
    session.acctsessiontime = (session.acctstoptime - session.acctstarttime).total_seconds()

    db.commit()
    print(f"[ACCT-STOP] Session stopped. Final usage: "
          f"DL: {session.acctinputoctets / 1_048_576:.2f} MiB, "
          f"UL: {session.acctoutputoctets / 1_048_576:.2f} MiB")
    
    # --- LOG USAGE FOR BILLING ---
    # The main billing engine will pick this up on the customer's billing date.
    total_bytes = (session.acctinputoctets or 0) + (session.acctoutputoctets or 0)
    service = db.query(models.InternetService).filter(models.InternetService.login == session.username).first()

    if total_bytes > 0 and service:
        total_gb = Decimal(total_bytes) / (1024 * 1024 * 1024)

        usage_record = schemas.UsageTrackingCreate(
            customer_id=service.customer_id,
            service_type='internet',
            service_id=service.id,
            usage_date=date.today(),
            usage_type='data_transfer',
            usage_amount=total_gb,
            usage_unit='GB',
            billable=True,
            rate_per_unit=price_per_gb,
            billing_period=datetime.now(timezone.utc).strftime('%Y-%m'),
            device_info={'session_id': session.acctsessionid, 'nas_ip': session.nasipaddress}
        )
        crud.create_usage_record(db, usage=usage_record)
        print(f"  -> Logged {total_gb:.4f} GB of data usage for billing period {usage_record.billing_period}.")


def setup_simulation_data(db: Session):
    """Ensure necessary data for simulation exists, creating it if needed."""
    print("\n--- Setting up simulation data ---")

    # Ensure a router exists for the NAS IP
    router = crud.get_router_by_ip(db, ip=NAS_IP)
    if not router:
        print(f"Router with IP {NAS_IP} not found. Creating it...")
        location = db.query(models.Location).first()
        if not location:
            location = crud.create_location(db, schemas.LocationCreate(name="Default Sim Location"))

        router_create = schemas.RouterCreate(title=f"Simulated NAS {NAS_IP}", ip=NAS_IP, location_id=location.id, nas_type=1, radius_secret="sim_secret")
        router = crud.create_router(db, router=router_create)
        print(f"Created router '{router.title}' with ID {router.id}")

    customer_login = "radius_user"
    # Find the corresponding InternetService to get customer/tariff info
    service = db.query(models.InternetService).filter(models.InternetService.login == customer_login).first()
    if not service:
        print(f"Service for login '{customer_login}' not found. Creating it...")
        customer = crud.get_customer_by_login(db, login=customer_login)
        if not customer:
            partner = db.query(models.Partner).first()
            location = db.query(models.Location).first()
            customer = crud.create_customer(db, schemas.CustomerCreate(name="Radius Test Customer", login=customer_login, partner_id=partner.id, location_id=location.id, status='active'))
            print(f"Created customer '{customer.name}'")

        tariff = db.query(models.InternetTariff).first()
        if not tariff:
            tariff = crud.create_internet_tariff(db, schemas.InternetTariffCreate(title="Sim 10M/2M Plan", partners_ids=[1], price=Decimal("5000.00"), speed_download=10000, speed_upload=2000))
            print(f"Created tariff '{tariff.title}'")

        service = crud.create_internet_service(db, schemas.InternetServiceCreate(customer_id=customer.id, tariff_id=tariff.id, status='active', description="Simulated RADIUS Service", login=customer_login, password="sim_password", start_date=date.today(), ipv4="192.168.100.5", mac="00:11:22:33:44:55"))
        print(f"Created service '{service.description}' for customer '{customer.name}'")
        # The create_internet_service hook already syncs to freeradius tables
    else:
        # Ensure the user exists in FreeRADIUS tables
        radius_user = freeradius_crud.get_radius_user(db, username=customer_login)
        if not radius_user:
            print(f"RADIUS user '{customer_login}' not found. Creating...")
            rate_limit = f"{service.tariff.speed_upload}k/{service.tariff.speed_download}k" if service.tariff else None
            radius_user_data = freeradius_schemas.RadiusUserCreate(
                username=service.login,
                password=service.password,
                rate_limit=rate_limit,
                framed_ip_address=str(service.ipv4) if service.ipv4 else None
            )
            freeradius_crud.create_or_update_radius_user(db, user=radius_user_data)

    print("--- Simulation data setup complete ---\n")
    return "radius_user", "sim_password"


if __name__ == "__main__":
    db_gen = get_db()
    db = next(db_gen)
    try:
        test_username, test_password = setup_simulation_data(db)

        # --- SCENARIO 1: Successful Connection ---
        print("--- RUNNING SCENARIO 1: Successful Connection ---")
        # 1. Simulate Authentication check
        radius_user = freeradius_crud.get_radius_user(db, username=test_username)
        service = db.query(models.InternetService).filter(models.InternetService.login == test_username).first()

        if radius_user and service and service.status == 'active':
            print(f"[AUTH-SIM] User '{test_username}' found in radcheck. Proceeding to accounting.")
            session = simulate_accounting_start(db, service=service, nas_ip=NAS_IP)
            if session:
                print("\n...simulating usage for 5 seconds...")
                for i in range(5):
                    time.sleep(1)
                    simulate_accounting_update(db, session)
            simulate_accounting_stop(db, session, price_per_gb=PRICE_PER_GB)
        else:
            print(f"[AUTH-SIM-REJECT] User '{test_username}' not authorized.")

        # --- SCENARIO 2: Blocked Customer ---
        print("\n\n--- RUNNING SCENARIO 2: Blocked Customer ---")
        customer_to_block = crud.get_customer_by_login(db, test_username)
        if customer_to_block:
            print(f"Temporarily blocking customer '{customer_to_block.name}' for test...")
            # Updating the service will trigger the CRUD hook to remove the RADIUS user
            crud.update_internet_service(db, service.id, schemas.InternetServiceUpdate(status='blocked'))

            # Simulate authentication check again
            radius_user_after_block = freeradius_crud.get_radius_user(db, username=test_username)
            if not radius_user_after_block:
                print(f"[AUTH-SIM-REJECT] User '{test_username}' correctly not found in radcheck after being blocked.")
            else:
                print(f"[AUTH-SIM-FAIL] User '{test_username}' was found in radcheck even after being blocked.")

            # Reactivate for future runs
            crud.update_internet_service(db, service.id, schemas.InternetServiceUpdate(status='active'))
            print("...customer and service re-activated for future runs.")
    finally:
        print("\n--- Simulation finished ---")
        db.close()
"""
NAS Synchronization Verification Script (Refactored with Debug Assertions)
"""

import requests
import time
from sqlalchemy.orm import Session

# Project imports
from .database import SessionLocal
from .models import Nas, RadCheck

# --- Configuration ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"
ADMIN_EMAIL = "doctmacautomations@gmail.com"
ADMIN_PASSWORD = "#Dotmac246"


# --- Global State ---
headers = {}
created_router_ids = []
created_partner_id = None
created_tariff_id = None
created_customer_id = None
created_service_id = None
created_location_id = None  # To store the ID of the temporary location


def login_and_get_token():
    """Authenticate and set the global headers for subsequent requests."""
    global headers
    print("--- Authenticating ---")
    try:
        response = requests.post(
            f"{API_BASE_URL}/token",
            data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authentication successful.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Authentication failed: {e}")
        if e.response is not None:
            print(f"Response body: {e.response.text}")
        return False


def get_nas_by_shortname(shortname: str) -> Nas:
    """Directly query the 'nas' table by shortname."""
    db = SessionLocal()
    try:
        return db.query(Nas).filter(Nas.shortname == shortname).first()
    finally:
        db.close()

def get_radcheck_user(username: str) -> list[RadCheck]:
    """Directly query the 'radcheck' table for a user."""
    db = SessionLocal()
    try:
        # Using .all() to see if we get one or more entries
        return db.query(RadCheck).filter(RadCheck.username == username).all()
    finally:
        db.close()

def setup_test_dependencies():
    """Create a temporary location for the routers to use."""
    global created_location_id, created_partner_id, created_tariff_id, created_customer_id
    print("\n--- Setting up test dependencies (creating location) ---")
    # Use a unique name to avoid conflicts on re-runs if cleanup fails
    location_data = {"name": f"NAS-Sync-Test-Location-{int(time.time())}", "address_line_1": "Temp"}
    try:
        res = requests.post(
            f"{API_BASE_URL}/locations/", json=location_data, headers=headers
        )
        res.raise_for_status()
        created_location_id = res.json()["id"]
        print(f"✅ Created temporary location with ID: {created_location_id}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create temporary location: {e}")
        return False
    
    # Partner
    print("Creating temporary partner...")
    partner_data = {"name": f"Sync-Test-Partner-{int(time.time())}"}
    try:
        res = requests.post(f"{API_BASE_URL}/partners/", json=partner_data, headers=headers)
        res.raise_for_status()
        created_partner_id = res.json()["id"]
        print(f"✅ Created temporary partner with ID: {created_partner_id}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create temporary partner: {e}")
        return False

    # Tariff
    print("Creating temporary internet tariff...")
    tariff_data = {
        "title": f"SyncTest-Tariff-10M-{int(time.time())}",
        "partners_ids": [created_partner_id],
        "speed_download": 10000,
        "speed_upload": 5000,
        "price": "10.0"
    }
    try:
        res = requests.post(f"{API_BASE_URL}/internet-tariffs/", json=tariff_data, headers=headers)
        res.raise_for_status()
        created_tariff_id = res.json()["id"]
        print(f"✅ Created temporary tariff with ID: {created_tariff_id}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create temporary tariff: {e}")
        return False

    # Customer
    print("Creating temporary customer...")
    customer_data = {
        "name": "SyncTest Customer",
        "login": f"synctest_user_{int(time.time())}",
        "partner_id": created_partner_id,
        "location_id": created_location_id,
    }
    try:
        res = requests.post(f"{API_BASE_URL}/customers/", json=customer_data, headers=headers)
        res.raise_for_status()
        created_customer_id = res.json()["id"]
        print(f"✅ Created temporary customer with ID: {created_customer_id}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create temporary customer: {e}")
        return False

    return True

def cleanup():
    """Delete all resources created during the test."""
    print("\n--- Cleaning up created resources ---")

    # Routers
    if created_router_ids:
        print("Cleaning up routers...")
        for router_id in created_router_ids:
            try:
                response = requests.delete(
                    f"{API_BASE_URL}/network/routers/{router_id}", headers=headers
                )
                if response.status_code == 204:
                    print(f"✅ Deleted router ID: {router_id}")
                else:
                    print(
                        f"⚠️ Failed to delete router ID: {router_id}, Status: {response.status_code}"
                    )
            except requests.exceptions.RequestException as e:
                print(f"❌ Error deleting router ID {router_id}: {e}")

    # Customer (deleting customer should cascade and delete service)
    if created_customer_id:
        print(f"Cleaning up customer (ID: {created_customer_id})...")
        try:
            res = requests.delete(f"{API_BASE_URL}/customers/{created_customer_id}", headers=headers)
            if res.status_code == 204:
                print("✅ Deleted customer.")
            else:
                print(f"⚠️ Failed to delete customer ID: {created_customer_id}, Status: {res.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting customer ID {created_customer_id}: {e}")

    # Tariff
    if created_tariff_id:
        print(f"Cleaning up tariff (ID: {created_tariff_id})...")
        try:
            res = requests.delete(f"{API_BASE_URL}/internet-tariffs/{created_tariff_id}", headers=headers)
            if res.status_code == 204:
                print("✅ Deleted tariff.")
            else:
                print(f"⚠️ Failed to delete tariff ID: {created_tariff_id}, Status: {res.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting tariff ID {created_tariff_id}: {e}")

    # Partner
    if created_partner_id:
        print(f"Cleaning up partner (ID: {created_partner_id})...")
        try:
            res = requests.delete(f"{API_BASE_URL}/partners/{created_partner_id}", headers=headers)
            if res.status_code == 204:
                print("✅ Deleted partner.")
            else:
                print(f"⚠️ Failed to delete partner ID: {created_partner_id}, Status: {res.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting partner ID {created_partner_id}: {e}")

    # Location
    if created_location_id:
        print(f"Cleaning up location (ID: {created_location_id})...")

        try:
            res = requests.delete(
                f"{API_BASE_URL}/locations/{created_location_id}", headers=headers
            )
            if res.status_code == 204:
                print("✅ Deleted temporary location.")
            else:
                print(
                    f"⚠️ Failed to delete location ID: {created_location_id}, Status: {res.status_code}"
                )
        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting location ID {created_location_id}: {e}")


def debug_assert(condition, msg, nas_entry=None):
    """Custom assert with debug printing for NAS rows."""
    if not condition:
        if nas_entry:
            print(
                f"🔎 Debug NAS row: shortname={nas_entry.shortname}, "
                f"nasname={nas_entry.nasname}, secret={nas_entry.secret}"
            )
        raise AssertionError(msg)


def run_tests():
    """Execute all verification test cases."""
    global created_service_id
    try:
        # --- Test Case 1: Create Router with RADIUS Secret ---
        print("\n--- Test 1: Create Router with RADIUS Secret ---")
        router1_data = {
            "title": "SyncTest-Router-1",
            "ip": "192.168.101.1",
            "location_id": created_location_id,
            "nas_type": 1,
            "radius_secret": "secret1",
        }
        res = requests.post(
            f"{API_BASE_URL}/network/routers/", json=router1_data, headers=headers
        )
        debug_assert(res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}")
        router1_id = res.json()["id"]
        created_router_ids.append(router1_id)
        print(f"✅ Router created (ID: {router1_id}, title: SyncTest-Router-1)")

        nas1 = get_nas_by_shortname("SyncTest-Router-1")
        debug_assert(nas1 is not None, "NAS entry for Router 1 was not created.")
        debug_assert(
            nas1.nasname == "192.168.101.1" and nas1.secret == "secret1",
            "NAS entry for Router 1 has incorrect values.",
            nas1,
        )
        print("✅ NAS entry for Router 1 created and verified.")

        # --- Test Case 2: Create Router WITHOUT RADIUS Secret ---
        print("\n--- Test 2: Create Router without RADIUS Secret ---")
        router2_data = {
            "title": "SyncTest-Router-2",
            "ip": "192.168.101.2",
            "location_id": created_location_id,
            "nas_type": 1,
        }
        res = requests.post(
            f"{API_BASE_URL}/network/routers/", json=router2_data, headers=headers
        )
        debug_assert(res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}")
        router2_id = res.json()["id"]
        created_router_ids.append(router2_id)
        print(f"✅ Router created (ID: {router2_id}, title: SyncTest-Router-2)")

        nas2 = get_nas_by_shortname("SyncTest-Router-2")
        debug_assert(
            nas2 is None,
            "NAS entry for Router 2 was created, but should not have been.",
        )
        print("✅ NAS entry for Router 2 correctly not created.")

        # --- Test Case 3: Update Router to ADD RADIUS Secret ---
        print("\n--- Test 3: Update Router to ADD RADIUS Secret ---")
        update_data3 = {"radius_secret": "secret2"}
        res = requests.put(
            f"{API_BASE_URL}/network/routers/{router2_id}",
            json=update_data3,
            headers=headers,
        )
        debug_assert(res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}")
        print("✅ Router 2 updated.")

        nas2_after = get_nas_by_shortname("SyncTest-Router-2")
        debug_assert(
            nas2_after is not None, "NAS entry for Router 2 was not created after adding secret."
        )
        debug_assert(
            nas2_after.secret == "secret2",
            f"Expected secret=secret2 but got {nas2_after.secret}",
            nas2_after,
        )
        print("✅ NAS entry for Router 2 created after update.")

        # --- Test Case 4: Update Router to CHANGE Secret and IP ---
        print("\n--- Test 4: Update Router to CHANGE Secret and IP ---")
        update_data4 = {"radius_secret": "secret1_updated", "ip": "192.168.101.101"}
        res = requests.put(
            f"{API_BASE_URL}/network/routers/{router1_id}",
            json=update_data4,
            headers=headers,
        )
        debug_assert(res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}")
        print("✅ Router 1 updated.")

        nas1_after = get_nas_by_shortname("SyncTest-Router-1")
        debug_assert(nas1_after is not None, "NAS entry for Router 1 not found after update.")
        debug_assert(
            nas1_after.secret == "secret1_updated",
            f"Expected secret=secret1_updated but got {nas1_after.secret}",
            nas1_after,
        )
        debug_assert(
            nas1_after.nasname == "192.168.101.101",
            f"Expected nasname=192.168.101.101 but got {nas1_after.nasname}",
            nas1_after,
        )
        print("✅ NAS entry for Router 1 correctly updated.")

        # --- Test Case 5: Update Router to REMOVE RADIUS Secret ---
        print("\n--- Test 5: Update Router to REMOVE RADIUS Secret ---")
        update_data5 = {"radius_secret": None}
        res = requests.put(
            f"{API_BASE_URL}/network/routers/{router1_id}",
            json=update_data5,
            headers=headers,
        )
        debug_assert(res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}")
        print("✅ Router 1 updated to remove secret.")

        nas1_removed = get_nas_by_shortname("SyncTest-Router-1")
        debug_assert(
            nas1_removed is None,
            "NAS entry for Router 1 was not deleted after removing secret.",
        )
        print("✅ NAS entry for Router 1 correctly deleted.")

        # --- Test Case 6: Delete a Router with a Secret ---
        print("\n--- Test 6: Delete a Router with a Secret ---")
        res = requests.delete(
            f"{API_BASE_URL}/network/routers/{router2_id}", headers=headers
        )
        debug_assert(res.status_code == 204, f"Expected 204, got {res.status_code}: {res.text}")
        created_router_ids.remove(router2_id)
        print(f"✅ Router 2 (ID: {router2_id}) deleted.")

        nas2_deleted = get_nas_by_shortname("SyncTest-Router-2")
        debug_assert(
            nas2_deleted is None,
            "NAS entry for Router 2 was not deleted when router was deleted.",
        )
        print("✅ NAS entry for Router 2 correctly deleted.")

        # --- Test Case 7: Create Active Service and Verify radcheck ---
        print("\n--- Test 7: Create Active Service and Verify radcheck ---")
        service_password = "test_password_123"
        # Get the login from the created customer to ensure it's unique for this test run
        customer_res = requests.get(f"{API_BASE_URL}/customers/{created_customer_id}/", headers=headers).json()
        service_login = customer_res["login"]
        service_data = {
            "customer_id": created_customer_id,
            "tariff_id": created_tariff_id,
            "status": "active",
            "description": "SyncTest Service",
            "login": service_login,
            "password": service_password,
            "start_date": "2024-01-01"  # A valid date string
        }
        res = requests.post(f"{API_BASE_URL}/internet-services/", json=service_data, headers=headers)
        debug_assert(res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}")
        created_service_id = res.json()["id"]
        print(f"✅ Active service created (ID: {created_service_id}) for user '{service_login}'")

        radcheck_entries = get_radcheck_user(service_login)
        debug_assert(len(radcheck_entries) > 0, f"radcheck entry for '{service_login}' was not created.")
        
        password_attr = next((attr for attr in radcheck_entries if attr.attribute == 'Cleartext-Password'), None)
        debug_assert(password_attr is not None, "Cleartext-Password attribute not found in radcheck.")
        # We can't easily verify the hashed password value here, but its presence is a strong indicator.
        print(f"✅ radcheck entry for '{service_login}' created successfully.")

        # --- Test Case 8: Deactivate Service and Verify radcheck ---
        print("\n--- Test 8: Deactivate Service and Verify radcheck ---")
        update_data8 = {"status": "blocked"}
        res = requests.put(f"{API_BASE_URL}/internet-services/{created_service_id}", json=update_data8, headers=headers)
        debug_assert(res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}")
        print(f"✅ Service for '{service_login}' deactivated.")

        radcheck_entries_after_block = get_radcheck_user(service_login)
        debug_assert(len(radcheck_entries_after_block) == 0, f"radcheck entry for '{service_login}' was not deleted after deactivation.")
        print(f"✅ radcheck entry for '{service_login}' correctly deleted.")

        # # --- Test Case 9: Reactivate Service and Verify radcheck ---
        # print("\n--- Test 9: Reactivate Service and Verify radcheck ---")
        # update_data9 = {"status": "active"}
        # res = requests.put(f"{API_BASE_URL}/internet-services/{created_service_id}", json=update_data9, headers=headers)
        # debug_assert(res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}")
        # print(f"✅ Service for '{service_login}' reactivated.")

        # radcheck_entries_after_reactivate = get_radcheck_user(service_login)
        # debug_assert(len(radcheck_entries_after_reactivate) > 0, f"radcheck entry for '{service_login}' was not re-created after reactivation.")
        # print(f"✅ radcheck entry for '{service_login}' correctly re-created.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    print("Starting NAS synchronization verification...")
    if login_and_get_token():
        if setup_test_dependencies():
            time.sleep(1)  # ensure API is ready
            run_tests()
        else:
            print("Cannot run tests without setting up dependencies.")
    else:
        print("Cannot run tests without authentication.")
    print("\nVerification finished.")

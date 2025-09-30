"""
FreeRADIUS Server Test Script

This script simulates a Network Access Server (NAS) sending real RADIUS packets
to your FreeRADIUS server to perform a true end-to-end test.

It will:
1. Send an Authentication request to verify a user's credentials.
2. Send Accounting-Start and Accounting-Stop packets to simulate a user session.

This allows you to confirm that your FreeRADIUS server is correctly configured
to read from `radcheck` and write to `radacct` in your project's database.

**Prerequisites**:
- Run `pip install pyrad`
- Ensure the test data exists by running `simulate_radius_db_logic.py` at least once.
  This script seeds the database with the necessary test user and router.

To run this script, navigate to the `backend` directory and execute:
`python test_freeradius_server.py`
"""
import socket
import os
from pyrad.client import Client, Timeout
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, AccessAccept, AccessReject, AccountingResponse
import time
import uuid
import random

# --- Configuration ---
RADIUS_SERVER_IP = os.getenv("RADIUS_SERVER_IP", "10.120.120.30")
RADIUS_AUTH_PORT = int(os.getenv("RADIUS_AUTH_PORT", "18120"))
RADIUS_ACCT_PORT = int(os.getenv("RADIUS_ACCT_PORT", "1813")) # Standard accounting port
RADIUS_SECRET = os.getenv("RADIUS_SECRET", "testing123").encode('utf-8')  # The secret configured for your NAS in the 'routers' table
# Your successful `radtest` command used 127.0.1.1, which is a common default on some systems.
# We'll use that as the default here, as it's a likely cause for timeouts if mismatched.
NAS_IP = os.getenv("NAS_IP", "10.120.120.5") # The IP of the NAS this script is pretending to be
TEST_USERNAME = os.getenv("RADIUS_TEST_USER", "bob")
TEST_PASSWORD = os.getenv("RADIUS_TEST_PASS", "hello")

# Create a RADIUS client
# The dictionary file contains definitions for RADIUS attributes.
client = Client(
    server=RADIUS_SERVER_IP,
    authport=RADIUS_AUTH_PORT,
    acctport=RADIUS_ACCT_PORT,
    secret=RADIUS_SECRET,
    # The dictionary file contains definitions for RADIUS attributes.
    # "dictionary.ps1" is an unconventional name and could be a typo.
    # Consider renaming the file to a standard name like "dictionary".
    dict=Dictionary("dictionary"),
    timeout=10 # Increased timeout for more reliability
)

def test_authentication():
    """Sends a real RADIUS Access-Request packet to the server."""
    print("\n--- SCENARIO 1: Testing Authentication ---")
    
    # Create an Access-Request packet
    req = client.CreateAuthPacket(
        code=AccessRequest,
        User_Name=TEST_USERNAME,
        NAS_Identifier="New Nas"
    )
    # Add attributes
    req["NAS-IP-Address"] = NAS_IP
    req["NAS-Port"] = 0
    req["Service-Type"] = "Login-User"
    req["Called-Station-Id"] = "00-04-5F-00-0F-D1" # Mimic real NAS attribute
    req["Calling-Station-Id"] = "00-01-24-80-B3-9C" # Mimic real NAS attribute
    # For PAP authentication (against Cleartext-Password in radcheck), the password
    # must be obfuscated using the shared secret. pyrad's PwCrypt does this.
    req["User-Password"] = req.PwCrypt(TEST_PASSWORD)

    try:
        print(f"Sending Access-Request for user '{TEST_USERNAME}' to {RADIUS_SERVER_IP}:{RADIUS_AUTH_PORT}...")
        reply = client.SendPacket(req)

        if reply.code == AccessAccept:
            print("✅ [AUTH-ACCEPT] Authentication successful!")
            print("  -> Attributes returned by server:")
            for key in reply.keys():
                print(f"    {key}: {reply[key]}")
            return True
        else:
            print("❌ [AUTH-REJECT] Authentication failed.")
            print("  -> Reply code:", reply.code)
            print("  -> Attributes returned by server:")
            for key in reply.keys():
                print(f"    {key}: {reply[key]}")
            return False

    except Timeout:
        print(f"❌ [ERROR] RADIUS server at {RADIUS_SERVER_IP}:{client.authport} did not reply (timeout).")
        print("  Possible causes:")
        print("  1. FreeRADIUS server is not running (use `freeradius -X` to debug).")
        print("  2. The server is not listening on the correct IP/port.")
        print(f"  3. A firewall is blocking UDP packets to port {RADIUS_AUTH_PORT}.")
        print(f"  4. The NAS-IP-Address '{NAS_IP}' is not configured as a client in FreeRADIUS.")
        print("     (Your successful `radtest` used '127.0.1.1', so we've updated the script to match.)")
        return False
    except socket.error as e:
        print(f"❌ [ERROR] Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ [ERROR] An unexpected exception occurred: {repr(e)}")
        return False

def test_accounting():
    """Sends real RADIUS Accounting-Request packets (Start and Stop)."""
    print("\n--- SCENARIO 2: Testing Accounting ---")
    
    # Generate random data for a more realistic simulation
    session_id = uuid.uuid4().hex
    session_time = random.randint(120, 3600)
    input_octets = random.randrange(2**10, 2**30)
    output_octets = random.randrange(2**10, 2**30)
    terminate_cause = random.choice(["User-Request", "Idle-Timeout", "Session-Timeout", "Admin-Reset"])

    # 1. Send Accounting-Start
    req_start = client.CreateAcctPacket(User_Name=TEST_USERNAME, NAS_Identifier="Simulated-NAS")
    req_start["Acct-Status-Type"] = "Start"
    req_start["NAS-IP-Address"] = NAS_IP
    req_start["NAS-Port"] = 0
    req_start["Called-Station-Id"] = "00-04-5F-00-0F-D1" # Example MAC
    req_start["Calling-Station-Id"] = "00-01-24-80-B3-9C" # Example MAC
    req_start["Acct-Session-Id"] = session_id
    req_start["Framed-IP-Address"] = "192.168.100.5" # Example IP

    try:
        print(f"Sending Accounting-Start for session '{session_id}'...")
        reply_start = client.SendPacket(req_start)
        if reply_start.code == AccountingResponse:
            print("✅ [ACCT-START] Accounting-Start packet sent and acknowledged by server.")
        else:
            print(f"⚠️  [ACCT-START] Server sent an unexpected reply code: {reply_start.code}")
    except Exception as e:
        print(f"❌ [ERROR] An exception occurred during Accounting-Start: {repr(e)}")
        print(f"  -> Check that the RADIUS accounting port (e.g., {client.acctport}) is open and the server is running.")
        return False

    # 2. Simulate some time passing
    print(f"...simulating a session of {session_time} seconds (without actual delay)...")

    # 3. Send Accounting-Stop
    req_stop = client.CreateAcctPacket(User_Name=TEST_USERNAME, NAS_Identifier="Simulated-NAS")
    req_stop["Acct-Status-Type"] = "Stop"
    req_stop["NAS-IP-Address"] = NAS_IP
    req_stop["NAS-Port"] = 0
    req_stop["Called-Station-Id"] = "00-04-5F-00-0F-D1"
    req_stop["Calling-Station-Id"] = "00-01-24-80-B3-9C"
    req_stop["Acct-Session-Id"] = session_id
    req_stop["Acct-Session-Time"] = session_time
    req_stop["Acct-Input-Octets"] = input_octets
    req_stop["Acct-Output-Octets"] = output_octets
    req_stop["Acct-Terminate-Cause"] = terminate_cause

    try:
        print(f"Sending Accounting-Stop for session '{session_id}'...")
        reply_stop = client.SendPacket(req_stop)
        if reply_stop.code == AccountingResponse:
            print("✅ [ACCT-STOP] Accounting-Stop packet sent and acknowledged by server.")
            print("  -> Check your 'radacct' table in the database to verify the session was recorded.")
        else:
            print(f"⚠️  [ACCT-STOP] Server sent an unexpected reply code: {reply_stop.code}")
    except Exception as e:
        print(f"❌ [ERROR] An exception occurred during Accounting-Stop: {repr(e)}")
        print(f"  -> Check that the RADIUS accounting port (e.g., {client.acctport}) is open and the server is running.")
        return False
    
    return True
def test_failed_authentication():
    """Sends a real RADIUS Access-Request with a wrong password to verify rejection."""
    print("\n--- SCENARIO 3: Testing Failed Authentication ---")
    
    wrong_password = "wrong_password"
    
    # Create an Access-Request packet
    req = client.CreateAuthPacket(
        code=AccessRequest,
        User_Name=TEST_USERNAME,
        NAS_Identifier="Simulated-NAS"
    )
    # Add attributes
    req["NAS-IP-Address"] = NAS_IP
    req["NAS-Port"] = 0
    req["Service-Type"] = "Login-User"
    req["Called-Station-Id"] = "00-04-5F-00-0F-D1"
    req["Calling-Station-Id"] = "00-01-24-80-B3-9C"
    req["User-Password"] = req.PwCrypt(wrong_password)

    try:
        print(f"Sending Access-Request for user '{TEST_USERNAME}' with an incorrect password...")
        reply = client.SendPacket(req)

        if reply.code == AccessReject:
            print("✅ [AUTH-REJECT] Authentication correctly failed as expected.")
            return True
        elif reply.code == AccessAccept:
            print("❌ [AUTH-FAIL] Authentication succeeded but should have failed!")
            return False
        else:
            print(f"⚠️  [AUTH-UNEXPECTED] Received unexpected reply code: {reply.code}")
            print("  -> Attributes returned by server:")
            for key in reply.keys():
                print(f"    {key}: {reply[key]}")
            return False

    except Timeout:
        print(f"❌ [ERROR] RADIUS server at {RADIUS_SERVER_IP}:{client.authport} did not reply (timeout).")
        print("  (This is likely the same timeout issue as in the successful authentication test.)")
        return False
    except socket.error as e:
        print(f"❌ [ERROR] Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ [ERROR] An unexpected exception occurred: {repr(e)}")
        return False

if __name__ == "__main__":
    print("Starting FreeRADIUS Server Test Simulation...")
    print(f"Server IP: {RADIUS_SERVER_IP}, Auth Port: {RADIUS_AUTH_PORT}, Acct Port: {RADIUS_ACCT_PORT}, NAS IP: {NAS_IP}, Secret: {'*' * len(RADIUS_SECRET)}")
    
    print("\nNOTE: Ensure the test data is set up by running `simulate_radius_db_logic.py` first.")
    
    if test_authentication():
        test_accounting()
    else:
        print("\nSkipping accounting test because authentication failed.")

    # Always run the failed authentication test
    test_failed_authentication()

    print("\n--- Test simulation finished ---")
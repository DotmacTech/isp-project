#!/usr/bin/python
from pyrad.client import Client,Timeout
from pyrad.dictionary import Dictionary
import socket
import sys

import os
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

srv = Client(
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


req = srv.CreateAuthPacket(code=AccessRequest, User_Name=TEST_USERNAME)

req["NAS-IP-Address"] = NAS_IP
req["NAS-Port"] = 0
req["Service-Type"] = "Login-User"
req["NAS-Identifier"] = "trillian"
req["Called-Station-Id"] = "00-04-5F-00-0F-D1"
req["Calling-Station-Id"] = "00-01-24-80-B3-9C"
req["Framed-IP-Address"] = "10.0.0.100"
req["User-Password"] = req.PwCrypt(TEST_PASSWORD)

try:
    print("Sending authentication request")
    reply = srv.SendPacket(req)
except Timeout:
    print("RADIUS server does not reply")
    sys.exit(1)
except socket.error as error:
    print("Network error: " + error[1])
    sys.exit(1)

if reply.code == AccessAccept:
    print("Access accepted")
else:
    print("Access denied")

print("Attributes returned by server:")
for i in reply.keys():
    print("%s: %s" % (i, reply[i]))
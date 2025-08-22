import pytest
from fastapi import status
from decimal import Decimal

import crud
import schemas
from models import Customer, Lead, Opportunity

# --- Lead Endpoint Tests ---

def test_create_lead(test_client, crm_manager_auth_headers):
    """Test creating a new lead with proper permissions."""
    lead_data = {
        "name": "Jane Smith Lead",
        "email": "jane.smith@example.com",
        "phone": "0987654321"
    }
    response = test_client.post("/api/v1/crm/leads/", json=lead_data, headers=crm_manager_auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Jane Smith Lead"
    assert data["email"] == "jane.smith@example.com"

def test_create_lead_permission_denied(test_client, billing_manager_auth_headers):
    """Test that a user without crm.manage_leads permission cannot create a lead."""
    lead_data = {"name": "Forbidden Lead"}
    response = test_client.post("/api/v1/crm/leads/", json=lead_data, headers=billing_manager_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_read_leads(test_client, crm_manager_auth_headers, test_lead):
    """Test reading a list of leads."""
    response = test_client.get("/api/v1/crm/leads/", headers=crm_manager_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert any(lead["id"] == test_lead.id for lead in data["items"])

def test_update_lead(test_client, crm_manager_auth_headers, test_lead):
    """Test updating an existing lead."""
    update_data = {"status": "Contacted"}
    response = test_client.put(f"/api/v1/crm/leads/{test_lead.id}", json=update_data, headers=crm_manager_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "Contacted"

# --- Opportunity Endpoint Tests ---

def test_create_opportunity(test_client, crm_manager_auth_headers, test_lead):
    """Test creating a new opportunity."""
    opportunity_data = {
        "name": "Project Gamma",
        "lead_id": test_lead.id,
        "amount": "10000.00",
        "stage": "Qualification"
    }
    response = test_client.post("/api/v1/crm/opportunities/", json=opportunity_data, headers=crm_manager_auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Project Gamma"
    assert Decimal(data["amount"]) == Decimal("10000.00")

def test_read_opportunities(test_client, crm_manager_auth_headers, test_opportunity):
    """Test reading a list of opportunities."""
    response = test_client.get("/api/v1/crm/opportunities/", headers=crm_manager_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert any(opp["id"] == test_opportunity.id for opp in data["items"])

# --- Conversion Logic Test ---

def test_convert_opportunity_to_customer(test_client, crm_manager_auth_headers, db_session, test_opportunity, test_partner, test_location):
    """Test the full business logic of converting an opportunity to a customer."""
    # First, update the opportunity to a "winnable" stage
    winnable_update = {"stage": "Closed Won"}
    test_client.put(f"/api/v1/crm/opportunities/{test_opportunity.id}", json=winnable_update, headers=crm_manager_auth_headers)

    # Now, perform the conversion
    conversion_data = {
        "login": "new_customer_login",
        "partner_id": test_partner.id,
        "location_id": test_location.id
    }
    response = test_client.post(f"/api/v1/crm/opportunities/{test_opportunity.id}/convert", json=conversion_data, headers=crm_manager_auth_headers)

    # 1. Assert the API call was successful and returned a customer
    assert response.status_code == status.HTTP_201_CREATED, response.text
    customer_data = response.json()
    assert customer_data["name"] == test_opportunity.lead.name # Name should come from the lead
    assert customer_data["login"] == "new_customer_login"

    # 2. Verify the database state after conversion by re-fetching from the DB
    db_session.commit() # Ensure the test session sees the committed data from the API call

    # 2a. Check the new customer
    new_customer = db_session.query(Customer).filter(Customer.id == customer_data["id"]).one()
    assert new_customer is not None
    assert new_customer.name == test_opportunity.lead.name
    assert new_customer.email == test_opportunity.lead.email

    # 2b. Check the original lead
    updated_lead = db_session.query(Lead).filter(Lead.id == test_opportunity.lead_id).one()
    assert updated_lead.status == "Converted"

    # 2c. Check the opportunity
    updated_opportunity = db_session.query(Opportunity).filter(Opportunity.id == test_opportunity.id).one()
    assert updated_opportunity.stage == "Closed Won"
    assert updated_opportunity.customer_id == new_customer.id

def test_convert_opportunity_permission_denied(test_client, billing_manager_auth_headers, test_opportunity):
    """Test that a user without crm.create_accounts cannot convert an opportunity."""
    conversion_data = {"login": "forbidden_login", "partner_id": 1, "location_id": 1}
    response = test_client.post(f"/api/v1/crm/opportunities/{test_opportunity.id}/convert", json=conversion_data, headers=billing_manager_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
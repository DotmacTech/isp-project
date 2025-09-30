import pytest
from fastapi import status

import crud
import schemas
from models import Ticket

# --- Ticket Creation and Permission Tests ---

def test_create_ticket_as_support_manager(test_client, support_manager_auth_headers, test_customer, test_ticket_status, test_ticket_type):
    """
    Tests that a user with 'support.create_tickets' permission can create a ticket.
    """
    ticket_data = {
        "customer_id": test_customer.id,
        "subject": "Ticket created by support manager",
        "initial_message": "This is a test message from the support manager.",
        "status_id": test_ticket_status.id,
        "type_id": test_ticket_type.id,
        "priority": "high"
    }
    response = test_client.post("/api/v1/support/tickets/", json=ticket_data, headers=support_manager_auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["subject"] == "Ticket created by support manager"
    assert data["priority"] == "high"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["message"] == "This is a test message from the support manager."

def test_create_ticket_permission_denied(test_client, crm_manager_auth_headers, test_customer, test_ticket_status, test_ticket_type):
    """
    Tests that a user without 'support.create_tickets' permission is denied.
    """
    ticket_data = {
        "customer_id": test_customer.id,
        "subject": "Forbidden Ticket",
        "initial_message": "This should not be created.",
        "status_id": test_ticket_status.id,
        "type_id": test_ticket_type.id
    }
    response = test_client.post("/api/v1/support/tickets/", json=ticket_data, headers=crm_manager_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_manage_config_permission_denied(test_client, crm_manager_auth_headers):
    """
    Tests that a user without 'support.manage_config' permission is denied access to config endpoints.
    """
    response = test_client.get("/api/v1/support/config/statuses/", headers=crm_manager_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = test_client.get("/api/v1/support/config/types/", headers=crm_manager_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = test_client.get("/api/v1/support/config/groups/", headers=crm_manager_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

# --- Ticket Access and Scoping Tests ---

def test_support_manager_can_list_all_tickets(test_client, support_manager_auth_headers, test_ticket):
    """
    Tests that a support manager can see all tickets, including the one created by the customer.
    """
    response = test_client.get("/api/v1/support/tickets/", headers=support_manager_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 1
    assert any(ticket["id"] == test_ticket.id for ticket in data["items"])

def test_customer_user_can_only_view_own_ticket(test_client, customer_user_auth_headers, test_ticket):
    """
    Tests that a customer user can view their own ticket details.
    """
    response = test_client.get(f"/api/v1/support/tickets/{test_ticket.id}", headers=customer_user_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == test_ticket.id

def test_customer_user_cannot_view_other_tickets(test_client, customer_user_auth_headers, db_session, test_partner, test_location, support_manager_user, test_ticket_status, test_ticket_type):
    """
    Tests that a customer user receives a 404 when trying to access a ticket that is not theirs.
    """
    # Create another customer and a ticket for them
    other_customer = crud.create_customer(db_session, schemas.CustomerCreate(name="Other Customer", login="othercust", partner_id=test_partner.id, location_id=test_location.id))
    other_ticket_data = schemas.TicketCreate(customer_id=other_customer.id, subject="Other Ticket", initial_message="...", status_id=test_ticket_status.id, type_id=test_ticket_type.id)
    other_ticket = crud.create_ticket(db_session, ticket_data=other_ticket_data, reporter_user_id=support_manager_user.id)
    
    # The customer_user should not be able to see this other ticket
    response = test_client.get(f"/api/v1/support/tickets/{other_ticket.id}", headers=customer_user_auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

# --- Ticket Update and Message Tests ---

def test_update_ticket(test_client, support_manager_auth_headers, test_ticket, db_session):
    """
    Tests updating a ticket's status and priority.
    """
    new_status = crud.create_ticket_status(db_session, schemas.TicketStatusCreate(title_for_agent="In Progress", title_for_customer="In Progress"))
    update_data = {
        "priority": "urgent",
        "status_id": new_status.id
    }
    response = test_client.put(f"/api/v1/support/tickets/{test_ticket.id}", json=update_data, headers=support_manager_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["priority"] == "urgent"
    assert data["status"]["id"] == new_status.id

def test_add_message_to_ticket(test_client, support_manager_auth_headers, test_ticket, db_session):
    """
    Tests adding a new message to an existing ticket.
    """
    message_data = {
        "message": "This is a follow-up message from support.",
        "is_internal_note": False
    }
    response = test_client.post(f"/api/v1/support/tickets/{test_ticket.id}/messages", json=message_data, headers=support_manager_auth_headers)
    assert response.status_code == status.HTTP_201_CREATED
    
    # Verify the message was added
    ticket = db_session.query(Ticket).filter(Ticket.id == test_ticket.id).one()
    assert len(ticket.messages) == 2
    assert ticket.messages[-1].message == "This is a follow-up message from support."

# --- Ticket Configuration Management Tests ---

def test_manage_ticket_statuses(test_client, support_manager_auth_headers):
    """
    Tests the full CRUD lifecycle for a ticket status.
    """
    headers = support_manager_auth_headers
    
    # 1. Create
    create_data = {"title_for_agent": "Awaiting Customer", "title_for_customer": "Awaiting Your Reply"}
    response = test_client.post("/api/v1/support/config/statuses/", json=create_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    new_status_id = response.json()["id"]
    
    # 2. Read
    response = test_client.get("/api/v1/support/config/statuses/", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert any(s["id"] == new_status_id for s in response.json())
    
    # 3. Update
    update_data = {"label": "info"}
    response = test_client.put(f"/api/v1/support/config/statuses/{new_status_id}", json=update_data, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["label"] == "info"
    
    # 4. Delete
    response = test_client.delete(f"/api/v1/support/config/statuses/{new_status_id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_delete_ticket_status_in_use(test_client, support_manager_auth_headers, test_ticket):
    """
    Tests that a ticket status cannot be deleted if it is currently in use by a ticket.
    """
    status_in_use_id = test_ticket.status_id
    response = test_client.delete(f"/api/v1/support/config/statuses/{status_in_use_id}", headers=support_manager_auth_headers)
    
    # The API should return a 409 Conflict or similar error.
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "Cannot delete status, it is currently in use" in response.json()["detail"]
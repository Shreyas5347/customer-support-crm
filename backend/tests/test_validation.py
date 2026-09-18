import pytest


def test_create_ticket_invalid_email(client):
    payload = {
        "customer_name": "Rahul Sharma",
        "customer_email": "not-an-email",
        "subject": "Valid Subject",
        "description": "Valid description long enough.",
    }
    res = client.post("/api/tickets", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_create_ticket_missing_fields(client):
    payload = {
        "customer_name": "Rahul Sharma",
    }
    res = client.post("/api/tickets", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_create_ticket_short_description(client):
    payload = {
        "customer_name": "Rahul Sharma",
        "customer_email": "rahul@example.com",
        "subject": "Valid Subject",
        "description": "Short",  # min_length is 10
    }
    res = client.post("/api/tickets", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_update_ticket_invalid_status(client):
    # First create a valid ticket
    create_res = client.post("/api/tickets", json={
        "customer_name": "Rahul Sharma",
        "customer_email": "rahul@example.com",
        "subject": "Payment deducted",
        "description": "Payment was deducted but order failed.",
    })
    ticket_id = create_res.json()["ticket_id"]

    # Try updating with an invalid status string
    update_res = client.put(f"/api/tickets/{ticket_id}", json={
        "status": "INVALID_STATUS",
        "notes": "Testing invalid status",
    })
    assert update_res.status_code == 422
    data = update_res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"

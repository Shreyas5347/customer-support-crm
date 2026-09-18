import pytest


def test_create_ticket_success(client):
    payload = {
        "customer_name": "Rahul Sharma",
        "customer_email": "rahul@example.com",
        "subject": "Payment deducted but order failed",
        "description": "My account was debited Rs 500 for order #1234, but no confirmation was received.",
    }
    response = client.post("/api/tickets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "ticket_id" in data
    assert data["ticket_id"].startswith("TKT-")
    assert len(data["ticket_id"]) == 12  # TKT- + 8 chars
    assert "created_at" in data


def test_list_tickets_empty(client):
    response = client.get("/api/tickets")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tickets_filtering_and_search(client):
    # Create test tickets
    t1 = client.post("/api/tickets", json={
        "customer_name": "Rahul Sharma",
        "customer_email": "rahul@example.com",
        "subject": "Payment deducted",
        "description": "Money deducted twice",
    }).json()

    t2 = client.post("/api/tickets", json={
        "customer_name": "Priya Singh",
        "customer_email": "priya@example.com",
        "subject": "Delivery delayed",
        "description": "Package has not arrived after 5 days",
    }).json()

    # Basic list
    res = client.get("/api/tickets")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # Search by customer name
    res_search = client.get("/api/tickets?search=rahul")
    assert res_search.status_code == 200
    items = res_search.json()
    assert len(items) == 1
    assert items[0]["ticket_id"] == t1["ticket_id"]

    # Search by description keyword
    res_search_desc = client.get("/api/tickets?search=Package")
    assert res_search_desc.status_code == 200
    assert len(res_search_desc.json()) == 1
    assert res_search_desc.json()[0]["ticket_id"] == t2["ticket_id"]

    # Filter by status
    res_status = client.get("/api/tickets?status=OPEN")
    assert res_status.status_code == 200
    assert len(res_status.json()) == 2

    # Pagination test: limit 1
    res_page = client.get("/api/tickets?page=1&limit=1")
    assert res_page.status_code == 200
    assert len(res_page.json()) == 1


def test_get_ticket_details(client):
    create_res = client.post("/api/tickets", json={
        "customer_name": "Amit Patel",
        "customer_email": "amit@example.com",
        "subject": "Account access issue",
        "description": "Unable to log in after password reset.",
    })
    ticket_id = create_res.json()["ticket_id"]

    # Fetch details
    detail_res = client.get(f"/api/tickets/{ticket_id}")
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert data["ticket_id"] == ticket_id
    assert data["customer_name"] == "Amit Patel"
    assert data["customer_email"] == "amit@example.com"
    assert data["status"] == "OPEN"
    assert data["priority"] == "MEDIUM"
    assert data["notes"] == []


def test_get_ticket_not_found(client):
    res = client.get("/api/tickets/TKT-UNKNOWN")
    assert res.status_code == 404
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "TICKET_NOT_FOUND"


def test_update_ticket_status_and_note(client):
    create_res = client.post("/api/tickets", json={
        "customer_name": "Ananya Roy",
        "customer_email": "ananya@example.com",
        "subject": "Refund request",
        "description": "Requesting refund for returned item.",
    })
    ticket_id = create_res.json()["ticket_id"]

    # Update to IN_PROGRESS with note
    update_res = client.put(f"/api/tickets/{ticket_id}", json={
        "status": "IN_PROGRESS",
        "notes": "Payment team is investigating.",
    })
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["status"] == "IN_PROGRESS"
    assert len(data["notes"]) == 1
    assert data["notes"][0]["note_text"] == "Payment team is investigating."

    # Update to CLOSED without note
    update_closed = client.put(f"/api/tickets/{ticket_id}", json={
        "status": "CLOSED",
    })
    assert update_closed.status_code == 200
    data_closed = update_closed.json()
    assert data_closed["status"] == "CLOSED"
    assert len(data_closed["notes"]) == 1  # Note count stays 1


def test_update_ticket_not_found(client):
    res = client.put("/api/tickets/TKT-NONEXISTENT", json={
        "status": "CLOSED",
        "notes": "Closing ticket",
    })
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "TICKET_NOT_FOUND"

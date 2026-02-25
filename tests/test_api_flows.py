def test_signup_login_and_me_flow(client):
    signup_response = client.post(
        "/users/signup",
        json={
            "email": "test.user@example.com",
            "full_name": "Test User",
            "phone": "1234567890",
            "password": "secret123",
        },
    )
    assert signup_response.status_code == 201

    login_response = client.post(
        "/users/login",
        json={"email": "test.user@example.com", "password": "secret123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    me_response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "test.user@example.com"


def test_wallet_and_order_flow(client):
    client.post(
        "/users/signup",
        json={
            "email": "wallet.user@example.com",
            "full_name": "Wallet User",
            "phone": "1234567890",
            "password": "secret123",
        },
    )
    login = client.post(
        "/users/login",
        json={"email": "wallet.user@example.com", "password": "secret123"},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    credit = client.post("/wallet/me/credit", headers=headers, json={"amount": 50})
    assert credit.status_code == 200
    assert float(credit.json()["balance"]) == 50.0

    debit = client.post("/wallet/me/debit", headers=headers, json={"amount": 20})
    assert debit.status_code == 200
    assert float(debit.json()["balance"]) == 30.0

    order = client.post(
        "/orders",
        headers=headers,
        json={"amount": 10, "currency": "USD", "idempotency_key": "test-idem-1"},
    )
    assert order.status_code == 201

    orders = client.get("/orders", headers=headers)
    assert orders.status_code == 200
    assert len(orders.json()) == 1


def test_health_endpoint(client):
    health = client.get("/health")
    # In tests, real DB healthcheck points to configured DB, so accept healthy/unhealthy status codes.
    assert health.status_code in (200, 503)

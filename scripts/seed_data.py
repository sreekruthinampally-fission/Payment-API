#!/usr/bin/env python3
import argparse
import logging
import requests

BASE_URL = "http://localhost:8000"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


def ensure_user(base_url: str, email: str, full_name: str, password: str) -> None:
    """Create a user if it does not already exist."""
    response = requests.post(
        f"{base_url}/users/signup",
        json={
            "email": email,
            "full_name": full_name,
            "phone": None,
            "password": password,
        },
        timeout=10.0,
    )
    if response.status_code == 201:
        logger.info("User created: %s", email)
    elif response.status_code == 400:
        logger.info("User already exists: %s", email)
    else:
        raise RuntimeError(f"Signup failed: {response.status_code} {response.text}")


def login(base_url: str, email: str, password: str) -> str:
    """Return bearer token for the user."""
    response = requests.post(
        f"{base_url}/users/login",
        json={"email": email, "password": password},
        timeout=10.0,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Login failed: {response.status_code} {response.text}")
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def credit_wallet(base_url: str, token: str, amount: float) -> None:
    response = requests.post(
        f"{base_url}/wallet/me/credit",
        headers=auth_headers(token),
        json={"amount": amount},
        timeout=10.0,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Wallet credit failed: {response.status_code} {response.text}")
    data = response.json()
    logger.info("Wallet credited. Balance: %s", data["balance"])


def create_orders(base_url: str, token: str, count: int) -> None:
    for i in range(count):
        response = requests.post(
            f"{base_url}/orders",
            headers=auth_headers(token),
            json={
                "amount": 100.0 + (i * 25.0),
                "currency": "USD",
                "idempotency_key": f"seed-order-{i}",
            },
            timeout=10.0,
        )
        if response.status_code != 201:
            raise RuntimeError(f"Order create failed: {response.status_code} {response.text}")
        logger.info("Order created: %s", response.json()["order_id"])


def main():
    parser = argparse.ArgumentParser(description="Seed authenticated sample data")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--email", default="seed.user@example.com")
    parser.add_argument("--password", default="secret123")
    parser.add_argument("--full-name", default="Seed User")
    parser.add_argument("--credit", type=float, default=1000.0)
    parser.add_argument("--orders", type=int, default=3)
    args = parser.parse_args()

    ensure_user(args.base_url, args.email, args.full_name, args.password)
    token = login(args.base_url, args.email, args.password)
    credit_wallet(args.base_url, token, args.credit)
    create_orders(args.base_url, token, args.orders)
    logger.info("Seeding complete.")


if __name__ == "__main__":
    main()

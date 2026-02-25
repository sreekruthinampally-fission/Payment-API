#!/usr/bin/env python3
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests


class ScenarioRunner:
    def __init__(self, base_url: str, email: str, password: str, full_name: str):
        self.base_url = base_url
        self.email = email
        self.password = password
        self.full_name = full_name
        self.token = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def ensure_auth(self):
        signup = requests.post(
            f"{self.base_url}/users/signup",
            json={
                "email": self.email,
                "full_name": self.full_name,
                "phone": None,
                "password": self.password,
            },
            timeout=10.0,
        )
        if signup.status_code not in (201, 400):
            raise RuntimeError(f"Signup failed: {signup.status_code} {signup.text}")

        login = requests.post(
            f"{self.base_url}/users/login",
            json={"email": self.email, "password": self.password},
            timeout=10.0,
        )
        if login.status_code != 200:
            raise RuntimeError(f"Login failed: {login.status_code} {login.text}")
        self.token = login.json()["access_token"]

    def orders_retry(self):
        print("\n=== orders_retry ===")
        idempotency_key = f"retry-{int(time.time())}"
        payload = {
            "amount": 120.0,
            "currency": "USD",
            "idempotency_key": idempotency_key,
        }

        first = requests.post(
            f"{self.base_url}/orders",
            headers=self._headers(),
            json=payload,
            timeout=10.0,
        )
        second = requests.post(
            f"{self.base_url}/orders",
            headers=self._headers(),
            json=payload,
            timeout=10.0,
        )
        print(f"First: {first.status_code} {first.text}")
        print(f"Second: {second.status_code} {second.text}")

    def wallet_concurrency(self):
        print("\n=== wallet_concurrency ===")
        requests.post(
            f"{self.base_url}/wallet/me/credit",
            headers=self._headers(),
            json={"amount": 300.0},
            timeout=10.0,
        )

        def debit_once():
            response = requests.post(
                f"{self.base_url}/wallet/me/debit",
                headers=self._headers(),
                json={"amount": 10.0},
                timeout=10.0,
            )
            return response.status_code

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(debit_once) for _ in range(20)]
            statuses = [f.result() for f in as_completed(futures)]

        success_count = sum(status == 200 for status in statuses)
        wallet = requests.get(
            f"{self.base_url}/wallet/me",
            headers=self._headers(),
            timeout=10.0,
        ).json()
        print(f"Successful debits: {success_count}/20")
        print(f"Current balance: {wallet['balance']}")

    def mixed(self):
        print("\n=== mixed ===")
        requests.post(
            f"{self.base_url}/wallet/me/credit",
            headers=self._headers(),
            json={"amount": 200.0},
            timeout=10.0,
        )
        requests.post(
            f"{self.base_url}/orders",
            headers=self._headers(),
            json={"amount": 75.0, "currency": "USD", "idempotency_key": f"mix-{int(time.time())}"},
            timeout=10.0,
        )
        requests.post(
            f"{self.base_url}/wallet/me/debit",
            headers=self._headers(),
            json={"amount": 20.0},
            timeout=10.0,
        )
        wallet = requests.get(
            f"{self.base_url}/wallet/me",
            headers=self._headers(),
            timeout=10.0,
        )
        orders = requests.get(
            f"{self.base_url}/orders",
            headers=self._headers(),
            timeout=10.0,
        )
        print(f"Wallet: {wallet.status_code} {wallet.text}")
        print(f"Orders: {orders.status_code} count={len(orders.json()) if orders.status_code == 200 else 'n/a'}")


def main():
    parser = argparse.ArgumentParser(description="Run API scenarios against authenticated endpoints")
    parser.add_argument("--scenario", choices=["orders_retry", "wallet_concurrency", "mixed", "all"], default="all")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--email", default="scenario.user@example.com")
    parser.add_argument("--password", default="secret123")
    parser.add_argument("--full-name", default="Scenario User")
    args = parser.parse_args()

    runner = ScenarioRunner(args.base_url, args.email, args.password, args.full_name)
    runner.ensure_auth()

    if args.scenario in ("orders_retry", "all"):
        runner.orders_retry()
    if args.scenario in ("wallet_concurrency", "all"):
        runner.wallet_concurrency()
    if args.scenario in ("mixed", "all"):
        runner.mixed()


if __name__ == "__main__":
    main()

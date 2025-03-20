import pytest
import asyncio
from locust import HttpUser, task, between
from typing import List, Dict
import random
import json

class PaymentLoadTest(HttpUser):
    """Load test for payment system endpoints."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize test data."""
        self.test_users = self._create_test_users()
        self.test_orders = self._create_test_orders()
        
    def _create_test_users(self) -> List[Dict]:
        """Create test users for load testing."""
        users = []
        for i in range(100):
            user = {
                "username": f"loadtest_user_{i}",
                "email": f"loadtest_{i}@example.com",
                "phone_number": f"9891234567{i:03d}",
                "password": "test_password123",
                "wallet_balance": random.randint(0, 1000000)
            }
            users.append(user)
        return users
    
    def _create_test_orders(self) -> List[Dict]:
        """Create test orders for load testing."""
        orders = []
        for i in range(50):
            order = {
                "user_id": random.randint(1, 100),
                "amount": random.randint(10000, 100000),
                "status": "pending"
            }
            orders.append(order)
        return orders
    
    @task(3)
    def test_payment_wallet(self):
        """Test wallet payment endpoint under load."""
        order = random.choice(self.test_orders)
        payload = {
            "user_id": order["user_id"],
            "order_id": order["id"],
            "payment_method": "wallet"
        }
        
        with self.client.post(
            "/api/v1/payments/process",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(2)
    def test_payment_zarinpal(self):
        """Test ZarinPal payment endpoint under load."""
        order = random.choice(self.test_orders)
        payload = {
            "user_id": order["user_id"],
            "order_id": order["id"],
            "amount": order["amount"]
        }
        
        with self.client.post(
            "/api/v1/payments/zarinpal/initiate",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(2)
    def test_payment_bank_transfer(self):
        """Test bank transfer payment endpoint under load."""
        order = random.choice(self.test_orders)
        payload = {
            "user_id": order["user_id"],
            "order_id": order["id"],
            "amount": order["amount"]
        }
        
        with self.client.post(
            "/api/v1/payments/bank-transfer/initiate",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(1)
    def test_payment_verification(self):
        """Test payment verification endpoint under load."""
        transaction_id = random.randint(1, 1000)
        payload = {
            "transaction_id": transaction_id,
            "status": "OK",
            "ref_id": f"test_ref_{transaction_id}"
        }
        
        with self.client.post(
            "/api/v1/payments/verify",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(1)
    def test_get_transaction_status(self):
        """Test transaction status endpoint under load."""
        transaction_id = random.randint(1, 1000)
        
        with self.client.get(
            f"/api/v1/payments/transactions/{transaction_id}/status",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")

class PaymentStressTest(HttpUser):
    """Stress test for payment system endpoints."""
    
    wait_time = between(0.1, 1)
    
    def on_start(self):
        """Initialize test data."""
        self.test_users = self._create_test_users()
        self.test_orders = self._create_test_orders()
    
    def _create_test_users(self) -> List[Dict]:
        """Create test users for stress testing."""
        users = []
        for i in range(1000):
            user = {
                "username": f"stresstest_user_{i}",
                "email": f"stresstest_{i}@example.com",
                "phone_number": f"9891234567{i:03d}",
                "password": "test_password123",
                "wallet_balance": random.randint(0, 1000000)
            }
            users.append(user)
        return users
    
    def _create_test_orders(self) -> List[Dict]:
        """Create test orders for stress testing."""
        orders = []
        for i in range(500):
            order = {
                "user_id": random.randint(1, 1000),
                "amount": random.randint(10000, 100000),
                "status": "pending"
            }
            orders.append(order)
        return orders
    
    @task(5)
    def test_concurrent_payments(self):
        """Test concurrent payment processing under stress."""
        order = random.choice(self.test_orders)
        payment_method = random.choice(["wallet", "zarinpal", "bank_transfer"])
        
        payload = {
            "user_id": order["user_id"],
            "order_id": order["id"],
            "payment_method": payment_method,
            "amount": order["amount"]
        }
        
        with self.client.post(
            "/api/v1/payments/process",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(3)
    def test_concurrent_verifications(self):
        """Test concurrent payment verifications under stress."""
        transaction_id = random.randint(1, 2000)
        payment_method = random.choice(["zarinpal", "bank_transfer"])
        
        payload = {
            "transaction_id": transaction_id,
            "status": "OK",
            "ref_id": f"test_ref_{transaction_id}",
            "payment_method": payment_method
        }
        
        with self.client.post(
            "/api/v1/payments/verify",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}")
    
    @task(2)
    def test_concurrent_status_checks(self):
        """Test concurrent transaction status checks under stress."""
        transaction_id = random.randint(1, 2000)
        
        with self.client.get(
            f"/api/v1/payments/transactions/{transaction_id}/status",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status code: {response.status_code}") 
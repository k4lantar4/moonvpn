import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from app.main import app
from app.tests.utils import (
    create_test_user,
    create_test_vpn_config,
    create_test_subscription,
    create_test_payment,
    create_test_telegram_user,
    get_test_user_data
)
from app.core.config import settings

client = TestClient(app)

@pytest.mark.asyncio
class TestPerformance:
    async def test_concurrent_user_registration(self, db_session):
        """Test concurrent user registration performance."""
        num_users = 50
        start_time = time.time()
        
        # Create users concurrently
        tasks = []
        for i in range(num_users):
            user_data = get_test_user_data(
                email=f"test{i}@example.com",
                full_name=f"Test User {i}"
            )
            tasks.append(create_test_user(db_session, **user_data))
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        avg_time_per_user = total_time / num_users
        
        print(f"\nConcurrent User Registration Performance:")
        print(f"Total Users: {num_users}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Time per User: {avg_time_per_user:.2f} seconds")
        
        # Assert performance requirements
        assert total_time < 10.0  # Should complete within 10 seconds
        assert avg_time_per_user < 0.2  # Each user should take less than 0.2 seconds

    async def test_concurrent_vpn_config_creation(self, db_session):
        """Test concurrent VPN configuration creation performance."""
        # Create test user
        user = await create_test_user(db_session, **get_test_user_data())
        
        num_configs = 100
        start_time = time.time()
        
        # Create VPN configs concurrently
        tasks = []
        for i in range(num_configs):
            tasks.append(
                create_test_vpn_config(
                    db_session,
                    user.id,
                    server=f"test{i}.vpn.server"
                )
            )
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        avg_time_per_config = total_time / num_configs
        
        print(f"\nConcurrent VPN Config Creation Performance:")
        print(f"Total Configs: {num_configs}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Time per Config: {avg_time_per_config:.2f} seconds")
        
        # Assert performance requirements
        assert total_time < 15.0  # Should complete within 15 seconds
        assert avg_time_per_config < 0.15  # Each config should take less than 0.15 seconds

    async def test_concurrent_api_requests(self, db_session):
        """Test concurrent API request performance."""
        # Create test user and login
        user = await create_test_user(db_session, **get_test_user_data())
        
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": user.email,
                "password": "testpassword123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        num_requests = 200
        start_time = time.time()
        
        # Make concurrent API requests
        async def make_request():
            response = client.get(
                f"{settings.API_V1_STR}/vpn/config",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert response.status_code == 200
        
        tasks = [make_request() for _ in range(num_requests)]
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        avg_time_per_request = total_time / num_requests
        requests_per_second = num_requests / total_time
        
        print(f"\nConcurrent API Requests Performance:")
        print(f"Total Requests: {num_requests}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Time per Request: {avg_time_per_request:.2f} seconds")
        print(f"Requests per Second: {requests_per_second:.2f}")
        
        # Assert performance requirements
        assert total_time < 20.0  # Should complete within 20 seconds
        assert avg_time_per_request < 0.1  # Each request should take less than 0.1 seconds
        assert requests_per_second > 10  # Should handle at least 10 requests per second

    async def test_database_query_performance(self, db_session):
        """Test database query performance."""
        # Create multiple test users and related data
        num_users = 100
        users = []
        
        for i in range(num_users):
            user = await create_test_user(
                db_session,
                email=f"test{i}@example.com",
                full_name=f"Test User {i}"
            )
            users.append(user)
            
            # Create related data for each user
            await create_test_vpn_config(db_session, user.id)
            await create_test_subscription(db_session, user.id)
            await create_test_payment(db_session, user.id)
            await create_test_telegram_user(db_session, user.id)
        
        # Test complex query performance
        start_time = time.time()
        
        # Perform complex queries
        for user in users:
            # Get user with all related data
            response = client.get(
                f"{settings.API_V1_STR}/users/{user.id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert response.status_code == 200
        
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        avg_time_per_query = total_time / num_users
        
        print(f"\nDatabase Query Performance:")
        print(f"Total Users: {num_users}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Time per Query: {avg_time_per_query:.2f} seconds")
        
        # Assert performance requirements
        assert total_time < 30.0  # Should complete within 30 seconds
        assert avg_time_per_query < 0.3  # Each query should take less than 0.3 seconds

    async def test_telegram_notification_performance(self, db_session):
        """Test Telegram notification sending performance."""
        # Create test user and Telegram user
        user = await create_test_user(db_session, **get_test_user_data())
        telegram_user = await create_test_telegram_user(db_session, user.id)
        
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            data={
                "username": user.email,
                "password": "testpassword123"
            }
        )
        
        access_token = login_response.json()["access_token"]
        
        num_notifications = 50
        start_time = time.time()
        
        # Send notifications concurrently
        async def send_notification():
            response = client.post(
                f"{settings.API_V1_STR}/telegram/test-notification",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            assert response.status_code == 200
        
        tasks = [send_notification() for _ in range(num_notifications)]
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        avg_time_per_notification = total_time / num_notifications
        notifications_per_second = num_notifications / total_time
        
        print(f"\nTelegram Notification Performance:")
        print(f"Total Notifications: {num_notifications}")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"Average Time per Notification: {avg_time_per_notification:.2f} seconds")
        print(f"Notifications per Second: {notifications_per_second:.2f}")
        
        # Assert performance requirements
        assert total_time < 25.0  # Should complete within 25 seconds
        assert avg_time_per_notification < 0.5  # Each notification should take less than 0.5 seconds
        assert notifications_per_second > 2  # Should handle at least 2 notifications per second 
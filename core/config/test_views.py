import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from api.models import Subscription, Payment

User = get_user_model()

@pytest.mark.django_db
class UserViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('user-profile')

    def test_get_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_update_profile(self):
        data = {
            'email': 'newemail@example.com',
            'phone': '1234567890'
        }
        response = self.client.put(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'newemail@example.com')
        self.assertEqual(response.data['phone'], '1234567890')

@pytest.mark.django_db
class SubscriptionViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan='basic',
            status='active'
        )
        self.url = reverse('subscription-user-subscriptions')

    def test_get_user_subscriptions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['plan'], 'basic')
        self.assertEqual(response.data[0]['status'], 'active')

@pytest.mark.django_db
class PaymentViewSetTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.payment = Payment.objects.create(
            user=self.user,
            amount=1000,
            status='pending'
        )
        self.url = reverse('payment-list')

    def test_create_payment(self):
        data = {
            'amount': 2000,
            'payment_method': 'card'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['amount'], 2000)
        self.assertEqual(response.data['status'], 'pending')

    def test_get_payment_status(self):
        url = reverse('payment-status', kwargs={'pk': self.payment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['amount'], 1000) 
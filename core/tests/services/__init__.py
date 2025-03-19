from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Service, Plan, Subscription, Config, Usage, ServiceLog, ServiceMetric, ServiceAlert
from .tasks import (
    check_expired_subscriptions,
    collect_service_metrics,
    check_service_health,
    cleanup_old_metrics,
    cleanup_old_alerts,
    notify_expiring_subscriptions,
    generate_usage_report
)

User = get_user_model()

class ServiceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Description',
            owner=self.user
        )
    
    def test_service_creation(self):
        self.assertEqual(self.service.name, 'Test Service')
        self.assertEqual(self.service.description, 'Test Description')
        self.assertEqual(self.service.owner, self.user)
        self.assertTrue(self.service.is_active)
    
    def test_service_str(self):
        self.assertEqual(str(self.service), 'Test Service')

class PlanModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Description',
            owner=self.user
        )
        self.plan = Plan.objects.create(
            name='Test Plan',
            description='Test Plan Description',
            service=self.service,
            price=10.00,
            duration=30
        )
    
    def test_plan_creation(self):
        self.assertEqual(self.plan.name, 'Test Plan')
        self.assertEqual(self.plan.description, 'Test Plan Description')
        self.assertEqual(self.plan.service, self.service)
        self.assertEqual(self.plan.price, 10.00)
        self.assertEqual(self.plan.duration, 30)
        self.assertTrue(self.plan.is_active)
    
    def test_plan_str(self):
        self.assertEqual(str(self.plan), 'Test Plan')

class SubscriptionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Description',
            owner=self.user
        )
        self.plan = Plan.objects.create(
            name='Test Plan',
            description='Test Plan Description',
            service=self.service,
            price=10.00,
            duration=30
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
    
    def test_subscription_creation(self):
        self.assertEqual(self.subscription.user, self.user)
        self.assertEqual(self.subscription.plan, self.plan)
        self.assertEqual(self.subscription.status, 'active')
        self.assertTrue(self.subscription.is_active())
    
    def test_subscription_str(self):
        self.assertEqual(str(self.subscription), f'{self.user.username} - {self.plan.name}')
    
    def test_subscription_renew(self):
        self.subscription.renew()
        self.assertEqual(self.subscription.status, 'active')
        self.assertTrue(self.subscription.is_active())
    
    def test_subscription_cancel(self):
        self.subscription.cancel()
        self.assertEqual(self.subscription.status, 'cancelled')
        self.assertFalse(self.subscription.is_active())

class ServiceTasksTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Description',
            owner=self.user
        )
        self.plan = Plan.objects.create(
            name='Test Plan',
            description='Test Plan Description',
            service=self.service,
            price=10.00,
            duration=30
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
    
    def test_check_expired_subscriptions(self):
        # Set subscription to expire
        self.subscription.end_date = timezone.now() - timezone.timedelta(days=1)
        self.subscription.save()
        
        check_expired_subscriptions()
        
        # Refresh subscription from database
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, 'expired')
    
    def test_collect_service_metrics(self):
        collect_service_metrics()
        
        # Check if metrics were created
        metrics = ServiceMetric.objects.filter(service=self.service)
        self.assertTrue(metrics.exists())
    
    def test_check_service_health(self):
        check_service_health()
        
        # Check if any alerts were created
        alerts = ServiceAlert.objects.filter(service=self.service)
        self.assertTrue(alerts.exists())
    
    def test_cleanup_old_metrics(self):
        # Create old metric
        ServiceMetric.objects.create(
            service=self.service,
            name='test_metric',
            value=100,
            timestamp=timezone.now() - timezone.timedelta(days=31)
        )
        
        cleanup_old_metrics()
        
        # Check if old metric was deleted
        metrics = ServiceMetric.objects.filter(service=self.service)
        self.assertFalse(metrics.exists())
    
    def test_cleanup_old_alerts(self):
        # Create old resolved alert
        ServiceAlert.objects.create(
            service=self.service,
            level='info',
            message='Test Alert',
            is_resolved=True,
            created_at=timezone.now() - timezone.timedelta(days=8)
        )
        
        cleanup_old_alerts()
        
        # Check if old alert was deleted
        alerts = ServiceAlert.objects.filter(service=self.service)
        self.assertFalse(alerts.exists())
    
    def test_notify_expiring_subscriptions(self):
        # Set subscription to expire in 3 days
        self.subscription.end_date = timezone.now() + timezone.timedelta(days=3)
        self.subscription.save()
        
        notify_expiring_subscriptions()
        
        # Check if notification was created
        # Note: This depends on your notification system implementation
        pass
    
    def test_generate_usage_report(self):
        # Create some usage data
        Usage.objects.create(
            subscription=self.subscription,
            date=timezone.now().date(),
            amount=100
        )
        
        generate_usage_report()
        
        # Check if report was generated
        # Note: This depends on your notification system implementation
        pass 
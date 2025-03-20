# Payment Integration Guide

## Architecture Overview

The payment system follows a modular architecture with the following components:

```
vpn/
├── services/
│   ├── payment_manager.py      # Core payment management service
│   └── subscription_manager.py  # Subscription management service
├── models/
│   ├── plan.py                 # Plan model
│   ├── subscription.py         # Subscription model
│   └── transaction.py          # Transaction model
└── api/
    ├── views.py                # API endpoints
    ├── serializers.py          # Data serializers
    └── urls.py                 # URL routing
```

## Adding a New Payment Gateway

1. Create a new gateway class that implements the `PaymentGateway` interface:

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

class NewGateway(PaymentGateway):
    def __init__(self):
        self.api_key = settings.NEW_GATEWAY_API_KEY
        self.api_url = settings.NEW_GATEWAY_API_URL
        
    def create_payment(
        self,
        amount: float,
        description: str,
        **kwargs
    ) -> Tuple[Optional[str], Optional[str]]:
        try:
            # Implement gateway-specific payment creation
            response = requests.post(
                f"{self.api_url}/create",
                json={
                    "amount": amount,
                    "description": description,
                    # Add gateway-specific fields
                }
            )
            
            result = response.json()
            
            if result["success"]:
                return result["payment_id"], result["payment_url"]
            else:
                return None, result["error"]
                
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            return None, str(e)
    
    def verify_payment(self, payment_id: str) -> Tuple[bool, Optional[str]]:
        try:
            # Implement gateway-specific verification
            response = requests.post(
                f"{self.api_url}/verify",
                json={"payment_id": payment_id}
            )
            
            result = response.json()
            
            if result["success"]:
                return True, None
            else:
                return False, result["error"]
                
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return False, str(e)
```

2. Register the gateway in `PaymentManager`:

```python
class PaymentManager:
    GATEWAYS = {
        'zarinpal': ZarinPalGateway,
        'wallet': WalletGateway,
        'new_gateway': NewGateway  # Add new gateway
    }
```

3. Add gateway-specific settings in `settings.py`:

```python
NEW_GATEWAY_API_KEY = env('NEW_GATEWAY_API_KEY', default='')
NEW_GATEWAY_API_URL = env('NEW_GATEWAY_API_URL', default='')
```

## Handling Payments

### Creating a Payment

```python
from vpn.services.payment_manager import PaymentManager

# Create a payment
payment_data, error = PaymentManager.create_payment(
    user=request.user,
    amount=plan.price,
    payment_method='zarinpal',
    description=f"Subscription to {plan.name}",
    transaction_type='new',
    email=request.user.email,
    mobile=request.user.phone
)

if error:
    # Handle error
    return Response({'error': error}, status=400)

# Return payment data to frontend
return Response({
    'transaction_id': payment_data['transaction_id'],
    'payment_url': payment_data['payment_url']
})
```

### Verifying a Payment

```python
from vpn.services.payment_manager import PaymentManager

# Verify payment
transaction, error = PaymentManager.verify_payment(
    payment_id=payment_id,
    payment_method='zarinpal'
)

if error:
    # Handle error
    return Response({'error': error}, status=400)

# Payment successful
return Response({
    'status': 'success',
    'transaction': TransactionSerializer(transaction).data
})
```

## Subscription Management

### Creating a Subscription

```python
from vpn.services.subscription_manager import SubscriptionManager

# Create subscription
subscription, error = SubscriptionManager.create_subscription(
    user=request.user,
    plan=plan,
    payment_method='zarinpal',
    auto_renew=False
)

if error:
    # Handle error
    return Response({'error': error}, status=400)

# Return subscription data
return Response(SubscriptionSerializer(subscription).data)
```

### Handling Renewals

```python
from vpn.services.subscription_manager import SubscriptionManager

# Renew subscription
success, error = SubscriptionManager.renew_subscription(
    subscription=subscription,
    payment_method='zarinpal'
)

if error:
    # Handle error
    return Response({'error': error}, status=400)

# Return updated subscription
return Response(SubscriptionSerializer(subscription).data)
```

## Error Handling Best Practices

1. **Gateway Errors**
```python
try:
    response = requests.post(gateway_url, data=payload)
    response.raise_for_status()
except requests.RequestException as e:
    logger.error(f"Gateway error: {str(e)}")
    return None, "Payment gateway is unavailable"
```

2. **Transaction Consistency**
```python
from django.db import transaction

@transaction.atomic
def process_payment(payment_id):
    # Lock the transaction record
    transaction = Transaction.objects.select_for_update().get(
        payment_id=payment_id
    )
    
    # Prevent double processing
    if transaction.status == 'completed':
        return transaction, None
        
    # Process payment
    # ...
```

3. **Logging**
```python
import logging

logger = logging.getLogger(__name__)

def create_payment():
    try:
        # Payment creation logic
        logger.info(
            "Payment created",
            extra={
                'user_id': user.id,
                'amount': amount,
                'payment_method': payment_method
            }
        )
    except Exception as e:
        logger.error(
            "Payment creation failed",
            exc_info=True,
            extra={
                'user_id': user.id,
                'error': str(e)
            }
        )
```

## Testing

### Unit Tests

```python
from django.test import TestCase
from vpn.services.payment_manager import PaymentManager

class PaymentManagerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.plan = Plan.objects.create(
            name='Test Plan',
            price=100000
        )
    
    def test_create_payment(self):
        payment_data, error = PaymentManager.create_payment(
            user=self.user,
            amount=self.plan.price,
            payment_method='zarinpal',
            description='Test payment'
        )
        
        self.assertIsNone(error)
        self.assertIsNotNone(payment_data['payment_id'])
        self.assertIsNotNone(payment_data['payment_url'])
```

### Integration Tests

```python
from django.test import TestCase
from rest_framework.test import APIClient

class PaymentIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_subscription_creation(self):
        response = self.client.post('/api/subscriptions/', {
            'plan': self.plan.id,
            'payment_method': 'zarinpal'
        })
        
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['payment_url'])
```

## Security Considerations

1. **Input Validation**
```python
from decimal import Decimal
from django.core.validators import MinValueValidator

class Transaction(models.Model):
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
```

2. **Payment Data Encryption**
```python
from django.conf import settings
from cryptography.fernet import Fernet

def encrypt_payment_data(data):
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.encrypt(data.encode()).decode()

def decrypt_payment_data(encrypted_data):
    f = Fernet(settings.ENCRYPTION_KEY)
    return f.decrypt(encrypted_data.encode()).decode()
```

3. **Rate Limiting**
```python
from rest_framework.throttling import UserRateThrottle

class PaymentRateThrottle(UserRateThrottle):
    rate = '100/minute'

class PaymentViewSet(viewsets.ModelViewSet):
    throttle_classes = [PaymentRateThrottle]
```

## Monitoring and Debugging

1. **Transaction Monitoring**
```python
def monitor_transactions():
    # Find stuck transactions
    stuck_transactions = Transaction.objects.filter(
        status='pending',
        created_at__lte=timezone.now() - timedelta(hours=1)
    )
    
    for transaction in stuck_transactions:
        logger.warning(
            f"Stuck transaction found: {transaction.id}",
            extra={'payment_id': transaction.payment_id}
        )
```

2. **Payment Gateway Health Check**
```python
def check_gateway_health():
    for gateway_name, gateway_class in PaymentManager.GATEWAYS.items():
        try:
            gateway = gateway_class()
            # Perform health check
            is_healthy = gateway.health_check()
            
            if not is_healthy:
                logger.error(f"Gateway {gateway_name} is unhealthy")
                
        except Exception as e:
            logger.error(
                f"Gateway {gateway_name} health check failed",
                exc_info=True
            )
```

## Performance Optimization

1. **Caching**
```python
from django.core.cache import cache

def get_transaction_status(transaction_id):
    cache_key = f'transaction_status_{transaction_id}'
    status = cache.get(cache_key)
    
    if status is None:
        transaction = Transaction.objects.get(id=transaction_id)
        status = transaction.status
        cache.set(cache_key, status, timeout=300)  # 5 minutes
    
    return status
```

2. **Database Optimization**
```python
class Transaction(models.Model):
    # Add indexes for frequently queried fields
    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_id']),
            models.Index(fields=['created_at'])
        ]
```

## Deployment Checklist

1. **Environment Variables**
   - Set all required gateway credentials
   - Configure callback URLs
   - Set encryption keys

2. **SSL Configuration**
   - Install valid SSL certificate
   - Configure secure headers
   - Enable HSTS

3. **Database**
   - Apply migrations
   - Create indexes
   - Set up backup system

4. **Monitoring**
   - Set up error tracking (e.g., Sentry)
   - Configure logging
   - Set up alerts for failed payments

5. **Testing**
   - Test all payment flows
   - Verify gateway integrations
   - Check error handling 
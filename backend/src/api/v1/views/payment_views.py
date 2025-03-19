"""
Payment views for the API.
"""

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction

from main.models import Wallet, Transaction, Order, Voucher
from main.serializers import (
    WalletSerializer, TransactionSerializer,
    OrderSerializer, VoucherSerializer
)
from main.services import PaymentService

class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user wallets."""
    
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get queryset for the current user."""
        return Wallet.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create a new wallet for the current user."""
        serializer.save(user=self.request.user)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing transactions."""
    
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get queryset for the current user."""
        return Transaction.objects.filter(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing orders."""
    
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get queryset for the current user."""
        return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create a new order for the current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def verify_payment(self, request, pk=None):
        """Verify payment for an order."""
        order = self.get_object()
        payment_service = PaymentService()
        
        result = payment_service.verify_payment({
            'payment_id': order.payment_id
        })
        
        return Response(result)

class VoucherViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing vouchers."""
    
    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated]
    queryset = Voucher.objects.filter(is_active=True)
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate a voucher."""
        voucher = self.get_object()
        order_amount = request.data.get('order_amount')
        
        if not order_amount:
            return Response({
                'success': False,
                'message': 'Order amount is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            order_amount = float(order_amount)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid order amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not voucher.is_valid():
            return Response({
                'success': False,
                'message': 'Voucher is not valid'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        discount = voucher.calculate_discount(order_amount)
        
        return Response({
            'success': True,
            'message': 'Voucher is valid',
            'discount': discount
        })

class CurrentUserWalletView(views.APIView):
    """API endpoint for getting current user's wallet info."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's wallet info."""
        wallet = Wallet.objects.get_or_create(user=request.user)[0]
        serializer = WalletSerializer(wallet)
        return Response(serializer.data)

class CurrentUserOrdersView(views.APIView):
    """API endpoint for getting current user's orders."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's orders."""
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

class PaymentCallbackView(views.APIView):
    """API endpoint for payment gateway callbacks."""
    permission_classes = []  # Allow anonymous access for payment gateway callbacks

    def post(self, request):
        """Handle payment gateway callback."""
        payment_service = PaymentService()
        result = payment_service.handle_callback(request.data)
        return Response(result)

class PaymentVerifyView(views.APIView):
    """API endpoint for verifying payments."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Verify a payment."""
        payment_service = PaymentService()
        result = payment_service.verify_payment(request.data)
        return Response(result) 
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from main.models import User, UserActivity
from main.serializers import UserSerializer

class LoginView(generics.GenericAPIView):
    """View for user login and token generation."""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': _('Please provide both username and password.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({
                'error': _('Invalid credentials.')
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'error': _('This account is inactive.')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Update last login
        user.last_login = timezone.now()
        user.last_login_ip = request.META.get('REMOTE_ADDR')
        user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            metadata={
                'method': 'api',
                'success': True
            }
        )
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })

class LogoutView(generics.GenericAPIView):
    """View for user logout."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='logout',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                metadata={
                    'method': 'api',
                    'success': True
                }
            )
            
            return Response({'message': _('Successfully logged out.')})
        except Exception as e:
            return Response({
                'error': _('Invalid token.')
            }, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(generics.GenericAPIView):
    """View for refreshing access tokens."""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response({
                'error': _('Please provide a refresh token.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh = RefreshToken(refresh_token)
            return Response({
                'access': str(refresh.access_token)
            })
        except Exception as e:
            return Response({
                'error': _('Invalid refresh token.')
            }, status=status.HTTP_401_UNAUTHORIZED)

class VerifyTokenView(generics.GenericAPIView):
    """View for verifying access tokens."""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        
        if not token:
            return Response({
                'error': _('Please provide a token to verify.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            RefreshToken(token)
            return Response({'valid': True})
        except Exception:
            return Response({'valid': False}) 
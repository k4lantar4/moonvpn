from rest_framework import permissions
from .models import LiveChatSession, LiveChatOperator

class IsOperator(permissions.BasePermission):
    """
    Custom permission to only allow operators to access operator-specific views.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   hasattr(request.user, 'operator_profile'))

class IsSessionParticipant(permissions.BasePermission):
    """
    Custom permission to only allow participants of a chat session to access messages.
    """
    def has_permission(self, request, view):
        session_id = view.kwargs.get('session_pk')
        if not session_id:
            return False
            
        try:
            session = LiveChatSession.objects.get(id=session_id)
            return (request.user == session.user or 
                   request.user == session.operator or 
                   request.user.is_staff)
        except LiveChatSession.DoesNotExist:
            return False 
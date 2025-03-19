from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from model_utils import FieldTracker

class LiveChatSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        CLOSED = 'closed', _('Closed')
        TRANSFERRED = 'transferred', _('Transferred')

    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_app_sessions')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_app_handled_sessions')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    subject = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    tracker = FieldTracker()

    class Meta:
        app_label = 'chat'
        ordering = ['-created_at']
        verbose_name = _('Live Chat Session')
        verbose_name_plural = _('Live Chat Sessions')

    def __str__(self):
        return f"Chat Session {self.id} - {self.user.username}"

class LiveChatMessage(models.Model):
    class MessageType(models.TextChoices):
        TEXT = 'text', _('Text')
        FILE = 'file', _('File')
        IMAGE = 'image', _('Image')
        SYSTEM = 'system', _('System')

    session = models.ForeignKey(LiveChatSession, on_delete=models.CASCADE, related_name='chat_app_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_app_messages')
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField()
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'chat'
        ordering = ['created_at']
        verbose_name = _('Live Chat Message')
        verbose_name_plural = _('Live Chat Messages')

    def __str__(self):
        return f"Message {self.id} in Session {self.session.id}"

class LiveChatOperator(models.Model):
    class Status(models.TextChoices):
        ONLINE = 'online', _('Online')
        BUSY = 'busy', _('Busy')
        OFFLINE = 'offline', _('Offline')

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_app_operator_profile')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OFFLINE)
    max_sessions = models.IntegerField(default=5)
    current_sessions = models.IntegerField(default=0)
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tracker = FieldTracker()

    class Meta:
        app_label = 'chat'
        verbose_name = _('Live Chat Operator')
        verbose_name_plural = _('Live Chat Operators')

    def __str__(self):
        return f"Operator {self.user.username}"

class LiveChatRating(models.Model):
    session = models.OneToOneField(LiveChatSession, on_delete=models.CASCADE, related_name='chat_app_rating')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_app_user_ratings')
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_app_operator_ratings')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'chat'
        verbose_name = _('Live Chat Rating')
        verbose_name_plural = _('Live Chat Ratings')

    def __str__(self):
        return f"Rating {self.rating} for Session {self.session.id}" 
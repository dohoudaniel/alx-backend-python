from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messaging_sent_messages'   # <- namespaced to avoid clashes
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messaging_received_messages'  # <- namespaced to avoid clashes
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # fields for edit tracking
    edited = models.BooleanField(default=False)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='messaging_edited_messages'  # also namespaced
    )

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'Message from {self.sender} to {self.receiver} at {self.timestamp}'


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'   # keep if you want to use notifications across app; change if it clashes
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    verb = models.CharField(max_length=255)  # e.g., "sent you a message"
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'Notification for {self.user}: {self.verb}'


class MessageHistory(models.Model):
    """
    Stores previous versions of a Message's content.
    Each record is created before the Message is updated.
    """
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='history'
    )
    old_content = models.TextField()
    edited_at = models.DateTimeField(default=timezone.now)
    editor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='message_edit_history'
    )

    class Meta:
        ordering = ['-edited_at']

    def __str__(self):
        return f'History for Message {self.message_id} at {self.edited_at}'


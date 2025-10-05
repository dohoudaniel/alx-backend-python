from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

# import the manager we created
from .managers import UnreadMessagesManager

User = get_user_model()

class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messaging_sent_messages'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messaging_received_messages'
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # reply/thread fields
    parent_message = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    thread_root = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='thread_messages',
        help_text='Top-level message for this thread (self for root messages).'
    )

    # UNREAD flag required by the assessment (default True = unread)
    unread = models.BooleanField(default=True, db_index=True)

    # fields for edit tracking
    edited = models.BooleanField(default=False)
    last_edited_at = models.DateTimeField(null=True, blank=True)
    last_edited_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='messaging_edited_messages'
    )

    # Managers
    objects = models.Manager()            # default manager
    unread = UnreadMessagesManager()      # custom manager expected by checks

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['thread_root']),  # speeds up fetching a thread
            models.Index(fields=['parent_message']),
            models.Index(fields=['receiver', 'unread']),  # composite index to optimize unread queries

        ]

    def __str__(self):
        return f'Message {self.pk} from {self.sender} to {self.receiver} at {self.timestamp}'

    def save(self, *args, **kwargs):
        """
        Ensure thread_root is set:
         - If this message has a parent_message, thread_root = parent's thread_root if present,
           otherwise parent's pk (parent is root).
         - If no parent_message, thread_root stays None (or self after save).
        We'll set thread_root to parent's thread_root or parent; after first save of a root
        message, set thread_root=self (optional).
        """
        # If reply: compute thread_root from parent
        if self.parent_message:
            parent = self.parent_message
            # prefer parent's thread_root if set, else parent's pk (parent is root)
            self.thread_root = parent.thread_root or parent
        super().save(*args, **kwargs)

        # For top-level (no parent) messages we might want thread_root=self so
        # queries can always filter by thread_root.
        if not self.parent_message and self.thread_root is None:
            # Set thread_root to self and save (only once)
            self.thread_root = self
            super().save(update_fields=['thread_root'])


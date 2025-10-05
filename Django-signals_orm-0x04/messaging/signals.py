from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Message, Notification, MessageHistory

User = get_user_model()

@receiver(post_save, sender=Message)
def create_notification_on_new_message(sender, instance: Message, created: bool, **kwargs):
    """Create a Notification for the receiver when a new Message is created."""
    if not created:
        return
    if instance.sender_id == instance.receiver_id:
        return

    def _create_notification():
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            verb=f"{instance.sender.get_full_name() or instance.sender.username} sent you a message"
        )

    transaction.on_commit(_create_notification)


@receiver(pre_save, sender=Message)
def log_message_edit_history(sender, instance: Message, **kwargs):
    """
    Before a Message is saved, if it already exists and content is changing,
    create a MessageHistory record with the prior content and mark the Message as edited.
    The view should attach `instance._editor = request.user` before saving when available.
    """
    # If new message, nothing to log
    if not instance.pk:
        return

    try:
        previous = Message.objects.get(pk=instance.pk)
    except Message.DoesNotExist:
        return

    # Only log when content actually changes
    if previous.content == instance.content:
        return

    # Get the transient editor attribute (set in the view) or fallback to previous last_edited_by
    editor = getattr(instance, "_editor", None) or instance.last_edited_by

    # Create history record BEFORE the message is updated
    MessageHistory.objects.create(
        message_id=previous.pk,
        old_content=previous.content,
        edited_at=timezone.now(),
        editor=editor
    )

    # Update message metadata so saved instance reflects edit state
    instance.edited = True
    instance.last_edited_at = timezone.now()
    if editor:
        instance.last_edited_by = editor


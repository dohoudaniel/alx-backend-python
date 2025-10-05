from django.db.models.signals import post_save, pre_save, post_delete
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

@receiver(post_delete, sender=User)
def cleanup_user_related_data(sender, instance: User, **kwargs):
    """
    Clean up messaging-related data after a User is deleted.

    We do explicit cleanup here to be explicit and resilient across apps,
    and to ensure ordering (e.g., remove Notifications referencing the user,
    null-out histories where the user was the editor, and delete messages).
    If your model FKs already use CASCADE, some of these deletes will be no-ops,
    but explicit deletion here avoids leftover objects if FK settings differ elsewhere.
    """
    # perform cleanup after the outer transaction completes
    def _cleanup():
        from .models import Message, Notification, MessageHistory

        # 1) Remove notifications where the user was the recipient
        Notification.objects.filter(user_id=instance.pk).delete()

        # 2) Delete messages where user was sender or receiver.
        # These will cascade-delete MessageHistory records that reference the Message.
        Message.objects.filter(sender_id=instance.pk).delete()
        Message.objects.filter(receiver_id=instance.pk).delete()

        # 3) For MessageHistory entries where the deleted user was the editor,
        #    prefer to keep the historical content but null the editor reference.
        MessageHistory.objects.filter(editor_id=instance.pk).update(editor=None)

        # 4) If you had any other per-user objects in messaging, wipe them here.
    transaction.on_commit(_cleanup)

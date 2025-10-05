from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Message, Notification

User = get_user_model()

@receiver(post_save, sender=Message)
def create_notification_on_new_message(sender, instance: Message, created: bool, **kwargs):
    """
    Creates a Notification for the message receiver when a new Message is created.
    We use transaction.on_commit to ensure the message is fully committed to DB.
    Keep this handler small — avoid long-running tasks here.
    """
    if not created:
        return

    # Avoid notifying when sender == receiver (if that case occurs)
    if instance.sender_id == instance.receiver_id:
        return

    def _create_notification():
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            verb=f"{instance.sender.get_full_name() or instance.sender.username} sent you a message"
        )

    # Create notification after DB transaction commits
    transaction.on_commit(_create_notification)


# messaging/managers.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UnreadMessagesManager(models.Manager):
    """
    Custom manager to query unread messages.
    Provides a clean API: Message.unread.unread_for_user(user)
    """
    def get_queryset(self):
        return super().get_queryset()

    def unread_for_user(self, user):
        """
        Return unread messages for the given receiver user.
        """
        return self.get_queryset().filter(receiver=user, unread=True)

    def mark_all_read(self, user):
        """
        Mark all unread messages for `user` as read (set unread=False).
        Returns number of rows updated.
        """
        qs = self.unread_for_user(user)
        return qs.update(unread=False)

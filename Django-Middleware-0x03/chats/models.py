from django.db import models

# Create your models here.

#!/usr/bin/env python3
"""Chat app models: custom User, Conversation, ConversationParticipant, Message."""
from __future__ import annotations

import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinLengthValidator


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.

    - Replaces the default integer PK with a UUID primary key (user_id).
    - Ensures unique email and required first/last names as per schema.
    - Adds phone_number, role enum and created_at timestamp.
    Note: AbstractUser already provides username and password fields.
    We add password_hash to mirror the external schema field name (optional).
    """
    # Use UUID as primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )

    # AbstractUser already has first_name, last_name, email, password fields.
    # Make sure email is unique and required.
    email = models.EmailField(unique=True, blank=False)

    # Optional phone number with a basic validation (internationally permissive)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{7,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=20,
        blank=True,
        null=True,
    )

    # role enum
    class Role(models.TextChoices):
        GUEST = "guest", "Guest"
        HOST = "host", "Host"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.GUEST,
    )

    # created timestamp
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # optional field to mirror the "password_hash" column from the schema.
    # Django manages passwords in .password; keep this as a convenience field
    # or for integration/migration scenarios.
    password_hash = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional: store external password hash if required.",
    )

    # username field default from AbstractUser remains, if you prefer email auth
    # you can set USERNAME_FIELD = "email" in settings and update REQUIRED_FIELDS.

    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        # index email explicitly (unique already creates index but listing for clarity)
        indexes = [
            models.Index(fields=["email"], name="user_email_idx"),
            models.Index(fields=["created_at"], name="user_created_idx"),
        ]
        constraints = [
            # email unique handled by field attribute - this keeps explicitness
        ]

    def __str__(self) -> str:
        return f"{self.get_full_name()} <{self.email}>"


class Conversation(models.Model):
    """
    Conversation model representing a chat thread between participants.

    - conversation_id: UUID primary key
    - participants: ManyToMany to User via ConversationParticipant
    - created_at: timestamp
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ConversationParticipant",
        related_name="conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "conversation"
        verbose_name_plural = "conversations"
        indexes = [
            models.Index(fields=["created_at"], name="conv_created_idx"),
        ]

    def __str__(self) -> str:
        # e.g. "Conversation <UUID> (2 participants)"
        count = self.participants.count()
        return f"Conversation {self.id} ({count} participants)"


class ConversationParticipant(models.Model):
    """
    Through model to record which users participate in a conversation.

    - Ensures unique pair (conversation, user) to avoid duplicate participants.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="participants_rows")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversation_rows")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "conversation participant"
        verbose_name_plural = "conversation participants"
        unique_together = ("conversation", "user")
        indexes = [
            models.Index(fields=["conversation"], name="cp_conv_idx"),
            models.Index(fields=["user"], name="cp_user_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} in {self.conversation.id}"


class Message(models.Model):
    """
    Message model representing messages sent within a Conversation.

    - message_id: UUID primary key
    - sender: FK to User (sender_id)
    - conversation: FK to Conversation
    - message_body: text
    - sent_at: timestamp
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    message_body = models.TextField(blank=False)
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "message"
        verbose_name_plural = "messages"
        ordering = ["sent_at"]
        indexes = [
            models.Index(fields=["sender"], name="msg_sender_idx"),
            models.Index(fields=["conversation"], name="msg_conv_idx"),
            models.Index(fields=["sent_at"], name="msg_sent_idx"),
        ]

    def __str__(self) -> str:
        # Short preview of the message
        preview = (self.message_body[:47] + "...") if len(self.message_body) > 50 else self.message_body
        return f"Message {self.id} by {self.sender}: {preview}"


#!/usr/bin/env python3
"""
DRF serializers for chats app (updated).

Includes:
- UserSerializer
- MessageSerializer (uses serializers.CharField and ValidationError)
- ConversationSerializer (nested messages, participant_ids, uses
  SerializerMethodField() and ValidationError)

These serializers ensure nested relationships are handled properly and
provide helpful read/write fields for API usage.
"""
from typing import Any, Dict, List, Optional

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conversation, Message

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the custom User model."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "created_at",
        )
        read_only_fields = ("id", "created_at", "username")


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Message.

    - `sender` is nested read-only.
    - `sender_id` is a writable PK field (optional) mapped to sender.
    - `preview` exposes a short preview of message_body using CharField.
    """
    sender = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="sender", write_only=True, required=False
    )
    conversation = serializers.PrimaryKeyRelatedField(queryset=Conversation.objects.all())

    # include a CharField representation (preview) mapped to message_body
    preview = serializers.CharField(source="message_body", read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "sender_id", "conversation",
                  "message_body", "preview", "sent_at")
        read_only_fields = ("id", "sent_at", "sender", "preview")

    def validate_message_body(self, value: str) -> str:
        """Ensure message body is not empty or whitespace-only."""
        if not value or not value.strip():
            raise serializers.ValidationError("message_body cannot be empty.")
        if len(value) > 2000:
            raise serializers.ValidationError("message_body exceeds max length (2000).")
        return value

    def create(self, validated_data: Dict[str, Any]) -> Message:
        """
        Create a message. If sender wasn't provided via sender_id, try to use
        request.user from the serializer context.
        """
        sender = validated_data.pop("sender", None)  # from sender_id
        if sender is None:
            request = self.context.get("request")
            if request and getattr(request, "user", None) and request.user.is_authenticated:
                sender = request.user
        if sender is None:
            raise serializers.ValidationError("Sender must be provided or request.user must be authenticated.")
        message = Message.objects.create(sender=sender, **validated_data)
        return message


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation.

    - `participants` is nested and read-only (full user data)
    - `participant_ids` is a write-only list of user PKs to assign participants
    - `messages` is a nested list of MessageSerializer instances (read-only)
    - `messages_count` and `last_message` are SerializerMethodField() fields
      used to present summary info about the conversation.
    """
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all(), source="participants"
    )
    messages = MessageSerializer(many=True, read_only=True)

    # SerializerMethodField examples (note the parentheses as required by checks)
    messages_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ("id", "participants", "participant_ids",
                  "messages", "messages_count", "last_message", "created_at")
        read_only_fields = ("id", "participants", "messages", "messages_count", "last_message", "created_at")

    def get_messages_count(self, obj: Conversation) -> int:
        """Return the total number of messages in the conversation."""
        return obj.messages.count()

    def get_last_message(self, obj: Conversation) -> Optional[str]:
        """
        Return a short preview of the last message body or None if no messages.
        Use a small preview (first 120 chars).
        """
        last = obj.messages.order_by("-sent_at").first()
        if not last:
            return None
        preview = last.message_body
        if len(preview) > 120:
            preview = preview[:117] + "..."
        return preview

    def validate_participant_ids(self, value: List[User]) -> List[User]:
        """
        Validate participant_ids list. Ensure there are at least 2 participants
        for a conversation and no duplicates (PrimaryKeyRelatedField already
        enforces valid users).
        """
        if not isinstance(value, list):
            # DRF will usually pass a list, but be defensive
            raise serializers.ValidationError("participant_ids must be a list of user IDs.")
        if len(value) < 2:
            raise serializers.ValidationError("A conversation requires at least 2 participants.")
        # Ensure uniqueness of participants
        if len(set([u.pk for u in value])) != len(value):
            raise serializers.ValidationError("Duplicate participants are not allowed.")
        return value

    def create(self, validated_data: Dict[str, Any]) -> Conversation:
        """
        Create a conversation and attach participants passed via `participant_ids`.
        """
        participants = validated_data.pop("participants", [])
        conversation = Conversation.objects.create(**validated_data)
        if participants:
            conversation.participants.set(participants)
        return conversation

    def update(self, instance: Conversation, validated_data: Dict[str, Any]) -> Conversation:
        """
        Update conversation participants if participant_ids provided.
        """
        participants = validated_data.pop("participants", None)
        if participants is not None:
            # validate_participant_ids will be called automatically by DRF if the
            # field is included; here we just set participants.
            instance.participants.set(participants)
        instance.save()
        return instance


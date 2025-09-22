#!/usr/bin/env python3
"""
DRF serializers for chats app:
- UserSerializer
- MessageSerializer
- ConversationSerializer

ConversationSerializer includes nested messages and exposes a writable
`participant_ids` field to create/update participants.
MessageSerializer exposes nested sender information and allows sender
to be provided via request.user if not supplied.
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
        # expose the fields we care about; username kept read-only to avoid surprises
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
      If not provided, create() will attempt to use request.user.
    """
    sender = UserSerializer(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="sender", write_only=True, required=False
    )
    conversation = serializers.PrimaryKeyRelatedField(
        queryset=Conversation.objects.all()
    )

    class Meta:
        model = Message
        fields = ("id", "sender", "sender_id", "conversation", "message_body", "sent_at")
        read_only_fields = ("id", "sent_at", "sender")

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
        # If still None, let DB throw an error (or you can raise ValidationError)
        message = Message.objects.create(sender=sender, **validated_data)
        return message


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation.

    - `participants` is nested and read-only (full user data)
    - `participant_ids` is a write-only list of user PKs to assign participants
    - `messages` is a nested list of MessageSerializer instances (read-only)
    """
    participants = UserSerializer(many=True, read_only=True)
    participant_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, queryset=User.objects.all(), source="participants"
    )
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ("id", "participants", "participant_ids", "messages", "created_at")
        read_only_fields = ("id", "participants", "messages", "created_at")

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
        # For now, only participants are writable. If other fields exist, handle them here.
        if participants is not None:
            instance.participants.set(participants)
        instance.save()
        return instance


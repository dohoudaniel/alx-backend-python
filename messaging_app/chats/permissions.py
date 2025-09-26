#!/usr/bin/env python3
"""
Custom permission classes for the chats app.

IsParticipantOfConversation enforces:
- only authenticated users can access the API
- only participants of a conversation can view/update/delete that conversation
- only participants can send/view/update/delete messages related to that conversation
"""
from typing import Any, Optional
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from .models import Conversation, Message


class IsParticipantOfConversation(BasePermission):
    """
    Permission that ensures:
    - request.user is authenticated
    - for object-level checks:
      - Conversations: user must be participant
      - Messages: user must be participant of message.conversation (or sender)
    - for create actions on messages: user must be a participant of the provided conversation
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Basic authentication check
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Allow list/retrieve actions — object-level permission will filter results
        # For create actions on messages we need extra validation: ensure user is part of conversation
        action = getattr(view, "action", None)

        # If creating a message, ensure conversation is provided and the user is a participant
        if action == "create" and view.basename in ("message", "conversation-messages"):
            conv_id = request.data.get("conversation")
            if conv_id is None:
                return False
            try:
                conv = Conversation.objects.get(pk=conv_id)
            except Conversation.DoesNotExist:
                return False
            return conv.participants.filter(pk=user.pk).exists()

        # For creating conversations, authenticated user is enough (we add them as participant in view)
        return True

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """
        Object-level permission:
        - If obj is a Conversation: user must be one of its participants.
        - If obj is a Message: user must be a participant of the message's conversation
          or the sender of the message.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Conversation instance check
        if isinstance(obj, Conversation):
            return obj.participants.filter(pk=user.pk).exists()

        # Message instance check
        if isinstance(obj, Message):
            if obj.sender_id == user.pk:
                # allow sender to see/edit their own message
                return True
            return obj.conversation.participants.filter(pk=user.pk).exists()

        # Fallback deny
        return False


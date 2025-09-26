#!/usr/bin/env python3
"""Permissions for chats app."""

from typing import Any
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View
from .models import Conversation, Message


class IsConversationParticipant(BasePermission):
    """
    Object-level permission to allow only participants of a Conversation
    to access it (retrieve, update, delete).
    """

    def has_object_permission(self, request: Request, view: View, obj: Conversation) -> bool:  # type: ignore[override]
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # obj.participants is a M2M; check if current user is included
        return obj.participants.filter(pk=user.pk).exists()

    def has_permission(self, request: Request, view: View) -> bool:
        # For list/create we allow authenticated users (list will be filtered in view)
        return bool(request.user and request.user.is_authenticated)


class IsMessageParticipantOrSender(BasePermission):
    """
    Permission for Message object:
    - Allow message retrieval if the requesting user is a participant of the conversation
      the message belongs to OR is the message sender.
    - For create, ensure the user is a participant of the target conversation.
    """

    def has_object_permission(self, request: Request, view: View, obj: Message) -> bool:  # type: ignore[override]
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Sender can always see their message
        if obj.sender_id == user.pk:
            return True
        # Participants in the conversation can see the message
        return obj.conversation.participants.filter(pk=user.pk).exists()

    def has_permission(self, request: Request, view: View) -> bool:
        """
        For create: validate that conversation provided in payload includes the user.
        For other actions, require authentication and object-level checks will apply.
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if view.action == "create":
            # Ensure a conversation id is provided and the user is a participant
            conv_id = request.data.get("conversation")
            if conv_id is None:
                return False
            try:
                conv = Conversation.objects.get(pk=conv_id)
            except Conversation.DoesNotExist:
                return False
            return conv.participants.filter(pk=user.pk).exists()

        return True


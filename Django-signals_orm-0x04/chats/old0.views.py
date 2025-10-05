#!/usr/bin/env python3
"""
ViewSets for Conversation and Message APIs.

- ConversationViewSet:
    - list: returns conversations the authenticated user participates in
    - retrieve: returns a single conversation with nested messages
    - create: create a conversation with participant_ids; request.user is
              automatically included as a participant if missing.

- MessageViewSet:
    - list: returns messages the authenticated user can see; optional
            query param `conversation=<uuid>` filters by conversation
    - create: create a message in an existing conversation; sender is set
              to request.user. User must be a participant in the conversation.
"""
from typing import Any, Optional
from uuid import UUID

from django.shortcuts import get_object_or_404
from django.db.models import QuerySet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving and creating conversations.

    - list: returns conversations the authenticated user participates in
    - create: create conversation from participant_ids (request body).
              Requesting user is added automatically if not present.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    queryset = Conversation.objects.all().prefetch_related("participants", "messages")

    def get_queryset(self) -> QuerySet[Conversation]:
        """Return conversations where the current user is a participant."""
        user = self.request.user
        if not user or not user.is_authenticated:
            return Conversation.objects.none()
        # Prefetch messages and participants for efficient nested serialization
        return Conversation.objects.filter(participants=user).prefetch_related("participants", "messages")

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a conversation.

        Expected payload (ConversationSerializer):
        {
            "participant_ids": ["<uuid>", "<uuid>", ...]
        }

        Ensures the requesting user is included as a participant.
        """
        data = request.data.copy()
        # Ensure participant_ids exists in payload; if not, initialize to empty
        participant_ids = data.get("participant_ids", [])
        # If participant_ids provided as comma-separated string, normalize
        if isinstance(participant_ids, str):
            participant_ids = [p.strip() for p in participant_ids.split(",") if p.strip()]
            data["participant_ids"] = participant_ids

        # Ensure request.user is included in the participants
        # If participant ids contain UUID strings, include current user's id if not present
        try:
            current_user_pk = str(request.user.pk)
        except Exception:
            current_user_pk = None

        if current_user_pk and current_user_pk not in [str(p) for p in participant_ids]:
            participant_ids = list(participant_ids) + [current_user_pk]
            data["participant_ids"] = participant_ids

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating messages.

    - list: lists messages visible to the authenticated user; supports
            optional ?conversation=<uuid> filtering.
    - create: create a message in a conversation; sender is set to request.user.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    queryset = Message.objects.all().select_related("sender", "conversation")

    def get_queryset(self) -> QuerySet[Message]:
        """Return messages belonging to conversations the user participates in."""
        user = self.request.user
        if not user or not user.is_authenticated:
            return Message.objects.none()

        qs = Message.objects.filter(conversation__participants=user).select_related("sender", "conversation")

        # Optional filter by conversation id via query param
        conversation_id = self.request.query_params.get("conversation")
        if conversation_id:
            try:
                # validate uuid
                _ = UUID(conversation_id)
            except Exception:
                raise ValidationError({"conversation": "Invalid conversation id"})
            qs = qs.filter(conversation__id=conversation_id)
        return qs.order_by("sent_at")

    def perform_create(self, serializer: MessageSerializer) -> None:
        """
        Ensure sender is request.user and that request.user is a participant
        in the conversation before saving.
        """
        request: Request = self.request
        user = request.user
        conversation: Optional[Conversation] = serializer.validated_data.get("conversation") \
            or serializer.initial_data.get("conversation")

        # If conversation was passed as id in initial_data, fetch the instance
        if isinstance(conversation, (str, UUID)):
            conversation = get_object_or_404(Conversation, pk=conversation)

        if conversation is None:
            raise ValidationError({"conversation": "Conversation must be provided."})

        # Check participant membership
        if not conversation.participants.filter(pk=user.pk).exists():
            raise PermissionDenied("You are not a participant of this conversation.")

        # Save with the authenticated user as sender
        serializer.save(sender=user)


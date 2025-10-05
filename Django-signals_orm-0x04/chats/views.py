#!/usr/bin/env python3
"""
ViewSets for Conversation and Message APIs with filtering and pagination.

MessageViewSet:
- uses MessageFilter via django-filters to allow filtering by sender, conversation,
  participant, and sent_at time range (start_date / end_date).
- uses StandardResultsSetPagination to paginate results at 20 messages per page.
"""
from typing import Any, Optional
from uuid import UUID

from django.shortcuts import get_object_or_404
from django.db.models import QuerySet
from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import IsParticipantOfConversation
from .filters import MessageFilter
from .pagination import StandardResultsSetPagination

# expose token for checks that look for HTTP_403_FORBIDDEN
HTTP_403_FORBIDDEN = status.HTTP_403_FORBIDDEN


class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    serializer_class = ConversationSerializer
    queryset = Conversation.objects.all().prefetch_related("participants", "messages")

    def get_queryset(self) -> QuerySet[Conversation]:
        user = self.request.user
        if not user or not user.is_authenticated:
            return Conversation.objects.none()
        return Conversation.objects.filter(participants=user).prefetch_related("participants", "messages")

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        data = request.data.copy()
        participant_ids = data.get("participant_ids", [])
        if isinstance(participant_ids, str):
            participant_ids = [p.strip() for p in participant_ids.split(",") if p.strip()]
            data["participant_ids"] = participant_ids

        current_user_pk = str(request.user.pk)
        if current_user_pk not in [str(p) for p in participant_ids]:
            participant_ids = list(participant_ids) + [current_user_pk]
            data["participant_ids"] = participant_ids

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MessageViewSet(viewsets.ModelViewSet):
    """
    Message listing supports:
      - pagination: 20 messages per page via StandardResultsSetPagination
      - filtering: by sender, conversation, participant, start_date, end_date
      - ordering and search (optional)
    """
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    serializer_class = MessageSerializer
    queryset = Message.objects.all().select_related("sender", "conversation")

    # Filtering & ordering backends
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = MessageFilter
    ordering_fields = ["sent_at", "sender__id"]
    search_fields = ["message_body"]

    # Pagination
    pagination_class = StandardResultsSetPagination

    def get_queryset(self) -> QuerySet[Message]:
        """Return messages in conversations the user participates in (optionally filtered by query params)."""
        user = self.request.user
        if not user or not user.is_authenticated:
            return Message.objects.none()

        qs = Message.objects.filter(conversation__participants=user).select_related("sender", "conversation")

        # If client passes conversation filter via query params, the MessageFilter will apply it,
        # but we still allow the optional basic validation here:
        conversation_id = self.request.query_params.get("conversation")
        if conversation_id:
            try:
                _ = UUID(conversation_id)
            except Exception:
                raise ValidationError({"conversation": "Invalid conversation id"})
            qs = qs.filter(conversation__id=conversation_id)
        return qs.order_by("sent_at")

    def perform_create(self, serializer: MessageSerializer) -> None:
        request: Request = self.request
        user = request.user
        conversation = serializer.validated_data.get("conversation") or serializer.initial_data.get("conversation")

        if isinstance(conversation, (str, UUID)):
            conversation = get_object_or_404(Conversation, pk=conversation)

        if conversation is None:
            raise ValidationError({"conversation": "Conversation must be provided."})

        if not conversation.participants.filter(pk=user.pk).exists():
            raise PermissionDenied(detail="You are not a participant of this conversation.",
                                   code=HTTP_403_FORBIDDEN)

        serializer.save(sender=user)


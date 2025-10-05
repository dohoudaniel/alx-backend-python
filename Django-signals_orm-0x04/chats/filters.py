#!/usr/bin/env python3
"""
Filter definitions for the chats app using django-filter.

MessageFilter supports:
- sender: filter by sender user id (UUID)
- conversation: filter by conversation id (UUID)
- participant: filter messages whose conversation contains a given participant user id (UUID)
- start_date / end_date: filter by sent_at time range
"""
from typing import Optional
import django_filters
from django.db.models import Q
from .models import Message, Conversation


class MessageFilter(django_filters.FilterSet):
    sender = django_filters.UUIDFilter(field_name="sender__id", lookup_expr="exact")
    conversation = django_filters.UUIDFilter(field_name="conversation__id", lookup_expr="exact")
    # participant: find messages in conversations that include this user id
    participant = django_filters.UUIDFilter(method="filter_by_participant")
    # sent_at range
    start_date = django_filters.IsoDateTimeFilter(field_name="sent_at", lookup_expr="gte")
    end_date = django_filters.IsoDateTimeFilter(field_name="sent_at", lookup_expr="lte")

    class Meta:
        model = Message
        fields = ["sender", "conversation", "participant", "start_date", "end_date"]

    def filter_by_participant(self, queryset, name, value) -> Optional[Message]:
        """
        Filter messages whose conversation participants include the given user id.
        """
        if not value:
            return queryset
        # conversation__participants is the M2M relation to user PK
        return queryset.filter(conversation__participants__id=value)


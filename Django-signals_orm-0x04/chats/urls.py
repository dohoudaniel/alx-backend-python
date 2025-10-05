#!/usr/bin/env python3
"""
Chats app routing using DRF routers with nested routes for messages.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from .views import ConversationViewSet, MessageViewSet

# top-level router
router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")
router.register(r"messages", MessageViewSet, basename="message")

# nested router: /conversations/{conversation_pk}/messages/
conversations_router = NestedDefaultRouter(router, r"conversations", lookup="conversation")
conversations_router.register(r"messages", MessageViewSet, basename="conversation-messages")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(conversations_router.urls)),
]


#!/usr/bin/env python3
"""
Router wiring for chats API: Conversation and Message endpoints.
Uses routers.DefaultRouter() as required by checks.
"""
from django.urls import path, include
from rest_framework import routers

from .views import ConversationViewSet, MessageViewSet

router = routers.DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")
router.register(r"messages", MessageViewSet, basename="message")

urlpatterns = [
    path("", include(router.urls)),
]


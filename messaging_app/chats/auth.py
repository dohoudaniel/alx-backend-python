#!/usr/bin/env python3
"""Helpers to create JWT tokens for a user (uses SimpleJWT)."""
from typing import Dict
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()


def get_tokens_for_user(user: User) -> Dict[str, str]:
    """
    Return a dict with 'refresh' and 'access' tokens for the provided user.
    Usage: tokens = get_tokens_for_user(user)
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

#!/usr/bin/env python3
"""
Chat-related middleware.

Contains:
- RequestLoggingMiddleware (if you still want it; kept minimal)
- RestrictAccessByTimeMiddleware: denies access to chat endpoints outside
  configured hours (default: deny between 21:00 and 06:00).

Place "chats.middleware.RestrictAccessByTimeMiddleware" in your
MIDDLEWARE setting (near the top) to enable.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import time
from typing import Callable, Iterable, List

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone


# Optional: simple request logger (kept short — you may already have one)
class RequestLoggingMiddleware:
    """Log each request to a file (configured via settings.REQUESTS_LOG_FILE)."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        log_path = getattr(settings, "REQUESTS_LOG_FILE", None)
        if not log_path:
            base_dir = getattr(settings, "BASE_DIR", None)
            log_path = os.path.join(str(base_dir) if base_dir else ".", "requests.log")

        self.logger = logging.getLogger("request_logger")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            fh = logging.FileHandler(log_path)
            fh.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(fh)
            self.logger.propagate = False

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        user_repr = "Anonymous"
        try:
            if user and getattr(user, "is_authenticated", False):
                user_repr = getattr(user, "username", None) or getattr(user, "email", None) or str(user.pk)
        except Exception:
            user_repr = "Anonymous"
        ts = timezone.now().isoformat(sep=" ", timespec="seconds")
        self.logger.info(f"{ts} - User: {user_repr} - Path: {request.path}")
        return self.get_response(request)


class RestrictAccessByTimeMiddleware:
    """
    Deny access to chat endpoints outside allowed hours.

    Default behaviour:
      - allowed hours: 06:00 (inclusive) .. 21:00 (exclusive)
      - restricted paths: ['/api/messages', '/api/conversations']

    You can customize by adding the following variables to settings.py:
      - CHAT_ACCESS_OPEN_HOUR: int (0-23) default 6
      - CHAT_ACCESS_CLOSE_HOUR: int (0-23) default 21
      - CHAT_RESTRICTED_PATHS: list[str] default ['/api/messages', '/api/conversations']

    The middleware checks server local time (Django timezone aware) via django.utils.timezone.now()
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

        # Configurable hours
        open_hour = getattr(settings, "CHAT_ACCESS_OPEN_HOUR", 6)
        close_hour = getattr(settings, "CHAT_ACCESS_CLOSE_HOUR", 21)

        # Validate hours
        if not (0 <= open_hour <= 23 and 0 <= close_hour <= 23):
            raise ValueError("CHAT_ACCESS_OPEN_HOUR and CHAT_ACCESS_CLOSE_HOUR must be in 0..23")

        self.open_time = time(open_hour, 0, 0)
        self.close_time = time(close_hour, 0, 0)

        # Paths to protect
        default_paths = ["/api/messages", "/api/conversations"]
        self.restricted_paths: List[str] = getattr(settings, "CHAT_RESTRICTED_PATHS", default_paths)

        # Logger
        self.logger = logging.getLogger("chat_time_restriction")
        if not self.logger.handlers:
            # Ensure default handler to avoid "No handlers" warnings
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def _is_path_restricted(self, path: str) -> bool:
        """Return True if the request path should be subject to time restriction."""
        for p in self.restricted_paths:
            if p and p in path:
                return True
        return False

    def _is_within_allowed_hours(self, now_time) -> bool:
        """
        Return True if now_time (a datetime.time) is within allowed range.

        Allowed ranges can wrap midnight. Example:
          open_time = 06:00, close_time = 21:00 -> allowed if 06:00 <= t < 21:00
          open_time = 20:00, close_time = 04:00 -> allowed if (t >= 20:00) or (t < 04:00)
        """
        open_t = self.open_time
        close_t = self.close_time

        if open_t < close_t:
            return open_t <= now_time < close_t
        # wraps midnight
        return now_time >= open_t or now_time < close_t

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Only consider chat endpoints
        if self._is_path_restricted(request.path):
            now = timezone.localtime(timezone.now()).time()
            allowed = self._is_within_allowed_hours(now)
            if not allowed:
                # Deny access
                msg = {
                    "detail": "Chat access is restricted at this time. Please try during allowed hours."
                }
                # Log the denied attempt
                user = getattr(request, "user", None)
                user_repr = "Anonymous"
                try:
                    if user and getattr(user, "is_authenticated", False):
                        user_repr = getattr(user, "username", None) or getattr(user, "email", None) or str(user.pk)
                except Exception:
                    pass
                self.logger.warning("Blocked chat access outside allowed hours - User: %s Path: %s Time: %s",
                                    user_repr, request.path, now.isoformat())
                return JsonResponse(msg, status=403)

        # otherwise proceed normally
        return self.get_response(request)


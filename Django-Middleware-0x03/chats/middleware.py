#!/usr/bin/env python3
"""
Chat middlewares.

Contains:
- RequestLoggingMiddleware: logs requests to a file (optional, kept short)
- RestrictAccessByTimeMiddleware: blocks chat endpoints outside allowed hours
- OffensiveLanguageMiddleware: rate-limits POSTs to message endpoints per IP
  (implements a sliding time window, e.g. max 5 messages per 60 seconds)

To enable the rate-limit middleware, add the path
"chats.middleware.OffensiveLanguageMiddleware" to MIDDLEWARE in settings.py.

Configuration (optional, add to settings.py):
- CHAT_RATE_LIMIT_MAX_MESSAGES: int (default 5)
- CHAT_RATE_LIMIT_WINDOW_SECONDS: int (default 60)
- CHAT_RATE_LIMIT_PATHS: list[str] (default ['/api/messages'])
"""
from __future__ import annotations

import logging
import os
import threading
from collections import deque
from datetime import time
from typing import Callable, Deque, Dict, Iterable, List

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone


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
        if not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
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
        try:
            self.logger.info(f"{ts} - User: {user_repr} - Path: {request.path}")
        except Exception:
            # never break the request on logging failure
            pass
        return self.get_response(request)


class RestrictAccessByTimeMiddleware:
    """
    Deny access to chat endpoints outside allowed hours.

    Default behaviour:
      - allowed hours: 06:00 (inclusive) .. 21:00 (exclusive)
      - restricted paths: ['/api/messages', '/api/conversations']

    Config via settings:
      CHAT_ACCESS_OPEN_HOUR, CHAT_ACCESS_CLOSE_HOUR, CHAT_RESTRICTED_PATHS
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

        open_hour = getattr(settings, "CHAT_ACCESS_OPEN_HOUR", 6)
        close_hour = getattr(settings, "CHAT_ACCESS_CLOSE_HOUR", 21)
        if not (0 <= open_hour <= 23 and 0 <= close_hour <= 23):
            raise ValueError("CHAT_ACCESS_OPEN_HOUR and CHAT_ACCESS_CLOSE_HOUR must be in 0..23")

        self.open_time = time(open_hour, 0, 0)
        self.close_time = time(close_hour, 0, 0)
        default_paths = ["/api/messages", "/api/conversations"]
        self.restricted_paths: List[str] = getattr(settings, "CHAT_RESTRICTED_PATHS", default_paths)

        self.logger = logging.getLogger("chat_time_restriction")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def _is_path_restricted(self, path: str) -> bool:
        for p in self.restricted_paths:
            if p and p in path:
                return True
        return False

    def _is_within_allowed_hours(self, now_time) -> bool:
        open_t = self.open_time
        close_t = self.close_time
        if open_t < close_t:
            return open_t <= now_time < close_t
        return now_time >= open_t or now_time < close_t

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if self._is_path_restricted(request.path):
            now = timezone.localtime(timezone.now()).time()
            allowed = self._is_within_allowed_hours(now)
            if not allowed:
                user = getattr(request, "user", None)
                user_repr = "Anonymous"
                try:
                    if user and getattr(user, "is_authenticated", False):
                        user_repr = getattr(user, "username", None) or getattr(user, "email", None) or str(user.pk)
                except Exception:
                    pass
                self.logger.warning(
                    "Blocked chat access outside allowed hours - User: %s Path: %s Time: %s",
                    user_repr, request.path, now.isoformat()
                )
                return JsonResponse(
                    {"detail": "Chat access is restricted at this time. Please try during allowed hours."},
                    status=403,
                )
        return self.get_response(request)


class OffensiveLanguageMiddleware:
    """
    Rate-limit POST requests to message endpoints by IP address (sliding window).

    Default policy:
      - MAX_MESSAGES_PER_WINDOW = 5
      - WINDOW_SECONDS = 60
      - TARGET_PATHS = ['/api/messages']

    Configurable via settings:
      CHAT_RATE_LIMIT_MAX_MESSAGES
      CHAT_RATE_LIMIT_WINDOW_SECONDS
      CHAT_RATE_LIMIT_PATHS

    NOTE:
      - This implementation uses an in-memory store (process-local). For multi-process
        deployments consider using Redis or another centralized store.
      - The middleware counts POST requests only (typical message create action).
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.max_messages: int = getattr(settings, "CHAT_RATE_LIMIT_MAX_MESSAGES", 5)
        self.window_seconds: int = getattr(settings, "CHAT_RATE_LIMIT_WINDOW_SECONDS", 60)
        default_paths = ["/api/messages"]
        self.target_paths: List[str] = getattr(settings, "CHAT_RATE_LIMIT_PATHS", default_paths)

        # Map ip -> deque[timestamp_float]
        self._requests: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

        # Logger
        self.logger = logging.getLogger("chat_rate_limiter")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def _is_target_path(self, path: str) -> bool:
        for p in self.target_paths:
            if p and p in path:
                return True
        return False

    def _get_client_ip(self, request: HttpRequest) -> str:
        # Respect X-Forwarded-For if present (first entry is original client IP)
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            # X-Forwarded-For can be a comma-separated list
            parts = [p.strip() for p in xff.split(",") if p.strip()]
            if parts:
                return parts[0]
        # Fallback to REMOTE_ADDR
        return request.META.get("REMOTE_ADDR", "unknown")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            # Only count POST requests to the configured message endpoints
            if request.method.upper() == "POST" and self._is_target_path(request.path):
                ip = self._get_client_ip(request)
                now_ts = timezone.now().timestamp()

                with self._lock:
                    dq = self._requests.get(ip)
                    if dq is None:
                        dq = deque()
                        self._requests[ip] = dq

                    # Remove timestamps older than window
                    cutoff = now_ts - float(self.window_seconds)
                    while dq and dq[0] < cutoff:
                        dq.popleft()

                    if len(dq) >= self.max_messages:
                        # Rate limit exceeded
                        self.logger.warning(
                            "Rate limit exceeded for IP %s on path %s: %d in %d seconds",
                            ip, request.path, len(dq), self.window_seconds
                        )
                        return JsonResponse(
                            {"detail": "Rate limit exceeded. Try again later."},
                            status=429,
                        )

                    # Record this request
                    dq.append(now_ts)

                    # Optional cleanup: if deque becomes empty remove key (not needed here)
                    if not dq:
                        # If dq empty after trimming (unlikely immediately), remove mapping
                        self._requests.pop(ip, None)

        except Exception as exc:
            # Never break application due to middleware failure; log and proceed
            try:
                self.logger.exception("Error in OffensiveLanguageMiddleware: %s", exc)
            except Exception:
                pass

        return self.get_response(request)

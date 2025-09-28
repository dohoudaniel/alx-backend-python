#!/usr/bin/env python3
"""
Request logging middleware.

Logs each incoming request to a file with the format:
    "{datetime.now()} - User: {user} - Path: {request.path}"
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class RequestLoggingMiddleware:
    """
    Middleware that logs each request with timestamp, user and path.

    Configure the destination file via settings.REQUESTS_LOG_FILE (optional).
    If not set, it will default to <BASE_DIR>/requests.log.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

        # Determine log file path
        base_dir = getattr(settings, "BASE_DIR", None)
        default_filename = "requests.log"
        if getattr(settings, "REQUESTS_LOG_FILE", None):
            log_path = settings.REQUESTS_LOG_FILE
        elif base_dir:
            # settings.BASE_DIR may be a pathlib.Path — convert if needed
            log_path = os.path.join(str(base_dir), default_filename)
        else:
            # fallback to current working directory
            log_path = os.path.join(os.getcwd(), default_filename)

        # Create logger
        self.logger = logging.getLogger("request_logger")
        self.logger.setLevel(logging.INFO)
        # Avoid adding duplicate handlers on reloads (e.g. runserver auto-reload)
        if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == os.path.abspath(log_path)
                   for h in self.logger.handlers):
            # Ensure directory exists
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            fh = logging.FileHandler(log_path)
            formatter = logging.Formatter("%(message)s")
            fh.setFormatter(formatter)
            self.logger.addHandler(fh)
            # prevent the message being passed to the root logger
            self.logger.propagate = False

        # store path for debugging if needed
        self.log_path = log_path

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Resolve user display
        user = getattr(request, "user", None)
        if user is None:
            user_repr = "Anonymous"
        else:
            try:
                if user.is_authenticated:
                    # Prefer username or email or pk for readability
                    user_repr = getattr(user, "username", None) or getattr(user, "email", None) or str(user.pk)
                else:
                    user_repr = "Anonymous"
            except Exception:
                user_repr = "Anonymous"

        # Build log line and write
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        log_line = f"{ts} - User: {user_repr} - Path: {request.path}"
        try:
            self.logger.info(log_line)
        except Exception:
            # don't break request on logging failure
            pass

        # Continue processing the request
        response = self.get_response(request)
        return response


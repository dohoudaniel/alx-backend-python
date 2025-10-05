#!/usr/bin/env python3
# (other imports already in your file)
from typing import Callable, List
import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse


class RolepermissionMiddleware:
    """
    Middleware to enforce role-based permissions for chat operations.

    Default behaviour:
      - Apply check only to state-changing HTTP methods:
        POST, PUT, PATCH, DELETE
      - Check only on paths that contain one of CHAT_ROLE_PROTECTED_PATHS
        (default: ['/api/messages', '/api/conversations'])
      - Allowed roles default to CHAT_ROLE_ALLOWED = ['admin', 'moderator']

    Users who are staff or superuser bypass checks.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        # Methods that imply modification and thus require role checks
        self._protected_methods = {"POST", "PUT", "PATCH", "DELETE"}

        # allowed roles and protected paths are configurable in settings.py
        self.allowed_roles: List[str] = [
            r.lower() for r in getattr(settings, "CHAT_ROLE_ALLOWED", ["admin", "moderator"])
        ]
        self.protected_paths: List[str] = getattr(
            settings,
            "CHAT_ROLE_PROTECTED_PATHS",
            ["/api/messages", "/api/conversations"],
        )

        self.logger = logging.getLogger("chat_role_permission")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            self.logger.addHandler(handler)
            self.logger.propagate = False

    def _is_protected_path(self, path: str) -> bool:
        """Return True if the request path should be checked for role permissions."""
        for p in self.protected_paths:
            if p and p in path:
                return True
        return False

    def _user_has_allowed_role(self, user) -> bool:
        """Check if user has one of the allowed roles or is staff/superuser."""
        if not user:
            return False
        try:
            # Staff/superuser always allowed
            if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
                return True
            # try to read role attribute (case-insensitive)
            role = getattr(user, "role", None)
            if role is None:
                # maybe username-based admin flag: allow if user.is_staff handled above
                return False
            return str(role).lower() in self.allowed_roles
        except Exception:
            # on unexpected error, deny by default (safer)
            return False

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # only enforce on protected methods and protected paths
        method = request.method.upper()
        path = request.path or ""

        if method in self._protected_methods and self._is_protected_path(path):
            user = getattr(request, "user", None)

            # If not authenticated -> 403 (settings may already block anonymous earlier)
            if user is None or not getattr(user, "is_authenticated", False):
                self.logger.info("RolepermissionMiddleware: Anonymous or unauthenticated blocked for %s %s", method, path)
                return JsonResponse({"detail": "Forbidden: authentication required"}, status=403)

            # Check role
            if not self._user_has_allowed_role(user):
                # Log denied attempt and return 403
                uname = getattr(user, "username", None) or getattr(user, "email", None) or str(getattr(user, "pk", "unknown"))
                self.logger.warning("RolepermissionMiddleware: User %s denied %s %s (role=%s)", uname, method, path, getattr(user, "role", None))
                return JsonResponse({"detail": "Forbidden: role not permitted to perform this action"}, status=403)

        # otherwise allow request to proceed
        return self.get_response(request)


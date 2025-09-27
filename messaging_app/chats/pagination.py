#!/usr/bin/env python3
"""
Pagination classes for the chats app.
StandardResultsSetPagination enforces 20 items per page by default.
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination: 20 items per page by default.
    Clients may use ?page=<n> to navigate.
    """
    page_size = 20
    page_size_query_param = "page_size"  # optional: allow client to override up to max_page_size
    max_page_size = 100


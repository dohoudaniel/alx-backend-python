# File: 2-lazy_paginate.py
"""
Lazy pagination generator for user_data.

Provides:
- paginate_users(page_size, offset): helper that fetches one page from DB
- lazy_pagination(page_size): generator that yields pages (lists of dicts)
  fetched only when requested (lazy). This function uses exactly one loop.

Compatibility:
- Exposes both `lazy_pagination` and `lazy_paginate` names (alias) so it works
  with different prototype expectations.
"""

import os
import seed  # expects seed.connect_to_prodev() to be available


def paginate_users(page_size: int, offset: int):
    """
    Fetch a single page of rows from the user_data table.
    Returns a list of dict rows (empty list if none).
    """
    conn = None
    cursor = None
    try:
        conn = seed.connect_to_prodev()
        cursor = conn.cursor(dictionary=True)
        # Use parameterized query to avoid injection
        cursor.execute("SELECT user_id, name, email, age FROM user_data LIMIT %s OFFSET %s", (page_size, offset))
        rows = cursor.fetchall()
        return rows
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def lazy_pagination(page_size: int):
    """
    Generator that lazily fetches pages of users from the DB.
    Yields lists of rows (each row is a dict).
    Uses only one loop (while True) internally.
    """
    offset = 0

    # Single loop requirement: use only this while loop to fetch successive pages
    while True:
        page = paginate_users(page_size, offset)
        if not page:
            break
        yield page
        offset += page_size


# Provide alternate name to match different expected prototypes
lazy_paginate = lazy_pagination

#!/usr/bin/env python3
"""
File: 3-concurrent.py

Run multiple database queries concurrently using aiosqlite and asyncio.gather.

Requirements satisfied:
- Uses aiosqlite for async SQLite access
- Defines `async def async_fetch_users()` and `async def async_fetch_older_users()`
- Uses `asyncio.gather()` to run both concurrently
- Calls `asyncio.run(fetch_concurrently())` in the main guard
"""

import asyncio
import sqlite3
from typing import List, Dict, Any
import aiosqlite


async def async_fetch_users(db_path: str = "users.db") -> List[Dict[str, Any]]:
    """
    Asynchronously fetch all users from the `users` table.
    Returns a list of dicts.
    """
    results: List[Dict[str, Any]] = []
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        async with db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            for r in rows:
                results.append(dict(r))
    return results


async def async_fetch_older_users(db_path: str = "users.db", age_threshold: int = 40) -> List[Dict[str, Any]]:
    """
    Asynchronously fetch users older than `age_threshold`.
    Returns a list of dicts.
    """
    results: List[Dict[str, Any]] = []
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        async with db.execute("SELECT * FROM users WHERE age > ?", (age_threshold,)) as cursor:
            rows = await cursor.fetchall()
            for r in rows:
                results.append(dict(r))
    return results


async def fetch_concurrently() -> None:
    """
    Execute async_fetch_users() and async_fetch_older_users() concurrently
    with asyncio.gather(), then print summary and sample results.
    """
    # schedule both coroutines and run them concurrently
    all_users_coro = async_fetch_users()
    older_users_coro = async_fetch_older_users()

    all_users, older_users = await asyncio.gather(all_users_coro, older_users_coro)

    print(f"Total users fetched: {len(all_users)}")
    print(f"Users older than 40: {len(older_users)}\n")

    print("Sample users (up to 5):")
    for u in all_users[:5]:
        print(u)
    print("\nSample older users (up to 5):")
    for u in older_users[:5]:
        print(u)


if __name__ == "__main__":
    try:
        asyncio.run(fetch_concurrently())
    except Exception as e:
        print("Error running concurrent queries:", e)
        print("Make sure you have a 'users.db' SQLite file with a 'users' table.")

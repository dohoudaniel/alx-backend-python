#!/usr/bin/env python3
"""
Run concurrent asynchronous SQLite queries using aiosqlite and asyncio.gather.

- async_fetch_users(): fetch all users
- async_fetch_older_users(): fetch users with age > 40
- fetch_concurrently(): runs both concurrently and prints results
"""

import asyncio
import sqlite3
from typing import List, Dict, Any

import aiosqlite


async def async_fetch_users(db_path: str = "users.db") -> List[Dict[str, Any]]:
    """
    Fetch all users asynchronously.
    Returns a list of dict-like rows (converted to plain dicts).
    """
    rows_out = []
    # aiosqlite supports async context manager for connection
    async with aiosqlite.connect(db_path) as db:
        # set row factory to sqlite3.Row so we can convert to dict
        db.row_factory = sqlite3.Row
        async with db.execute("SELECT * FROM users") as cursor:
            rows = await cursor.fetchall()
            for r in rows:
                # convert sqlite3.Row to plain dict
                rows_out.append(dict(r))
    return rows_out


async def async_fetch_older_users(db_path: str = "users.db", age_threshold: int = 40) -> List[Dict[str, Any]]:
    """
    Fetch users older than `age_threshold` asynchronously.
    Returns a list of dict-like rows (converted to plain dicts).
    """
    rows_out = []
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        # parameterized query to avoid injection
        async with db.execute("SELECT * FROM users WHERE age > ?", (age_threshold,)) as cursor:
            rows = await cursor.fetchall()
            for r in rows:
                rows_out.append(dict(r))
    return rows_out


async def fetch_concurrently():
    """
    Run async_fetch_users() and async_fetch_older_users() concurrently using asyncio.gather,
    then print summary information about the results.
    """
    # run both coroutines concurrently
    all_users_task = async_fetch_users()
    older_users_task = async_fetch_older_users(age_threshold=40)

    all_users, older_users = await asyncio.gather(all_users_task, older_users_task)

    print(f"Total users fetched: {len(all_users)}")
    print(f"Users older than 40: {len(older_users)}\n")

    # Print sample outputs (up to 5 users each)
    print("Sample users (up to 5):")
    for user in all_users[:5]:
        print(user)
    print("\nSample older users (up to 5):")
    for user in older_users[:5]:
        print(user)


if __name__ == "__main__":
    # Run the concurrent fetch
    try:
        asyncio.run(fetch_concurrently())
    except Exception as e:
        print("Error running asynchronous queries:", e)
        print("Ensure 'users.db' exists and has a 'users' table.")

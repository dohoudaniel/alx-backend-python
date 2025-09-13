#!/usr/bin/env python3
"""
Class-based context manager `DatabaseConnection` that opens a sqlite3 connection
on enter and ensures it is closed on exit. Demonstrates usage by performing
a SELECT * FROM users and printing the results.

"""

import sqlite3
from typing import Optional


class DatabaseConnection:
    """
    Class-based context manager for sqlite3 connections.

    Usage:
        with DatabaseConnection(db_path) as conn:
            cur = conn.cursor()
            cur.execute(...)
    """

    def __init__(self, db_path: str = "users.db") -> None:
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> sqlite3.Connection:
        # Open connection and set row factory for convenient row access
        self.conn = sqlite3.connect(self.db_path)
        # Return rows as sqlite3.Row so they behave like dicts
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        # Always ensure connection is closed
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception:
            pass
        # Return False so that exceptions (if any) propagate normally
        return False


if __name__ == "__main__":
    # Demo: use the context manager to query the users table and print rows
    try:
        with DatabaseConnection("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users;")
            rows = cursor.fetchall()
            # Print rows in a readable format
            for row in rows:
                # sqlite3.Row supports mapping-like access
                print(dict(row))
            cursor.close()
    except sqlite3.OperationalError as e:
        print("OperationalError:", e)
        print("Ensure 'users.db' exists and has a 'users' table with data.")
    except Exception as e:
        print("Error:", e)

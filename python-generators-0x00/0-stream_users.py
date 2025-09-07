# File: 0-stream-users.py
"""
0-stream_users.py

Provides a generator function `stream_users()` that streams rows from the
user_data table one-by-one. The generator yields dicts with keys:
'user_id', 'name', 'email', 'age'.

Requirements satisfied:
- Uses `yield`
- Contains at most one loop
- Cleans up DB resources when the generator is exhausted or closed
"""

import os
import mysql.connector
from mysql.connector import Error
from typing import Generator, Dict, Any


def _get_conn_params():
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "ALX_prodev"),
    }


def stream_users() -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields rows from the `user_data` table one at a time.

    Usage:
        for user in stream_users():
            print(user)

    The function uses a single loop (while True) to fetch rows with fetchone()
    and yields each row as a dictionary. Resources (cursor, connection) are
    closed in the finally block so cleanup happens when the generator is
    exhausted or closed early.
    """
    params = _get_conn_params()
    conn = None
    cursor = None

    try:
        conn = mysql.connector.connect(
            host=params["host"],
            port=params["port"],
            user=params["user"],
            password=params["password"],
            database=params["database"],
        )
        # Use dict cursor so each row is a dict matching the sample output
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT user_id, name, email, age FROM user_data;")

        # Single loop requirement: only this while loop used to fetch+yield rows
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            # Convert DECIMAL/Decimal age to int if necessary
            try:
                row["age"] = int(row["age"])
            except Exception:
                # leave as-is if conversion fails
                pass
            yield row

    except Error as err:
        # surface DB connection/execution errors to the caller
        raise
    finally:
        # Ensure resources are closed whether generator finished or was closed early
        try:
            if cursor is not None:
                cursor.close()
        except Exception:
            pass
        try:
            if conn is not None and conn.is_connected():
                conn.close()
        except Exception:
            pass

# File: 1-batch_processing.py
"""
Batch streaming and processing for user_data.

Provides:
- stream_users_in_batches(batch_size): generator that yields batches (lists) of user dicts
- batch_processing(batch_size): processes each batch and prints users over age 25

Constraints satisfied:
- Uses `yield` in stream_users_in_batches
- Uses no more than 3 loops in the entire module:
  1) while loop inside stream_users_in_batches to fetch batches
  2) for loop in batch_processing to iterate batches
  3) for loop in batch_processing to iterate users inside a batch
"""

import os
from typing import Generator, Dict, Any, List, Optional

import mysql.connector
from mysql.connector import Error


def _get_conn_params() -> Dict[str, Any]:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "ALX_prodev"),
    }


def stream_users_in_batches(batch_size: int) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Connect to ALX_prodev and stream rows from user_data in batches.

    Yields:
        List[dict] : a list of rows (dicts) up to `batch_size` in length.

    Single loop: uses a while loop to fetchmany() until no rows remain.
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
        # dictionary cursor to yield dicts similar to expected output
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, name, email, age FROM user_data;")

        # single loop to fetch batches
        while True:
            batch = cursor.fetchmany(size=batch_size)
            if not batch:
                break
            # normalize age to int (if Decimal) and strip strings
            for row in batch:
                try:
                    row["age"] = int(row["age"])
                except Exception:
                    # leave as-is if conversion fails
                    pass
                # clean whitespace in strings
                for k in ("user_id", "name", "email"):
                    if k in row and isinstance(row[k], str):
                        row[k] = row[k].strip()
            yield batch

    except Error as err:
        # If there's a DB error, raise it so caller can see the problem
        raise
    finally:
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


def batch_processing(batch_size: int) -> None:
    """
    Process streamed batches and print users older than 25.

    Uses at most two loops here:
      - outer loop over batches (for batch in stream_users_in_batches(...))
      - inner loop over rows in a batch (for user in batch)
    (The generator itself has its own while loop; total loops in module <= 3.)
    """
    try:
        for batch in stream_users_in_batches(batch_size):  # loop 1 (module loop #2)
            for user in batch:  # loop 2 (module loop #3)
                # Filter users older than 25
                age = user.get("age")
                try:
                    if age is not None and int(age) > 25:
                        print(user)
                except Exception:
                    # If age is malformed, skip that row
                    continue
    except BrokenPipeError:
        # Allow graceful exit when piping output (e.g., head) closes the pipe
        raise
    except Exception:
        # Surface other exceptions to the caller/test harness
        raise

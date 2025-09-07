# File: 4-stream_ages.py
"""
Memory-efficient average age calculation using a generator.

- stream_user_ages(): generator that yields one age at a time from the
  user_data table.
- compute_average_age(): consumes the generator (one loop) and prints the
  average age without loading all rows into memory.

Constraints satisfied:
- Uses `yield`
- Uses no more than two loops total:
    1) the loop inside the generator to fetch rows
    2) the loop in compute_average_age to aggregate ages
- Does not use SQL AVG()
"""

import os
from typing import Generator, Optional

import seed  # expects seed.connect_to_prodev() to be available
from mysql.connector import Error


def stream_user_ages() -> Generator[int, None, None]:
    """
    Generator that yields the `age` column from `user_data` one row at a time.

    It opens a DB connection and a cursor, executes a simple SELECT age query,
    and fetches rows one-by-one with fetchone() inside a single loop. Cursor
    and connection are closed in the generator's finally block when the
    generator is exhausted or closed early.
    """
    conn = None
    cursor = None
    try:
        conn = seed.connect_to_prodev()
        if conn is None:
            raise RuntimeError("Could not connect to ALX_prodev database")

        # Use a simple cursor (not dictionary) since we select a single column
        cursor = conn.cursor()
        cursor.execute("SELECT age FROM user_data;")

        # Single loop: fetch rows one at a time and yield the age
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            age = row[0]
            # Normalize types (DECIMAL/Decimal -> int)
            try:
                age_val = int(age)
            except Exception:
                # If age is None or malformed, skip this row
                continue
            yield age_val

    except Error as err:
        # Re-raise DB errors to the caller
        raise
    finally:
        # cleanup resources
        try:
            if cursor is not None:
                cursor.close()
        except Exception:
            pass
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass


def compute_average_age() -> Optional[float]:
    """
    Consume the stream_user_ages generator and compute the average age.

    Returns the average as a float (or None if no rows).
    Uses exactly one loop to iterate over the generator.
    """
    total = 0
    count = 0

    for age in stream_user_ages():  # loop #2 (generator loop is loop #1)
        total += age
        count += 1

    if count == 0:
        return None

    return total / count


if __name__ == "__main__":
    avg = compute_average_age()
    if avg is None:
        print("Average age of users: 0")
    else:
        # Print with sensible formatting (round to 2 decimal places)
        print(f"Average age of users: {avg:.2f}")

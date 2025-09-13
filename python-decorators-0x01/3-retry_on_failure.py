import time
import sqlite3
import functools

# --------------------------
# with_db_connection decorator
# --------------------------
def with_db_connection(func):
    """
    Opens a sqlite3 connection to 'users.db', passes it as the first positional
    argument to the wrapped function, and ensures the connection is closed
    afterwards.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = sqlite3.connect('users.db')
            return func(conn, *args, **kwargs)
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
    return wrapper

# --------------------------
# retry_on_failure decorator
# --------------------------
def retry_on_failure(retries: int = 3, delay: float = 2.0):
    """
    Decorator factory that returns a decorator which retries the wrapped function
    up to `retries` times (total attempts = retries), waiting `delay` seconds
    between attempts if an exception is raised.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    attempt += 1
                    if attempt >= retries:
                        # Exhausted attempts — re-raise the last exception
                        raise
                    # Wait and retry
                    time.sleep(delay)
        return wrapper
    return decorator

# --------------------------
# Example usage
# --------------------------
@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows
    finally:
        try:
            cursor.close()
        except Exception:
            pass

# Attempt to fetch users with automatic retry on failure
if __name__ == "__main__":
    try:
        users = fetch_users_with_retry()
        print(users)
    except Exception as e:
        print(f"Failed to fetch users after retries: {e}")

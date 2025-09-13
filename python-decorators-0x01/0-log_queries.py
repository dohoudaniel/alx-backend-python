# 0-log_queries.py
import sqlite3
import functools
from typing import Callable, Any

def log_queries(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator that logs the SQL query string (and optional params) before
    calling the wrapped function.

    It looks for the SQL in:
      - keyword arg named 'query'
      - first positional argument if it's a str
      - first positional arg as (query, params) tuple/list

    Usage:
      @log_queries
      def fetch_all_users(query): ...
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        query = kwargs.get("query", None)
        params = kwargs.get("params", None)

        # If query not in kwargs, check first positional arg
        if query is None and args:
            first = args[0]
            if isinstance(first, str):
                query = first
            elif isinstance(first, (tuple, list)) and len(first) >= 1 and isinstance(first[0], str):
                query = first[0]
                if len(first) > 1:
                    params = first[1]

        # Log query (and params if available)
        if query is not None:
            if params is not None:
                print(f"[SQL] Query: {query} -- params: {params}")
            else:
                print(f"[SQL] Query: {query}")
        else:
            print(f"[SQL] Calling {func.__name__}() (no query argument detected)")

        return func(*args, **kwargs)

    return wrapper


# Example usage (kept in the file for demonstration; tests will import and run their own functions)
@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


if __name__ == "__main__":
    # Demo run (won't run during unit tests but is helpful locally)
    try:
        users = fetch_all_users(query="SELECT * FROM users")
        print(users)
    except Exception:
        # If DB/file doesn't exist locally, ignore demo errors
        pass

import sqlite3
import functools
from typing import Callable, Any

#### decorator to log SQL queries
def log_queries() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator factory that returns a decorator which logs the SQL query string
    (and optional params) before calling the wrapped function.

    The wrapped function is expected to accept either:
      - a positional first argument that is the SQL query (string), or
      - a keyword argument named 'query' containing the SQL string.

    If a 'params' kwarg is present it will also be printed.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # try to find SQL query in kwargs or first positional arg
            query = kwargs.get("query", None)
            params = kwargs.get("params", None)

            if query is None and args:
                # if first positional arg is a string, treat it as query
                first = args[0]
                if isinstance(first, str):
                    query = first
                # if first is tuple/list like (query, params) handle that too
                elif isinstance(first, (tuple, list)) and len(first) >= 1 and isinstance(first[0], str):
                    query = first[0]
                    if len(first) > 1:
                        params = first[1]

            # Log the query (and params if present)
            if query is not None:
                if params:
                    print(f"[SQL] Query: {query} -- params: {params}")
                else:
                    print(f"[SQL] Query: {query}")
            else:
                # fallback message if no query found in args/kwargs
                print(f"[SQL] Calling {func.__name__}() (no query argument detected)")

            # execute the wrapped function
            return func(*args, **kwargs)

        return wrapper
    return decorator

# Use the decorator (note: decorator is a factory so call it)
@log_queries()
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

#### fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")
print(users)

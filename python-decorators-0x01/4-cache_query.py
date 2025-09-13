import time
import sqlite3
import functools

# Simple in-memory cache: maps SQL string -> result
# (You can extend this to include params and TTL if needed)
query_cache = {}


def with_db_connection(func):
    """
    Simple connection handler decorator for sqlite (users.db).
    Passes the open connection as the first positional argument to the wrapped function.
    Ensures connection is closed after the wrapped function finishes.
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


def cache_query(func):
    """
    Decorator that caches results of a DB query based on the SQL query string.
    The wrapped function is expected to accept a `query` keyword argument or the
    SQL string as its first positional argument (after `conn` if using with_db_connection).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Determine the SQL string from kwargs or positional args
        sql = kwargs.get("query", None)
        params = kwargs.get("params", None)

        if sql is None:
            # If the function is used with with_db_connection, the first arg is conn,
            # so the SQL would be the second positional arg. Otherwise it's the first.
            pos_args = list(args)
            if len(pos_args) >= 2:
                # assume (conn, query, ...)
                candidate = pos_args[1]
                if isinstance(candidate, str):
                    sql = candidate
            elif len(pos_args) == 1:
                # assume (query,)
                candidate = pos_args[0]
                if isinstance(candidate, str):
                    sql = candidate

        # Build a cache key that includes params if provided (to distinguish queries)
        if sql is None:
            # fallback: cannot cache if no SQL string detected
            return func(*args, **kwargs)

        key = (sql, tuple(params) if isinstance(params, (list, tuple)) else params)

        # Check cache
        if key in query_cache:
            # cache hit
            # Return a shallow copy to avoid accidental mutation by caller
            cached = query_cache[key]
            # Optionally print a debug message
            print("[CACHE] HIT for query")
            # If rows are sqlite3.Row objects, convert to tuples/lists for safe reuse
            try:
                # attempt to deep-copy simple structures; if not, return as-is
                return [tuple(r) if hasattr(r, '__iter__') and not isinstance(r, (str, bytes)) else r
                        for r in cached]
            except Exception:
                return cached

        # Cache miss -> execute the function and store result
        result = func(*args, **kwargs)

        # Normalize result to a cacheable form (convert sqlite3.Row to tuple)
        try:
            normalized = [tuple(row) if hasattr(row, '__iter__') and not isinstance(row, (str, bytes)) else row
                          for row in result]
        except Exception:
            normalized = result

        query_cache[key] = normalized
        print("[CACHE] STORED for query")
        return result

    return wrapper


# Example usage
@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query, params=None):
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    finally:
        try:
            cursor.close()
        except Exception:
            pass


if __name__ == "__main__":
    # First call will execute and cache
    users = fetch_users_with_cache(query="SELECT * FROM users")
    print("First call, rows:", len(users) if users is not None else 0)

    # Second call should hit the cache
    users_again = fetch_users_with_cache(query="SELECT * FROM users")
    print("Second call, rows:", len(users_again) if users_again is not None else 0)

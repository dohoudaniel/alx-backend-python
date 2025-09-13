import sqlite3
import functools

def with_db_connection(func):
    """
    Decorator that opens a sqlite3 connection, passes it as the first positional
    argument to the wrapped function, and ensures the connection is closed
    afterwards (even if an exception occurs).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            # open connection (file DB named 'users.db' as in the example)
            conn = sqlite3.connect('users.db')
            # pass the connection as the first positional argument to the function
            return func(conn, *args, **kwargs)
        finally:
            # ensure the connection is closed
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
    return wrapper

@with_db_connection 
def get_user_by_id(conn, user_id): 
    cursor = conn.cursor() 
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)) 
    row = cursor.fetchone()
    cursor.close()
    return row

#### Fetch user by ID with automatic connection handling 
if __name__ == "__main__":
    user = get_user_by_id(user_id=1)
    print(user)

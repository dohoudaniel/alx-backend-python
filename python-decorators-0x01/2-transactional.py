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


def transactional(func):
    """
    Decorator that wraps a DB operation in a transaction. It expects that a
    sqlite3.Connection will be passed to the wrapped function either as the
    first positional argument or as keyword 'conn'. On success commit;
    on exception rollback and re-raise.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # try to find connection in kwargs or first positional arg
        conn = kwargs.get('conn', None)
        if conn is None and len(args) > 0:
            conn = args[0]

        if conn is None or not isinstance(conn, sqlite3.Connection):
            # No connection available — raise an informative error
            raise RuntimeError("transactional decorator requires a sqlite3.Connection "
                               "passed as first arg or 'conn' kwarg")

        try:
            result = func(*args, **kwargs)
            conn.commit()
            return result
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                # if rollback fails, we don't want to mask the original exception
                pass
            raise
    return wrapper


@with_db_connection
@transactional
def update_user_email(conn, user_id, new_email):
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))
    cursor.close()


#### Update user's email with automatic transaction handling
if __name__ == "__main__":
    # Example call: with_db_connection will inject conn, transactional will commit/rollback
    update_user_email(user_id=1, new_email='Crawford_Cartwright@hotmail.com')
    print("update_user_email executed")

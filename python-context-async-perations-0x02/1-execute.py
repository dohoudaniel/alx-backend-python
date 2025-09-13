#!/usr/bin/env python3
"""
Class-based context manager `ExecuteQuery` that opens a sqlite3 connection,
executes a provided query with parameters on enter, and ensures cleanup on exit.

This implements the requirement:
- Takes the query "SELECT * FROM users WHERE age > ?" and parameter (25,)
- Executes the query and returns the results in the context manager
"""

import sqlite3
from typing import Any, Iterable, List, Optional, Tuple


class ExecuteQuery:
    """
    Context manager that opens a sqlite3 connection, executes a query with params,
    and returns the fetched results on __enter__.

    Example:
        q = "SELECT * FROM users WHERE age > ?"
        with ExecuteQuery(q, (25,)) as results:
            for row in results:
                print(dict(row))
    """

    def __init__(self, query: str, params: Optional[Iterable[Any]] = None, db_path: str = "users.db"):
        self.query = query
        # convert params to tuple for sqlite execute
        self.params = tuple(params) if params is not None else tuple()
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._results: Optional[List[sqlite3.Row]] = None

    def __enter__(self) -> List[sqlite3.Row]:
        # open connection
        self.conn = sqlite3.connect(self.db_path)
        # return rows as sqlite3.Row to allow dict-like access
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # execute query with params
        if self.params:
            self.cursor.execute(self.query, self.params)
        else:
            self.cursor.execute(self.query)

        # fetch results and store them
        self._results = self.cursor.fetchall()
        return self._results

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        # cleanup cursor and connection
        try:
            if self.cursor is not None:
                self.cursor.close()
        except Exception:
            pass
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception:
            pass

        # Do not suppress exceptions: let them propagate
        return False


if __name__ == "__main__":
    # Demonstration: execute the required query and print results
    query = "SELECT * FROM users WHERE age > ?"
    params = (25,)

    try:
        with ExecuteQuery(query, params) as results:
            if not results:
                print("No users found with age > 25.")
            else:
                for row in results:
                    # sqlite3.Row behaves like a mapping
                    print(dict(row))
    except sqlite3.OperationalError as e:
        print("OperationalError:", e)
        print("Make sure 'users.db' exists and contains a 'users' table.")
    except Exception as e:
        print("Error:", e)

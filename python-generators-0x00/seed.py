#!/usr/bin/env python3
"""
seed.py

Utilities to bootstrap a MySQL database for the ALX_prodev project,
create the `user_data` table, load data from a CSV, and provide a
generator that streams rows one-by-one from the table.

Functions (as requested):
- connect_db()
- create_database(connection)
- connect_to_prodev()
- create_table(connection)
- insert_data(connection, csv_path)
- stream_user_data(connection)  # the row-by-row generator
"""

import os
import csv
import mysql.connector
from mysql.connector import errorcode
from typing import Generator, Tuple, Optional


def _get_mysql_connection_params():
    """
    Resolve connection parameters from environment variables with sensible defaults.
    Users may set MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_PORT.
    Defaults: user='root', password='', host='127.0.0.1', port=3306
    """
    return {
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
    }


def connect_db():
    """
    Connect to the MySQL server (no specific database).
    Returns a mysql.connector connection or None on failure.
    """
    params = _get_mysql_connection_params()
    try:
        conn = mysql.connector.connect(
            host=params["host"],
            port=params["port"],
            user=params["user"],
            password=params["password"],
            autocommit=True,  # for DB creation etc.
        )
        return conn
    except mysql.connector.Error as err:
        print(f"[connect_db] ERROR: Could not connect to MySQL server: {err}")
        return None


def create_database(connection) -> None:
    """
    Create the ALX_prodev database if it does not exist.
    """
    if connection is None:
        raise ValueError("create_database: connection is None")

    cursor = connection.cursor()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        # commit not necessary with autocommit=True, but keep for safety
        connection.commit()
    except mysql.connector.Error as err:
        print(f"[create_database] ERROR creating database: {err}")
        raise
    finally:
        cursor.close()


def connect_to_prodev():
    """
    Connect to the ALX_prodev database and return the connection.
    Returns None on failure.
    """
    params = _get_mysql_connection_params()
    try:
        conn = mysql.connector.connect(
            host=params["host"],
            port=params["port"],
            user=params["user"],
            password=params["password"],
            database="ALX_prodev",
            autocommit=False,  # we'll commit explicitly after inserts
        )
        return conn
    except mysql.connector.Error as err:
        print(f"[connect_to_prodev] ERROR: Could not connect to ALX_prodev database: {err}")
        return None


def create_table(connection) -> None:
    """
    Create the user_data table if it does not exist with the required fields:
    user_id CHAR(36) PRIMARY KEY, name VARCHAR NOT NULL, email VARCHAR NOT NULL, age DECIMAL NOT NULL
    Also creates an index on email (unique) to prevent duplicates.
    """
    if connection is None:
        raise ValueError("create_table: connection is None")

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS user_data (
      user_id CHAR(36) NOT NULL PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      email VARCHAR(255) NOT NULL,
      age DECIMAL(5,0) NOT NULL,
      UNIQUE KEY uq_user_email (email)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    cursor = connection.cursor()
    try:
        cursor.execute(create_table_sql)
        connection.commit()
        print("Table user_data created successfully")
    except mysql.connector.Error as err:
        print(f"[create_table] ERROR creating table: {err}")
        raise
    finally:
        cursor.close()


def insert_data(connection, csv_path: str) -> None:
    """
    Insert data from a CSV file into user_data table.
    CSV is expected to have headers: user_id,name,email,age (or equivalent order).
    If a row with the same user_id already exists, it will be ignored (no duplicate insert).
    """
    if connection is None:
        raise ValueError("insert_data: connection is None")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    cursor = connection.cursor()
    # Use INSERT IGNORE to skip duplicates on primary key or unique email
    insert_sql = """
    INSERT IGNORE INTO user_data (user_id, name, email, age)
    VALUES (%s, %s, %s, %s);
    """
    inserted = 0
    try:
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # If CSV has no headers, fallback to reader that yields lists
            if reader.fieldnames is None:
                csvfile.seek(0)
                reader = csv.reader(csvfile)
                for row in reader:
                    # expect order user_id, name, email, age
                    vals = (row[0], row[1], row[2], row[3])
                    cursor.execute(insert_sql, vals)
                    inserted += cursor.rowcount
            else:
                # Normalize header names (lower-case)
                headers = [h.strip().lower() for h in reader.fieldnames]
                for row in reader:
                    # fetch with tolerant keys
                    # expected keys: user_id, name, email, age
                    user_id = row.get("user_id") or row.get("id") or row.get("uuid")
                    name = row.get("name") or row.get("full_name")
                    email = row.get("email")
                    age = row.get("age")
                    if user_id is None or name is None or email is None or age is None:
                        # try positional fallback
                        vals = [row[h] for h in reader.fieldnames]
                        if len(vals) >= 4:
                            user_id, name, email, age = vals[0], vals[1], vals[2], vals[3]
                        else:
                            # skip malformed row
                            continue
                    # Convert age to integer-compatible string (DECIMAL with 0 scale)
                    try:
                        age_val = int(float(age))
                    except Exception:
                        # default age to 0 if malformed
                        age_val = 0
                    cursor.execute(insert_sql, (user_id.strip(), name.strip(), email.strip(), age_val))
                    inserted += cursor.rowcount
        connection.commit()
    except mysql.connector.Error as err:
        connection.rollback()
        print(f"[insert_data] ERROR inserting data: {err}")
        raise
    finally:
        cursor.close()
    # Optionally print how many inserted
    # print(f"Inserted {inserted} rows (duplicates ignored).")


def stream_user_data(connection) -> Generator[Tuple[str, str, str, int], None, None]:
    """
    Generator that streams rows from user_data one-by-one.
    Yields tuples: (user_id, name, email, age)

    Uses a server-side cursor (unbuffered) to avoid loading all rows in memory.
    """
    if connection is None:
        raise ValueError("stream_user_data: connection is None")

    # mysql.connector cursor default is unbuffered; to be explicit:
    cursor = connection.cursor(buffered=False)
    try:
        cursor.execute("SELECT user_id, name, email, age FROM user_data;")
        row = cursor.fetchone()
        while row is not None:
            # row is a tuple
            yield row
            row = cursor.fetchone()
    finally:
        try:
            cursor.close()
        except Exception:
            pass


# If this module is run directly, provide a small demo (not used by 0-main.py)
if __name__ == "__main__":
    conn = connect_db()
    if not conn:
        print("Unable to connect to MySQL server.")
        raise SystemExit(1)

    create_database(conn)
    conn.close()

    conn = connect_to_prodev()
    if not conn:
        print("Unable to connect to ALX_prodev database.")
        raise SystemExit(1)

    create_table(conn)

    # Attempt to locate user_data.csv in current directory
    csv_file = "user_data.csv"
    if os.path.exists(csv_file):
        insert_data(conn, csv_file)
    else:
        print(f"No '{csv_file}' found in current directory - skipping insert.")

    # Print first 5 rows (for quick verification)
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_data LIMIT 5;")
    rows = cur.fetchall()
    print(rows)
    cur.close()

    # Demonstrate streaming generator (print first 3 streamed rows)
    print("--- streaming 3 rows ---")
    gen = stream_user_data(conn)
    for _ in range(3):
        try:
            print(next(gen))
        except StopIteration:
            break

    conn.close()

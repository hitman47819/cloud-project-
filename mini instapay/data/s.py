import sqlite3
import os

DATABASE = 'instapay.db'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', DATABASE)

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Allows column access by name
    return conn

# Check the schema of the 'users' table
with get_db_connection() as conn:
    cursor = conn.execute("PRAGMA table_info(users);")
    columns = cursor.fetchall()
    for column in columns:
        print(dict(column))


import sqlite3
import os

def get_db_path():
    return os.path.join(os.path.dirname(__file__), '..', 'data', 'attention.db')

def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def execute_db(query, params=(), fetch_last_id=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    result = cursor.fetchall()
    last_id = cursor.lastrowid if fetch_last_id else None
    conn.close()
    return (result, last_id) if fetch_last_id else result

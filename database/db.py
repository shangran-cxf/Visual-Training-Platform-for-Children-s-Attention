import sqlite3
import os
from .config import DATABASE_PATH

def get_db_path():
    return DATABASE_PATH

def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def execute_db(query, params=(), fetch_last_id=False):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        if not query.strip().upper().startswith('SELECT'):
            conn.commit()
        result = cursor.fetchall()
        last_id = cursor.lastrowid if fetch_last_id else None
        return (result, last_id) if fetch_last_id else result
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise e
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

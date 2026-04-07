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
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        # 只有非SELECT查询才需要提交事务
        if not query.strip().upper().startswith('SELECT'):
            conn.commit()
        result = cursor.fetchall()
        last_id = cursor.lastrowid if fetch_last_id else None
        return (result, last_id) if fetch_last_id else result
    except Exception as e:
        # 发生异常时回滚事务
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise e
    finally:
        # 无论是否发生异常，都关闭数据库连接
        if conn:
            try:
                conn.close()
            except:
                pass

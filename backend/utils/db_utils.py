from flask import jsonify
from database import execute_db


def build_update_sql(table: str, data: dict, condition: str) -> tuple:
    set_clauses = []
    params = []
    
    for key, value in data.items():
        set_clauses.append(f"{key} = ?")
        params.append(value)
    
    sql = f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {condition}"
    return (sql, tuple(params))


def check_user_exists(user_id: int = None, username: str = None) -> bool:
    if user_id is not None:
        result = execute_db('SELECT id FROM parents WHERE id = ?', (user_id,))
        return len(result) > 0
    
    if username is not None:
        result = execute_db('SELECT id FROM parents WHERE username = ?', (username,))
        return len(result) > 0
    
    return False


def is_admin(user_id: int) -> bool:
    result = execute_db('SELECT role FROM parents WHERE id = ?', (user_id,))
    
    if not result:
        return False
    
    return result[0][0] == 'admin'

import sqlite3

def check_columns():
    conn = sqlite3.connect('backend/database.db')
    cursor = conn.cursor()
    
    # 获取 session_summaries 表的所有列
    cursor.execute("PRAGMA table_info(session_summaries)")
    columns = cursor.fetchall()
    
    print("=== session_summaries 表列结构 ===")
    for col in columns:
        print(f"{col[1]}: {col[2]}")
    
    conn.close()

if __name__ == "__main__":
    check_columns()
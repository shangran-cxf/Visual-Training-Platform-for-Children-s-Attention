import sqlite3

def check_database():
    conn = sqlite3.connect('backend/database.db')
    cursor = conn.cursor()
    
    # 获取所有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("=== 数据库表结构 ===")
    for table in tables:
        table_name = table[0]
        print(f"\n--- 表: {table_name} ---")
        
        # 获取表的列
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"{col[1]}: {col[2]}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
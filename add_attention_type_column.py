import sqlite3
import os

# 获取数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DATABASE_DIR, 'attention.db')

def add_attention_type_column():
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查 session_summaries 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_summaries';")
        if cursor.fetchone():
            # 检查 attention_type 列是否存在
            cursor.execute("PRAGMA table_info(session_summaries);")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'attention_type' not in columns:
                # 添加 attention_type 列
                cursor.execute("ALTER TABLE session_summaries ADD COLUMN attention_type TEXT;")
                print("成功添加 attention_type 列到 session_summaries 表")
            else:
                print("attention_type 列已经存在")
        else:
            print("session_summaries 表不存在")
        
        # 提交更改并关闭连接
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"操作失败: {e}")

if __name__ == "__main__":
    add_attention_type_column()
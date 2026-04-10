import sqlite3

conn = sqlite3.connect('database/attention.db')
cursor = conn.cursor()

# 查询所有表
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("数据库中的表:")
for table in tables:
    print(f"  - {table[0]}")

conn.close()

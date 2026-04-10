import sqlite3
conn = sqlite3.connect('database/attention.db')
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('所有表:')
for t in tables:
    print(f'  {t[0]}')

# 检查 game_raw_data 表
print('\ngame_raw_data 表的数据:')
try:
    rows = c.execute("SELECT * FROM game_raw_data ORDER BY id DESC LIMIT 5").fetchall()
    for r in rows:
        print(f'  {r}')
except Exception as e:
    print(f'  错误：{e}')

conn.close()

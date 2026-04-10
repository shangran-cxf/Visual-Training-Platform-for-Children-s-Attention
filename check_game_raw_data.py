import sqlite3
conn = sqlite3.connect('database/attention.db')
c = conn.cursor()
cols = c.execute("PRAGMA table_info(game_raw_data)").fetchall()
print('game_raw_data 表的列:')
for col in cols:
    print(f'  {col[0]}: {col[1]} ({col[2]})')

conn.close()

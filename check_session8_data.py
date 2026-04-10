import sqlite3
conn = sqlite3.connect('database/attention.db')
c = conn.cursor()
cols = c.execute("PRAGMA table_info(game_raw_data)").fetchall()
col_names = [col[1] for col in cols]
row = c.execute("SELECT * FROM game_raw_data WHERE session_id = 8").fetchone()
print('session_id=8 的数据:')
for i, (name, value) in enumerate(zip(col_names, row)):
    print(f'  {name}: {value}')
conn.close()

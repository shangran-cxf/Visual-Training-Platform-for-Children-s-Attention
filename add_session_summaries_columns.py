import sqlite3

# 连接数据库
conn = sqlite3.connect('database/attention.db')
cursor = conn.cursor()

# 检查 session_summaries 表的列
columns = cursor.execute("PRAGMA table_info(session_summaries)").fetchall()
column_names = [col[1] for col in columns]

print("当前 session_summaries 表的列:")
for col in column_names:
    print(f"  - {col}")

# 需要添加的列
columns_to_add = [
    ('accuracy_score', 'REAL'),
    ('precision_score', 'REAL'),
    ('speed_score', 'REAL'),
    ('head_stable_score', 'REAL'),
    ('face_stable_score', 'REAL'),
    ('blink_stable_score', 'REAL'),
    ('impulse_score', 'REAL'),
    ('memory_score', 'REAL'),
    ('no_fatigue_score', 'REAL'),
    ('rt_score', 'REAL'),
    ('order_score', 'REAL'),
    ('stable_act_score', 'REAL'),
    ('game_data', 'TEXT')
]

# 添加缺失的列
for column_name, column_type in columns_to_add:
    if column_name not in column_names:
        print(f"\n添加缺失的列：{column_name} {column_type}")
        try:
            cursor.execute(f'ALTER TABLE session_summaries ADD COLUMN {column_name} {column_type}')
            print(f'  ✓ 成功添加 {column_name}')
        except sqlite3.OperationalError as e:
            print(f'  ✗ 添加失败：{e}')
    else:
        print(f"\n列 {column_name} 已存在，跳过")

# 提交更改
conn.commit()

# 验证
print("\n\n验证添加后的列:")
columns = cursor.execute("PRAGMA table_info(session_summaries)").fetchall()
for col in columns:
    print(f"  {col[0]}: {col[1]} ({col[2]})")

conn.close()
print("\n数据库更新完成！")

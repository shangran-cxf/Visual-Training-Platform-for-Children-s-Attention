import sqlite3
import json

conn = sqlite3.connect('database/attention.db')
cursor = conn.cursor()

print("=== 检查儿童 ID 9 的训练数据 ===\n")

# 查询儿童 9 的信息
child = cursor.execute('SELECT id, name, parent_id FROM children WHERE id = 9').fetchone()
if child:
    print(f"儿童信息：ID={child[0]}, 姓名={child[1]}, 家长 ID={child[2]}")
else:
    print("儿童 ID 9 不存在")

# 查询儿童 9 的训练会话
sessions = cursor.execute('''
    SELECT id, game_type, attention_type, start_time, end_time, status
    FROM training_sessions
    WHERE child_id = 9
    ORDER BY start_time DESC
''').fetchall()

print(f"\n儿童 9 的训练会话数：{len(sessions)}")
for session in sessions:
    print(f"  - ID: {session[0]}, 游戏：{session[1]}, 注意力类型：{session[2]}, 开始：{session[3]}, 结束：{session[4]}, 状态：{session[5]}")

# 查询儿童 9 的会话摘要
summaries = cursor.execute('''
    SELECT session_id, game_type, attention_type, final_score, overall_score, performance_level
    FROM session_summaries
    WHERE child_id = 9
    ORDER BY session_id DESC
''').fetchall()

print(f"\n儿童 9 的会话摘要数：{len(summaries)}")
for summary in summaries:
    print(f"  - 会话 ID: {summary[0]}, 游戏：{summary[1]}, 注意力类型：{summary[2]}, 最终得分：{summary[3]}, 总体得分：{summary[4]}, 等级：{summary[5]}")

# 查询最新的训练会话（不限儿童 ID）
print("\n=== 最新的 5 条训练会话 ===")
latest_sessions = cursor.execute('''
    SELECT id, child_id, game_type, attention_type, start_time, end_time, status
    FROM training_sessions
    ORDER BY start_time DESC
    LIMIT 5
''').fetchall()

for session in latest_sessions:
    print(f"  - ID: {session[0]}, 儿童 ID: {session[1]}, 游戏：{session[2]}, 注意力类型：{session[3]}, 开始：{session[4]}, 状态：{session[6]}")

# 查询最新的会话摘要
print("\n=== 最新的 5 条会话摘要 ===")
latest_summaries = cursor.execute('''
    SELECT session_id, child_id, game_type, attention_type, final_score, overall_score, performance_level
    FROM session_summaries
    ORDER BY session_id DESC
    LIMIT 5
''').fetchall()

for summary in latest_summaries:
    print(f"  - 会话 ID: {summary[0]}, 儿童 ID: {summary[1]}, 游戏：{summary[2]}, 注意力类型：{summary[3]}, 最终得分：{summary[4]}, 总体得分：{summary[5]}, 等级：{summary[6]}")

conn.close()

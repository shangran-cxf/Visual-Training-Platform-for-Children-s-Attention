import sqlite3
import json

conn = sqlite3.connect('database/attention.db')
cursor = conn.cursor()

print("=== 所有儿童的训练数据 ===\n")

# 查询所有儿童
children = cursor.execute('SELECT id, name, parent_id FROM children').fetchall()
print(f"共有 {len(children)} 个儿童:\n")

for child in children:
    child_id, name, parent_id = child
    print(f"儿童 ID: {child_id}, 姓名: {name}, 家长 ID: {parent_id}")
    
    # 查询该儿童的训练会话
    sessions = cursor.execute('''
        SELECT id, game_type, attention_type, start_time, end_time, status
        FROM training_sessions
        WHERE child_id = ?
        ORDER BY start_time DESC
        LIMIT 5
    ''', (child_id,)).fetchall()
    
    print(f"  训练会话数: {len(sessions)}")
    if sessions:
        for session in sessions:
            print(f"    - ID: {session[0]}, 游戏: {session[1]}, 注意力类型: {session[2]}, 时间: {session[3]}, 状态: {session[5]}")
    
    # 查询该儿童的会话摘要
    summaries = cursor.execute('''
        SELECT session_id, game_type, attention_type, final_score, overall_score, performance_level
        FROM session_summaries
        WHERE child_id = ?
        ORDER BY session_id DESC
        LIMIT 5
    ''', (child_id,)).fetchall()
    
    print(f"  会话摘要数: {len(summaries)}")
    if summaries:
        for summary in summaries:
            print(f"    - 会话 ID: {summary[0]}, 游戏: {summary[1]}, 注意力类型: {summary[2]}, 最终得分: {summary[3]}, 总体得分: {summary[4]}")
    
    print()

conn.close()

import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('database/attention.db')
cursor = conn.cursor()

print("=== 实时检查训练数据 ===\n")
print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# 查询所有儿童
children = cursor.execute('SELECT id, name, parent_id FROM children').fetchall()
print(f"共有 {len(children)} 个儿童\n")

for child in children:
    child_id, name, parent_id = child
    
    # 查询该儿童最近的训练会话
    sessions = cursor.execute('''
        SELECT id, game_type, start_time, status
        FROM training_sessions
        WHERE child_id = ?
        ORDER BY start_time DESC
        LIMIT 1
    ''', (child_id,)).fetchall()
    
    # 查询该儿童的会话摘要
    summaries = cursor.execute('''
        SELECT session_id, final_score, overall_score
        FROM session_summaries
        WHERE child_id = ?
        ORDER BY session_id DESC
        LIMIT 1
    ''', (child_id,)).fetchall()
    
    if sessions or summaries:
        print(f"儿童 ID: {child_id}, 姓名：{name}, 家长 ID: {parent_id}")
        if sessions:
            session = sessions[0]
            print(f"  最近会话：ID={session[0]}, 游戏={session[1]}, 时间={session[2]}, 状态={session[3]}")
        if summaries:
            summary = summaries[0]
            print(f"  最近摘要：会话 ID={summary[0]}, 最终得分={summary[1]}, 总体得分={summary[2]}")
        print()

conn.close()

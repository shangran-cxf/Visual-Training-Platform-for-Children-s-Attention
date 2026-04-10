import sqlite3
import os

# 获取数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DATABASE_DIR, 'attention.db')

def check_database_data():
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查 training_sessions 表
        print("=== 检查 training_sessions 表 ===")
        cursor.execute("SELECT COUNT(*) FROM training_sessions;")
        training_sessions_count = cursor.fetchone()[0]
        print(f"training_sessions 表中的记录数: {training_sessions_count}")
        
        # 检查最近的训练会话
        if training_sessions_count > 0:
            cursor.execute("SELECT id, child_id, game_type, start_time, end_time, status FROM training_sessions ORDER BY start_time DESC LIMIT 5;")
            print("最近的5条训练会话:")
            for row in cursor.fetchall():
                print(f"ID: {row[0]}, 儿童ID: {row[1]}, 游戏类型: {row[2]}, 开始时间: {row[3]}, 结束时间: {row[4]}, 状态: {row[5]}")
        
        # 检查 session_summaries 表
        print("\n=== 检查 session_summaries 表 ===")
        cursor.execute("SELECT COUNT(*) FROM session_summaries;")
        session_summaries_count = cursor.fetchone()[0]
        print(f"session_summaries 表中的记录数: {session_summaries_count}")
        
        # 检查最近的会话摘要
        if session_summaries_count > 0:
            cursor.execute("SELECT session_id, child_id, game_type, attention_type, final_score, overall_score, performance_level FROM session_summaries ORDER BY rowid DESC LIMIT 5;")
            print("最近的5条会话摘要:")
            for row in cursor.fetchall():
                print(f"会话ID: {row[0]}, 儿童ID: {row[1]}, 游戏类型: {row[2]}, 注意力类型: {row[3]}, 最终得分: {row[4]}, 总体得分: {row[5]}, 表现等级: {row[6]}")
        
        # 检查儿童ID为9的训练数据
        print("\n=== 检查儿童ID为9的训练数据 ===")
        cursor.execute("SELECT COUNT(*) FROM training_sessions WHERE child_id = 9;")
        child9_training_count = cursor.fetchone()[0]
        print(f"儿童ID为9的训练会话数: {child9_training_count}")
        
        cursor.execute("SELECT COUNT(*) FROM session_summaries WHERE child_id = 9;")
        child9_summary_count = cursor.fetchone()[0]
        print(f"儿童ID为9的会话摘要数: {child9_summary_count}")
        
        # 关闭连接
        conn.close()
    except Exception as e:
        print(f"操作失败: {e}")

if __name__ == "__main__":
    check_database_data()
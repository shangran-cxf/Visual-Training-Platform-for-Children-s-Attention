import sqlite3
import os

# 获取数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DATABASE_DIR, 'attention.db')

def add_missing_columns():
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查 session_summaries 表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_summaries';")
        if cursor.fetchone():
            # 检查并添加缺少的列
            cursor.execute("PRAGMA table_info(session_summaries);")
            columns = [column[1] for column in cursor.fetchall()]
            
            # 定义需要的列及其类型
            required_columns = [
                ('session_id', 'TEXT PRIMARY KEY'),
                ('child_id', 'INTEGER'),
                ('game_type', 'TEXT'),
                ('attention_type', 'TEXT'),
                ('final_score', 'REAL'),
                ('total_accuracy', 'REAL'),
                ('total_time', 'REAL'),
                ('total_errors', 'INTEGER'),
                ('levels_completed', 'INTEGER'),
                ('avg_attention_score', 'REAL'),
                ('max_attention_score', 'REAL'),
                ('min_attention_score', 'REAL'),
                ('attention_stability', 'REAL'),
                ('avg_head_deviation', 'REAL'),
                ('avg_blink_rate', 'REAL'),
                ('total_focus_time', 'REAL'),
                ('distraction_count', 'INTEGER'),
                ('overall_score', 'REAL'),
                ('performance_level', 'TEXT'),
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
            
            # 添加缺少的列
            for column_name, column_type in required_columns:
                if column_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE session_summaries ADD COLUMN {column_name} {column_type};")
                        print(f"成功添加 {column_name} 列")
                    except Exception as e:
                        print(f"添加 {column_name} 列失败: {e}")
                else:
                    print(f"{column_name} 列已经存在")
        else:
            print("session_summaries 表不存在")
        
        # 提交更改并关闭连接
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"操作失败: {e}")

if __name__ == "__main__":
    add_missing_columns()
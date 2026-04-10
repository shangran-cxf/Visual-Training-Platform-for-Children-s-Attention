import sqlite3
import os

# 数据库文件路径
db_path = os.path.join(os.path.dirname(__file__), 'database.db')

def init_db():
    """初始化数据库，创建所有必要的表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建 processed_requests 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建 training_sessions 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER,
        game_type TEXT,
        session_token TEXT,
        device_id TEXT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        duration INTEGER,
        status TEXT DEFAULT 'active',
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id) REFERENCES children(id)
    )
    ''')
    
    # 创建 game_raw_data 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_raw_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        event_type TEXT,
        event_data TEXT,
        score INTEGER,
        accuracy REAL,
        level INTEGER,
        timestamp TEXT,
        time REAL,
        correct INTEGER,
        error INTEGER,
        miss INTEGER,
        leave INTEGER,
        obstacle INTEGER,
        total_target INTEGER,
        total_step INTEGER,
        total_click INTEGER,
        total_trial INTEGER,
        memory_load INTEGER,
        order_error INTEGER,
        late_error_ratio REAL,
        mean_rt REAL,
        reaction_times TEXT,
        FOREIGN KEY (session_id) REFERENCES training_sessions(id)
    )
    ''')
    
    # 创建 vision_raw_data 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vision_raw_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        attention_score REAL,
        face_detected INTEGER,
        head_yaw REAL,
        head_pitch REAL,
        face_area REAL,
        blink_rate REAL,
        focus_duration REAL,
        face_distance REAL,
        blink_count INTEGER,
        timestamp TEXT,
        FOREIGN KEY (session_id) REFERENCES training_sessions(id)
    )
    ''')
    
    # 创建 session_summaries 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS session_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        child_id INTEGER,
        game_type TEXT,
        attention_type TEXT,
        final_score INTEGER,
        total_accuracy REAL,
        total_time INTEGER,
        total_errors INTEGER,
        levels_completed INTEGER,
        avg_attention_score REAL,
        max_attention_score REAL,
        min_attention_score REAL,
        attention_stability REAL,
        avg_head_deviation REAL,
        avg_blink_rate REAL,
        total_focus_time REAL,
        distraction_count INTEGER,
        overall_score INTEGER,
        performance_level TEXT,
        accuracy_score INTEGER,
        precision_score INTEGER,
        speed_score INTEGER,
        head_stable_score INTEGER,
        face_stable_score INTEGER,
        blink_stable_score INTEGER,
        impulse_score INTEGER,
        memory_score INTEGER,
        no_fatigue_score INTEGER,
        rt_score INTEGER,
        order_score INTEGER,
        stable_act_score INTEGER,
        game_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES training_sessions(id),
        FOREIGN KEY (child_id) REFERENCES children(id)
    )
    ''')
    
    # 创建 children 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS children (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER,
        name TEXT,
        age INTEGER,
        gender TEXT,
        avatar TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES parents(id)
    )
    ''')
    
    # 创建 parents 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT UNIQUE,
        phone TEXT,
        avatar TEXT,
        role TEXT DEFAULT 'parent',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建 user_badges 表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER,
        badge_id TEXT,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id) REFERENCES children(id),
        UNIQUE(child_id, badge_id)
    )
    ''')
    
    # 插入默认数据
    # 插入默认家长用户
    cursor.execute('''
    INSERT OR IGNORE INTO parents (id, username, password, email, role) 
    VALUES (1, 'admin', 'admin123', 'admin@example.com', 'admin')
    ''')
    
    # 插入默认孩子数据
    default_children = [
        (1, 1, '小明', 8, '男', 'avatar1.png'),
        (2, 1, '小红', 7, '女', 'avatar2.png'),
        (3, 1, '小华', 9, '男', 'avatar3.png'),
        (4, 1, '小丽', 6, '女', 'avatar4.png'),
        (5, 1, '小强', 10, '男', 'avatar5.png'),
        (6, 1, '小美', 8, '女', 'avatar6.png'),
        (7, 1, '小杰', 9, '男', 'avatar7.png')
    ]
    
    cursor.executemany('''
    INSERT OR IGNORE INTO children (id, parent_id, name, age, gender, avatar) 
    VALUES (?, ?, ?, ?, ?, ?)
    ''', default_children)
    
    # 提交事务
    conn.commit()
    conn.close()

def execute_db(sql, params=(), fetch_last_id=False):
    """执行数据库操作"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        if fetch_last_id:
            cursor.execute(sql, params)
            last_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return None, last_id
        else:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            conn.commit()
            conn.close()
            return result
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e
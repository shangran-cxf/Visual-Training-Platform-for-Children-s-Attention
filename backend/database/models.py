import sqlite3
import os
from .db import get_db_path

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    try:
        cursor.execute('ALTER TABLE parents ADD COLUMN uid INTEGER UNIQUE')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE parents ADD COLUMN role TEXT DEFAULT \'user\'')
    except:
        pass
    
    cursor.execute("SELECT COUNT(*) FROM parents WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO parents (uid, username, password, email, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (100000, 'admin', '123456', 'admin@system.com', 'admin'))
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS children (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        age INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES parents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS forum_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        view_count INTEGER DEFAULT 0,
        FOREIGN KEY (parent_id) REFERENCES parents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS forum_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        parent_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES forum_posts (id),
        FOREIGN KEY (parent_id) REFERENCES parents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS forum_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        comment_id INTEGER,
        parent_id INTEGER NOT NULL,
        vote_type INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES forum_posts (id),
        FOREIGN KEY (comment_id) REFERENCES forum_comments (id),
        FOREIGN KEY (parent_id) REFERENCES parents (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS detection_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        selective_attention REAL,
        sustained_attention REAL,
        visual_tracking REAL,
        working_memory REAL,
        inhibitory_control REAL,
        total_score REAL,
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        training_type TEXT NOT NULL,
        difficulty INTEGER NOT NULL,
        accuracy REAL,
        completion_time INTEGER,
        error_count INTEGER,
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        icon TEXT,
        requirement_type TEXT,
        requirement_value INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        badge_id INTEGER NOT NULL,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id) REFERENCES children (id),
        FOREIGN KEY (badge_id) REFERENCES badges (id)
    )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM badges")
    if cursor.fetchone()[0] == 0:
        default_badges = [
            ('初学者', '完成第一次训练', '🎯', 'training_count', 1),
            ('坚持者', '连续训练7天', '🔥', 'consecutive_days', 7),
            ('专注达人', '完成50次训练', '⭐', 'training_count', 50),
            ('完美表现', '单次训练正确率达到100%', '💯', 'perfect_accuracy', 1),
            ('速度之星', '在规定时间内完成训练', '⚡', 'speed_complete', 1),
            ('记忆大师', '工作记忆得分超过90分', '🧠', 'memory_score', 90),
            ('追踪专家', '视觉追踪得分超过90分', '👁️', 'tracking_score', 90),
            ('注意力王者', '总分超过95分', '👑', 'total_score', 95),
        ]
        for badge in default_badges:
            cursor.execute('''
                INSERT INTO badges (name, description, icon, requirement_type, requirement_value)
                VALUES (?, ?, ?, ?, ?)
            ''', badge)
    
    try:
        cursor.execute('ALTER TABLE parents ADD COLUMN avatar TEXT DEFAULT \'\'')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE parents ADD COLUMN level INTEGER DEFAULT 1')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE parents ADD COLUMN experience INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE parents ADD COLUMN is_banned INTEGER DEFAULT 0')
    except:
        pass
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        icon TEXT,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ('育儿经验', '分享育儿心得和经验', '👶', 1),
            ('注意力训练', '讨论注意力训练方法和技巧', '🎯', 2),
            ('学习资源', '分享学习资料和资源', '📚', 3),
            ('问题求助', '遇到问题寻求帮助', '❓', 4),
            ('闲聊灌水', '轻松闲聊，分享生活', '💬', 5),
        ]
        for cat in default_categories:
            cursor.execute('''
                INSERT INTO categories (name, description, icon, sort_order)
                VALUES (?, ?, ?, ?)
            ''', cat)
    
    try:
        cursor.execute('ALTER TABLE forum_posts ADD COLUMN category_id INTEGER')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE forum_posts ADD COLUMN is_pinned INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE forum_posts ADD COLUMN is_essential INTEGER DEFAULT 0')
    except:
        pass
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES parents (id),
        FOREIGN KEY (post_id) REFERENCES forum_posts (id),
        UNIQUE(parent_id, post_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,
        post_id INTEGER,
        comment_id INTEGER,
        reason TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES parents (id),
        FOREIGN KEY (post_id) REFERENCES forum_posts (id),
        FOREIGN KEY (comment_id) REFERENCES forum_comments (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        game_type TEXT NOT NULL,
        session_token TEXT NOT NULL,
        device_id TEXT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        duration INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_raw_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        event_type TEXT NOT NULL,
        event_data TEXT,
        score INTEGER,
        accuracy REAL,
        level INTEGER,
        FOREIGN KEY (session_id) REFERENCES training_sessions (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vision_raw_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        attention_score REAL,
        face_detected INTEGER DEFAULT 0,
        head_yaw REAL,
        head_pitch REAL,
        face_area REAL,
        blink_rate REAL,
        focus_duration REAL,
        FOREIGN KEY (session_id) REFERENCES training_sessions (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS session_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        child_id INTEGER NOT NULL,
        game_type TEXT NOT NULL,
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
        overall_score REAL,
        performance_level TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES training_sessions (id),
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attention_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        report_type TEXT NOT NULL,
        period_start TIMESTAMP NOT NULL,
        period_end TIMESTAMP NOT NULL,
        selective_attention_score REAL,
        sustained_attention_score REAL,
        visual_tracking_score REAL,
        working_memory_score REAL,
        inhibitory_control_score REAL,
        total_score REAL,
        percentile REAL,
        improvement_rate REAL,
        strengths TEXT,
        weaknesses TEXT,
        recommendations TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS progress_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_sessions INTEGER DEFAULT 0,
        total_duration INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0,
        avg_score_change REAL,
        accuracy_improvement REAL,
        attention_improvement REAL,
        milestones_achieved TEXT,
        badges_earned INTEGER DEFAULT 0,
        recommended_games TEXT,
        focus_areas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS game_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_type TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT,
        dimensions TEXT,
        fields_schema TEXT,
        scoring_formula TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT NOT NULL UNIQUE,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

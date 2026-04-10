import sqlite3
from .db import get_db_path
import os

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
        avatar TEXT DEFAULT '',
        level INTEGER DEFAULT 1,
        experience INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
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
        category_id INTEGER,
        is_pinned INTEGER DEFAULT 0,
        is_essential INTEGER DEFAULT 0,
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
    CREATE TABLE IF NOT EXISTS user_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        badge_id INTEGER NOT NULL,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
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
    CREATE TABLE IF NOT EXISTS training_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        game_type TEXT NOT NULL,
        attention_type TEXT,
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
        time INTEGER DEFAULT 0,
        correct INTEGER DEFAULT 0,
        error INTEGER DEFAULT 0,
        miss INTEGER DEFAULT 0,
        leave INTEGER DEFAULT 0,
        obstacle INTEGER DEFAULT 0,
        total_target INTEGER DEFAULT 1,
        total_step INTEGER DEFAULT 1,
        total_click INTEGER DEFAULT 1,
        total_trial INTEGER DEFAULT 1,
        memory_load INTEGER DEFAULT 1,
        order_error INTEGER DEFAULT 0,
        late_error_ratio REAL DEFAULT 0,
        mean_rt INTEGER DEFAULT 1000,
        reaction_times TEXT,
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
        face_distance REAL,
        blink_rate REAL,
        blink_count INTEGER DEFAULT 0,
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
        overall_score REAL,
        performance_level TEXT,
        accuracy_score REAL DEFAULT 0,
        precision_score REAL DEFAULT 0,
        speed_score REAL DEFAULT 0,
        head_stable_score REAL DEFAULT 0,
        face_stable_score REAL DEFAULT 0,
        blink_stable_score REAL DEFAULT 0,
        impulse_score REAL DEFAULT 0,
        memory_score REAL DEFAULT 0,
        no_fatigue_score REAL DEFAULT 0,
        rt_score REAL DEFAULT 0,
        order_score REAL DEFAULT 0,
        stable_act_score REAL DEFAULT 0,
        game_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES training_sessions (id),
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS child_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_id INTEGER NOT NULL,
        report_type TEXT NOT NULL,
        period_start TIMESTAMP,
        period_end TIMESTAMP,
        report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        selective_attention_score REAL,
        sustained_attention_score REAL,
        visual_tracking_score REAL,
        working_memory_score REAL,
        inhibitory_control_score REAL,
        total_score REAL,
        percentile REAL,
        improvement_rate REAL,
        total_sessions INTEGER DEFAULT 0,
        total_duration INTEGER DEFAULT 0,
        games_played INTEGER DEFAULT 0,
        avg_score_change REAL,
        accuracy_improvement REAL,
        attention_improvement REAL,
        badges_earned INTEGER DEFAULT 0,
        strengths TEXT,
        weaknesses TEXT,
        recommendations TEXT,
        milestones_achieved TEXT,
        recommended_games TEXT,
        focus_areas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (child_id) REFERENCES children (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS processed_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT NOT NULL UNIQUE,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    try:
        cursor.execute('ALTER TABLE training_sessions ADD COLUMN attention_type TEXT')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN time INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN correct INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN error INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN miss INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN leave INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN obstacle INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN total_target INTEGER DEFAULT 1')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN total_step INTEGER DEFAULT 1')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN total_click INTEGER DEFAULT 1')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN total_trial INTEGER DEFAULT 1')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN memory_load INTEGER DEFAULT 1')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN order_error INTEGER DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN late_error_ratio REAL DEFAULT 0')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN mean_rt INTEGER DEFAULT 1000')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE game_raw_data ADD COLUMN reaction_times TEXT')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE vision_raw_data ADD COLUMN face_distance REAL')
    except:
        pass
    
    try:
        cursor.execute('ALTER TABLE vision_raw_data ADD COLUMN blink_count INTEGER DEFAULT 0')
    except:
        pass
    
    conn.commit()
    conn.close()

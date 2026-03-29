from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置静态文件目录
frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app.static_folder = frontend_dir

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'data', 'attention.db')

# 初始化数据库
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查users表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'child',  -- child 或 parent
            child_name TEXT,
            child_age INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    else:
        # 检查表结构，添加缺失的列
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'child_name' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN child_name TEXT")
        if 'child_age' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN child_age INTEGER")
    
    # 创建检测数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS detection_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        selective_attention REAL,  -- 选择性注意得分
        sustained_attention REAL,  -- 持续性注意得分
        visual_tracking REAL,  -- 视觉追踪得分
        working_memory REAL,  -- 工作记忆得分
        inhibitory_control REAL,  -- 抑制控制得分
        total_score REAL,  -- 总分
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # 创建训练数据表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS training_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        training_type TEXT NOT NULL,  -- 训练类型
        difficulty INTEGER NOT NULL,  -- 难度等级
        accuracy REAL,  -- 正确率
        completion_time INTEGER,  -- 完成时间（秒）
        error_count INTEGER,  -- 错误次数
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# 辅助函数：执行数据库操作
def execute_db(query, params=()):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    result = cursor.fetchall()
    conn.close()
    return result

# 1. 用户注册
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'child')
    child_name = data.get('child_name')
    child_age = data.get('child_age')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    try:
        execute_db('INSERT INTO users (username, password, role, child_name, child_age) VALUES (?, ?, ?, ?, ?)', 
                  (username, password, role, child_name, child_age))
        return jsonify({'message': '注册成功'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': '用户名已存在'}), 400

# 2. 用户登录
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    result = execute_db('SELECT id, role, child_name, child_age FROM users WHERE username = ? AND password = ?', (username, password))
    if not result:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    user_id, role, child_name, child_age = result[0]
    return jsonify({'message': '登录成功', 'user_id': user_id, 'role': role, 'child_name': child_name, 'child_age': child_age}), 200

# 3. 数据上传（检测数据）
@app.route('/api/upload/detection', methods=['POST'])
def upload_detection():
    data = request.json
    user_id = data.get('user_id')
    selective_attention = data.get('selective_attention')
    sustained_attention = data.get('sustained_attention')
    visual_tracking = data.get('visual_tracking')
    working_memory = data.get('working_memory')
    inhibitory_control = data.get('inhibitory_control')
    total_score = data.get('total_score')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    execute_db('''
    INSERT INTO detection_data (user_id, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score))
    
    return jsonify({'message': '检测数据上传成功'}), 201

# 4. 数据上传（训练数据）
@app.route('/api/upload/training', methods=['POST'])
def upload_training():
    data = request.json
    user_id = data.get('user_id')
    training_type = data.get('training_type')
    difficulty = data.get('difficulty')
    accuracy = data.get('accuracy')
    completion_time = data.get('completion_time')
    error_count = data.get('error_count')
    
    if not user_id or not training_type:
        return jsonify({'error': '用户ID和训练类型不能为空'}), 400
    
    execute_db('''
    INSERT INTO training_data (user_id, training_type, difficulty, accuracy, completion_time, error_count)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, training_type, difficulty, accuracy, completion_time, error_count))
    
    return jsonify({'message': '训练数据上传成功'}), 201

# 5. 数据拉取（检测数据）
@app.route('/api/get/detection', methods=['GET'])
def get_detection():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    result = execute_db('''
    SELECT timestamp, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score
    FROM detection_data
    WHERE user_id = ?
    ORDER BY timestamp DESC
    ''', (user_id,))
    
    data = []
    for row in result:
        data.append({
            'timestamp': row[0],
            'selective_attention': row[1],
            'sustained_attention': row[2],
            'visual_tracking': row[3],
            'working_memory': row[4],
            'inhibitory_control': row[5],
            'total_score': row[6]
        })
    
    return jsonify(data), 200

# 6. 数据拉取（训练数据）
@app.route('/api/get/training', methods=['GET'])
def get_training():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '用户ID不能为空'}), 400
    
    result = execute_db('''
    SELECT timestamp, training_type, difficulty, accuracy, completion_time, error_count
    FROM training_data
    WHERE user_id = ?
    ORDER BY timestamp DESC
    ''', (user_id,))
    
    data = []
    for row in result:
        data.append({
            'timestamp': row[0],
            'training_type': row[1],
            'difficulty': row[2],
            'accuracy': row[3],
            'completion_time': row[4],
            'error_count': row[5]
        })
    
    return jsonify(data), 200

# 根路径路由
@app.route('/')
def index():
    return send_from_directory(frontend_dir, 'index.html')

# 静态文件路由
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(frontend_dir, path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
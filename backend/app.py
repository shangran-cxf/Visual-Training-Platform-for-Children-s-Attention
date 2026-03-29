from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app.static_folder = frontend_dir

db_path = os.path.join(os.path.dirname(__file__), 'data', 'attention.db')

def init_db():
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
    
    conn.commit()
    conn.close()

init_db()

def execute_db(query, params=(), fetch_last_id=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    result = cursor.fetchall()
    last_id = cursor.lastrowid if fetch_last_id else None
    conn.close()
    return (result, last_id) if fetch_last_id else result

def get_next_uid():
    result = execute_db('SELECT MAX(uid) FROM parents')
    max_uid = result[0][0] if result and result[0][0] else 99999
    return max_uid + 1

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    children = data.get('children', [])
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    try:
        uid = get_next_uid()
        result, parent_id = execute_db(
            'INSERT INTO parents (uid, username, password, email, role) VALUES (?, ?, ?, ?, ?)',
            (uid, username, password, email, 'user'), fetch_last_id=True
        )
        
        for child in children:
            child_name = child.get('name')
            child_age = child.get('age')
            if child_name:
                execute_db(
                    'INSERT INTO children (parent_id, name, age) VALUES (?, ?, ?)',
                    (parent_id, child_name, child_age)
                )
        
        return jsonify({'message': '注册成功', 'parent_id': parent_id, 'uid': uid}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': '用户名已存在'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    result = execute_db(
        'SELECT id, uid, email, role FROM parents WHERE username = ? AND password = ?',
        (username, password)
    )
    
    if not result:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    parent_id, uid, email, role = result[0]
    
    children = execute_db(
        'SELECT id, name, age FROM children WHERE parent_id = ?',
        (parent_id,)
    )
    
    children_data = [{'id': c[0], 'name': c[1], 'age': c[2]} for c in children]
    
    return jsonify({
        'message': '登录成功',
        'parent_id': parent_id,
        'uid': uid,
        'username': username,
        'email': email,
        'role': role,
        'children': children_data
    }), 200

@app.route('/api/children', methods=['POST'])
def add_child():
    data = request.json
    parent_id = data.get('parent_id')
    name = data.get('name')
    age = data.get('age')
    
    if not parent_id or not name:
        return jsonify({'error': '家长ID和孩子姓名不能为空'}), 400
    
    result, child_id = execute_db(
        'INSERT INTO children (parent_id, name, age) VALUES (?, ?, ?)',
        (parent_id, name, age), fetch_last_id=True
    )
    
    return jsonify({'message': '添加成功', 'child_id': child_id}), 201

@app.route('/api/children/<int:parent_id>', methods=['GET'])
def get_children(parent_id):
    result = execute_db(
        'SELECT id, name, age, created_at FROM children WHERE parent_id = ?',
        (parent_id,)
    )
    
    children = [{'id': c[0], 'name': c[1], 'age': c[2], 'created_at': c[3]} for c in result]
    return jsonify(children), 200

@app.route('/api/children/<int:child_id>', methods=['DELETE'])
def delete_child(child_id):
    execute_db('DELETE FROM children WHERE id = ?', (child_id,))
    return jsonify({'message': '删除成功'}), 200

@app.route('/api/user/info', methods=['GET'])
def get_user_info():
    parent_id = request.args.get('parent_id')
    if not parent_id:
        return jsonify({'error': '缺少parent_id参数'}), 400
    
    result = execute_db(
        'SELECT uid, username, email, role, created_at FROM parents WHERE id = ?',
        (parent_id,)
    )
    
    if not result:
        return jsonify({'error': '用户不存在'}), 404
    
    uid, username, email, role, created_at = result[0]
    return jsonify({
        'uid': uid,
        'username': username,
        'email': email,
        'role': role,
        'created_at': created_at
    }), 200

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    result = execute_db('''
        SELECT p.id, p.uid, p.username, p.email, p.role, p.created_at,
               (SELECT COUNT(*) FROM children WHERE parent_id = p.id) as child_count
        FROM parents p
        ORDER BY p.uid ASC
    ''')
    
    users = [{
        'id': u[0],
        'uid': u[1],
        'username': u[2],
        'email': u[3],
        'role': u[4],
        'created_at': u[5],
        'child_count': u[6]
    } for u in result]
    
    return jsonify(users), 200

@app.route('/api/forum/posts', methods=['GET'])
def get_posts():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    offset = (page - 1) * per_page
    
    posts = execute_db('''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.parent_id,
               pr.username as author_name,
               (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) as comment_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1) as dislike_count
        FROM forum_posts p
        JOIN parents pr ON p.parent_id = pr.id
        ORDER BY p.created_at DESC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    total = execute_db('SELECT COUNT(*) FROM forum_posts')[0][0]
    
    posts_data = [{
        'id': p[0],
        'title': p[1],
        'content': p[2],
        'created_at': p[3],
        'view_count': p[4],
        'parent_id': p[5],
        'author_name': p[6],
        'comment_count': p[7],
        'like_count': p[8],
        'dislike_count': p[9]
    } for p in posts]
    
    return jsonify({
        'posts': posts_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }), 200

@app.route('/api/forum/posts', methods=['POST'])
def create_post():
    data = request.json
    parent_id = data.get('parent_id')
    title = data.get('title')
    content = data.get('content')
    
    if not parent_id or not title or not content:
        return jsonify({'error': '家长ID、标题和内容不能为空'}), 400
    
    result, post_id = execute_db(
        'INSERT INTO forum_posts (parent_id, title, content) VALUES (?, ?, ?)',
        (parent_id, title, content), fetch_last_id=True
    )
    
    return jsonify({'message': '发帖成功', 'post_id': post_id}), 201

@app.route('/api/forum/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    execute_db('UPDATE forum_posts SET view_count = view_count + 1 WHERE id = ?', (post_id,))
    
    post = execute_db('''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.parent_id,
               pr.username as author_name,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = -1) as dislike_count
        FROM forum_posts p
        JOIN parents pr ON p.parent_id = pr.id
        WHERE p.id = ?
    ''', (post_id,))
    
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    
    p = post[0]
    return jsonify({
        'id': p[0],
        'title': p[1],
        'content': p[2],
        'created_at': p[3],
        'view_count': p[4],
        'parent_id': p[5],
        'author_name': p[6],
        'like_count': p[7],
        'dislike_count': p[8]
    }), 200

@app.route('/api/forum/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    data = request.json or {}
    parent_id = data.get('parent_id')
    
    if parent_id:
        user_result = execute_db('SELECT role FROM parents WHERE id = ?', (parent_id,))
        if user_result:
            role = user_result[0][0]
            if role == 'admin':
                execute_db('DELETE FROM forum_comments WHERE post_id = ?', (post_id,))
                execute_db('DELETE FROM forum_votes WHERE post_id = ?', (post_id,))
                execute_db('DELETE FROM forum_posts WHERE id = ?', (post_id,))
                return jsonify({'message': '删除成功'}), 200
        
        post_result = execute_db('SELECT parent_id FROM forum_posts WHERE id = ?', (post_id,))
        if post_result and post_result[0][0] == parent_id:
            execute_db('DELETE FROM forum_comments WHERE post_id = ?', (post_id,))
            execute_db('DELETE FROM forum_votes WHERE post_id = ?', (post_id,))
            execute_db('DELETE FROM forum_posts WHERE id = ?', (post_id,))
            return jsonify({'message': '删除成功'}), 200
        
        return jsonify({'error': '无权删除此帖子'}), 403
    
    execute_db('DELETE FROM forum_comments WHERE post_id = ?', (post_id,))
    execute_db('DELETE FROM forum_votes WHERE post_id = ?', (post_id,))
    execute_db('DELETE FROM forum_posts WHERE id = ?', (post_id,))
    return jsonify({'message': '删除成功'}), 200

@app.route('/api/forum/comments', methods=['GET'])
def get_comments():
    post_id = request.args.get('post_id')
    if not post_id:
        return jsonify({'error': '帖子ID不能为空'}), 400
    
    comments = execute_db('''
        SELECT c.id, c.content, c.created_at, c.parent_id,
               pr.username as author_name,
               (SELECT COUNT(*) FROM forum_votes WHERE comment_id = c.id AND vote_type = 1) as like_count,
               (SELECT COUNT(*) FROM forum_votes WHERE comment_id = c.id AND vote_type = -1) as dislike_count
        FROM forum_comments c
        JOIN parents pr ON c.parent_id = pr.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
    ''', (post_id,))
    
    comments_data = [{
        'id': c[0],
        'content': c[1],
        'created_at': c[2],
        'parent_id': c[3],
        'author_name': c[4],
        'like_count': c[5],
        'dislike_count': c[6]
    } for c in comments]
    
    return jsonify(comments_data), 200

@app.route('/api/forum/comments', methods=['POST'])
def create_comment():
    data = request.json
    post_id = data.get('post_id')
    parent_id = data.get('parent_id')
    content = data.get('content')
    
    if not post_id or not parent_id or not content:
        return jsonify({'error': '帖子ID、家长ID和内容不能为空'}), 400
    
    result, comment_id = execute_db(
        'INSERT INTO forum_comments (post_id, parent_id, content) VALUES (?, ?, ?)',
        (post_id, parent_id, content), fetch_last_id=True
    )
    
    return jsonify({'message': '评论成功', 'comment_id': comment_id}), 201

@app.route('/api/forum/vote', methods=['POST'])
def vote():
    data = request.json
    parent_id = data.get('parent_id')
    vote_type = data.get('vote_type')
    post_id = data.get('post_id')
    comment_id = data.get('comment_id')
    
    if not parent_id or vote_type is None:
        return jsonify({'error': '参数不完整'}), 400
    
    if not post_id and not comment_id:
        return jsonify({'error': '必须指定帖子或评论'}), 400
    
    existing = execute_db('''
        SELECT id FROM forum_votes 
        WHERE parent_id = ? AND (post_id = ? OR comment_id = ?)
    ''', (parent_id, post_id, comment_id))
    
    if existing:
        execute_db('''
            UPDATE forum_votes SET vote_type = ? 
            WHERE parent_id = ? AND (post_id = ? OR comment_id = ?)
        ''', (vote_type, parent_id, post_id, comment_id))
    else:
        execute_db('''
            INSERT INTO forum_votes (parent_id, post_id, comment_id, vote_type)
            VALUES (?, ?, ?, ?)
        ''', (parent_id, post_id, comment_id, vote_type))
    
    return jsonify({'message': '投票成功'}), 200

@app.route('/api/upload/detection', methods=['POST'])
def upload_detection():
    data = request.json
    child_id = data.get('child_id')
    selective_attention = data.get('selective_attention')
    sustained_attention = data.get('sustained_attention')
    visual_tracking = data.get('visual_tracking')
    working_memory = data.get('working_memory')
    inhibitory_control = data.get('inhibitory_control')
    total_score = data.get('total_score')
    
    if not child_id:
        return jsonify({'error': '孩子ID不能为空'}), 400
    
    execute_db('''
        INSERT INTO detection_data (child_id, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (child_id, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score))
    
    return jsonify({'message': '检测数据上传成功'}), 201

@app.route('/api/upload/training', methods=['POST'])
def upload_training():
    data = request.json
    child_id = data.get('child_id')
    training_type = data.get('training_type')
    difficulty = data.get('difficulty')
    accuracy = data.get('accuracy')
    completion_time = data.get('completion_time')
    error_count = data.get('error_count')
    
    if not child_id or not training_type:
        return jsonify({'error': '孩子ID和训练类型不能为空'}), 400
    
    execute_db('''
        INSERT INTO training_data (child_id, training_type, difficulty, accuracy, completion_time, error_count)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (child_id, training_type, difficulty, accuracy, completion_time, error_count))
    
    return jsonify({'message': '训练数据上传成功'}), 201

@app.route('/api/get/detection', methods=['GET'])
def get_detection():
    child_id = request.args.get('child_id')
    
    if not child_id:
        return jsonify({'error': '孩子ID不能为空'}), 400
    
    result = execute_db('''
        SELECT timestamp, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score
        FROM detection_data
        WHERE child_id = ?
        ORDER BY timestamp DESC
    ''', (child_id,))
    
    data = [{
        'timestamp': row[0],
        'selective_attention': row[1],
        'sustained_attention': row[2],
        'visual_tracking': row[3],
        'working_memory': row[4],
        'inhibitory_control': row[5],
        'total_score': row[6]
    } for row in result]
    
    return jsonify(data), 200

@app.route('/api/get/training', methods=['GET'])
def get_training():
    child_id = request.args.get('child_id')
    
    if not child_id:
        return jsonify({'error': '孩子ID不能为空'}), 400
    
    result = execute_db('''
        SELECT timestamp, training_type, difficulty, accuracy, completion_time, error_count
        FROM training_data
        WHERE child_id = ?
        ORDER BY timestamp DESC
    ''', (child_id,))
    
    data = [{
        'timestamp': row[0],
        'training_type': row[1],
        'difficulty': row[2],
        'accuracy': row[3],
        'completion_time': row[4],
        'error_count': row[5]
    } for row in result]
    
    return jsonify(data), 200

@app.route('/api/badges', methods=['GET'])
def get_badges():
    badges = execute_db('SELECT id, name, description, icon FROM badges')
    badges_data = [{'id': b[0], 'name': b[1], 'description': b[2], 'icon': b[3]} for b in badges]
    return jsonify(badges_data), 200

@app.route('/api/badges/<int:child_id>', methods=['GET'])
def get_child_badges(child_id):
    badges = execute_db('''
        SELECT b.id, b.name, b.description, b.icon, ub.earned_at
        FROM badges b
        JOIN user_badges ub ON b.id = ub.badge_id
        WHERE ub.child_id = ?
        ORDER BY ub.earned_at DESC
    ''', (child_id,))
    
    badges_data = [{
        'id': b[0],
        'name': b[1],
        'description': b[2],
        'icon': b[3],
        'earned_at': b[4]
    } for b in badges]
    
    return jsonify(badges_data), 200

@app.route('/api/badges/award', methods=['POST'])
def award_badge():
    data = request.json
    child_id = data.get('child_id')
    badge_id = data.get('badge_id')
    
    if not child_id or not badge_id:
        return jsonify({'error': '参数不完整'}), 400
    
    existing = execute_db(
        'SELECT id FROM user_badges WHERE child_id = ? AND badge_id = ?',
        (child_id, badge_id)
    )
    
    if existing:
        return jsonify({'message': '已获得该勋章'}), 200
    
    execute_db(
        'INSERT INTO user_badges (child_id, badge_id) VALUES (?, ?)',
        (child_id, badge_id)
    )
    
    return jsonify({'message': '勋章授予成功'}), 201

@app.route('/api/knowledge/articles', methods=['GET'])
def get_knowledge_articles():
    import json
    
    knowledge_file = os.path.join(frontend_dir, 'knowledge', 'knowledge-data.json')
    
    try:
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            articles = data.get('articles', [])
            articles.sort(key=lambda x: x['date'], reverse=True)
            return jsonify(articles), 200
    except FileNotFoundError:
        return jsonify({'error': '知识文章文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/articles', methods=['POST'])
def add_knowledge_article():
    import json
    
    data = request.json
    title = data.get('title')
    content = data.get('content')
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    knowledge_file = os.path.join(frontend_dir, 'knowledge', 'knowledge-data.json')
    
    try:
        if os.path.exists(knowledge_file):
            with open(knowledge_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                articles = file_data.get('articles', [])
        else:
            articles = []
        
        max_id = max([article.get('id', 0) for article in articles], default=0)
        new_id = max_id + 1
        
        new_article = {
            'id': new_id,
            'title': title,
            'content': content,
            'author': data.get('author', '专业团队'),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'category': data.get('category', '未分类'),
            'tags': data.get('tags', []),
            'summary': data.get('summary', ''),
            'difficulty': data.get('difficulty', '初级'),
            'reading_time': data.get('reading_time', 3)
        }
        
        articles.append(new_article)
        
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump({'articles': articles}, f, ensure_ascii=False, indent=2)
        
        return jsonify({'message': '文章添加成功', 'article': new_article}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/articles/<int:article_id>', methods=['PUT'])
def update_knowledge_article(article_id):
    import json
    
    data = request.json
    title = data.get('title')
    content = data.get('content')
    
    if not title or not content:
        return jsonify({'error': '标题和内容不能为空'}), 400
    
    knowledge_file = os.path.join(frontend_dir, 'knowledge', 'knowledge-data.json')
    
    try:
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
            articles = file_data.get('articles', [])
        
        article_found = False
        for i, article in enumerate(articles):
            if article['id'] == article_id:
                articles[i] = {
                    'id': article_id,
                    'title': title,
                    'content': content,
                    'author': data.get('author', article.get('author', '专业团队')),
                    'date': data.get('date', article.get('date', datetime.now().strftime('%Y-%m-%d'))),
                    'category': data.get('category', article.get('category', '未分类')),
                    'tags': data.get('tags', article.get('tags', [])),
                    'summary': data.get('summary', article.get('summary', '')),
                    'difficulty': data.get('difficulty', article.get('difficulty', '初级')),
                    'reading_time': data.get('reading_time', article.get('reading_time', 3))
                }
                article_found = True
                break
        
        if not article_found:
            return jsonify({'error': '文章未找到'}), 404
        
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump({'articles': articles}, f, ensure_ascii=False, indent=2)
        
        return jsonify({'message': '文章更新成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/articles/<int:article_id>', methods=['DELETE'])
def delete_knowledge_article(article_id):
    import json
    
    knowledge_file = os.path.join(frontend_dir, 'knowledge', 'knowledge-data.json')
    
    try:
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
            articles = file_data.get('articles', [])
        
        original_length = len(articles)
        articles = [article for article in articles if article['id'] != article_id]
        
        if len(articles) == original_length:
            return jsonify({'error': '文章未找到'}), 404
        
        with open(knowledge_file, 'w', encoding='utf-8') as f:
            json.dump({'articles': articles}, f, ensure_ascii=False, indent=2)
        
        return jsonify({'message': '文章删除成功'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(frontend_dir, path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

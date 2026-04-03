from flask import Blueprint, request, jsonify
from database import execute_db
import sqlite3

auth_bp = Blueprint('auth', __name__)

def get_next_uid():
    result = execute_db('SELECT MAX(uid) FROM parents')
    max_uid = result[0][0] if result and result[0][0] else 99999
    return max_uid + 1

@auth_bp.route('/api/register', methods=['POST'])
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

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    result = execute_db(
        'SELECT id, uid, email, role, is_banned FROM parents WHERE username = ? AND password = ?',
        (username, password)
    )
    
    if not result:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    parent_id, uid, email, role, is_banned = result[0]
    
    if is_banned == 1:
        return jsonify({'error': '账户已封禁'}), 403
    
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

@auth_bp.route('/api/user/info', methods=['GET'])
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

@auth_bp.route('/api/user/change-password', methods=['POST'])
def change_password():
    data = request.json
    parent_id = data.get('parent_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not parent_id or not old_password or not new_password:
        return jsonify({'error': '参数不完整'}), 400
    
    user = execute_db('SELECT id, password FROM parents WHERE id = ?', (parent_id,))
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if user[0][1] != old_password:
        return jsonify({'error': '旧密码错误'}), 400
    
    execute_db('UPDATE parents SET password = ? WHERE id = ?', (new_password, parent_id))
    return jsonify({'message': '密码修改成功'}), 200

@auth_bp.route('/api/user/avatar', methods=['POST'])
def update_avatar():
    data = request.json
    parent_id = data.get('parent_id')
    avatar = data.get('avatar')
    
    if not parent_id or not avatar:
        return jsonify({'error': '参数不完整'}), 400
    
    execute_db('UPDATE parents SET avatar = ? WHERE id = ?', (avatar, parent_id))
    return jsonify({'message': '头像更新成功'}), 200

@auth_bp.route('/api/user/level/<int:parent_id>', methods=['GET'])
def get_user_level(parent_id):
    post_count = execute_db('SELECT COUNT(*) FROM forum_posts WHERE parent_id = ?', (parent_id,))[0][0]
    comment_count = execute_db('SELECT COUNT(*) FROM forum_comments WHERE parent_id = ?', (parent_id,))[0][0]
    like_received = execute_db('''
        SELECT COUNT(*) FROM forum_votes v
        JOIN forum_posts p ON v.post_id = p.id
        WHERE p.parent_id = ? AND v.vote_type = 1
    ''', (parent_id,))[0][0]
    favorite_count = execute_db('SELECT COUNT(*) FROM favorites WHERE parent_id = ?', (parent_id,))[0][0]
    
    experience = post_count * 10 + comment_count * 5 + like_received * 2
    level = 1 + experience // 100
    
    return jsonify({
        'post_count': post_count,
        'comment_count': comment_count,
        'like_received': like_received,
        'favorite_count': favorite_count,
        'experience': experience,
        'level': level
    }), 200

@auth_bp.route('/api/user/posts/<int:parent_id>', methods=['GET'])
def get_user_posts(parent_id):
    result = execute_db('''
        SELECT p.id, p.title, p.content, p.created_at, p.view_count, p.category_id, p.is_pinned, p.is_essential,
               (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) as comment_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count
        FROM forum_posts p
        WHERE p.parent_id = ?
        ORDER BY p.created_at DESC
    ''', (parent_id,))
    
    posts = [{
        'id': p[0],
        'title': p[1],
        'content': p[2],
        'created_at': p[3],
        'view_count': p[4],
        'category_id': p[5],
        'is_pinned': p[6],
        'is_essential': p[7],
        'comment_count': p[8],
        'like_count': p[9]
    } for p in result]
    
    return jsonify(posts), 200

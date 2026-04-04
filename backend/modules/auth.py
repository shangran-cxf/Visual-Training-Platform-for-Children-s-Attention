from flask import Blueprint, request, jsonify
from database import execute_db
import sqlite3
from utils.password_utils import hash_password, verify_password, is_bcrypt_hash
from middleware import generate_token
from utils import build_update_sql, check_user_exists, success_response, error_response

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
        hashed_password = hash_password(password)
        result, parent_id = execute_db(
            'INSERT INTO parents (uid, username, password, email, role) VALUES (?, ?, ?, ?, ?)',
            (uid, username, hashed_password, email, 'user'), fetch_last_id=True
        )
        
        for child in children:
            child_name = child.get('name')
            child_age = child.get('age')
            if child_name:
                execute_db(
                    'INSERT INTO children (parent_id, name, age) VALUES (?, ?, ?)',
                    (parent_id, child_name, child_age)
                )
        
        return jsonify({'parent_id': parent_id, 'uid': uid}), 201
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
        'SELECT id, uid, email, role, is_banned, password FROM parents WHERE username = ?',
        (username,)
    )
    
    if not result:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    parent_id, uid, email, role, is_banned, stored_password = result[0]
    
    if is_banned == 1:
        return jsonify({'error': '账户已封禁'}), 403
    
    password_valid = False
    need_upgrade = False
    
    if is_bcrypt_hash(stored_password):
        password_valid = verify_password(password, stored_password)
    else:
        if stored_password == password:
            password_valid = True
            need_upgrade = True
    
    if not password_valid:
        return jsonify({'error': '用户名或密码错误'}), 401
    
    if need_upgrade:
        hashed_password = hash_password(password)
        execute_db('UPDATE parents SET password = ? WHERE id = ?', (hashed_password, parent_id))
    
    children = execute_db(
        'SELECT id, name, age FROM children WHERE parent_id = ?',
        (parent_id,)
    )
    
    children_data = [{'id': c[0], 'name': c[1], 'age': c[2]} for c in children]
    
    token = generate_token(parent_id, role)
    
    return jsonify({
        'parent_id': parent_id,
        'uid': uid,
        'username': username,
        'role': role,
        'children': children_data,
        'token': token
    }), 200

@auth_bp.route('/api/user/query', methods=['GET'])
def query_user():
    query_type = request.args.get('type')
    value = request.args.get('value')
    
    if not query_type or not value:
        return error_response('缺少type或value参数', status=400)
    
    if query_type not in ['id', 'uid', 'username']:
        return error_response('type参数必须是id、uid或username', status=400)
    
    if query_type == 'id':
        result = execute_db(
            'SELECT id, uid, username, email, role, created_at FROM parents WHERE id = ?',
            (value,)
        )
    elif query_type == 'uid':
        result = execute_db(
            'SELECT id, uid, username, email, role, created_at FROM parents WHERE uid = ?',
            (value,)
        )
    else:
        result = execute_db(
            'SELECT id, uid, username, email, role, created_at FROM parents WHERE username = ?',
            (value,)
        )
    
    if not result:
        return error_response('用户不存在', status=404)
    
    row = result[0]
    return success_response({
        'id': row[0],
        'uid': row[1],
        'username': row[2],
        'email': row[3],
        'role': row[4],
        'created_at': row[5]
    })

@auth_bp.route('/api/user/change-password', methods=['POST'])
def change_password():
    data = request.json
    parent_id = data.get('parent_id')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not parent_id or not old_password or not new_password:
        return error_response('参数不完整', status=400)
    
    if not check_user_exists(user_id=parent_id):
        return error_response('用户不存在', status=404)
    
    user = execute_db('SELECT id, password FROM parents WHERE id = ?', (parent_id,))
    stored_password = user[0][1]
    password_valid = False
    
    if is_bcrypt_hash(stored_password):
        password_valid = verify_password(old_password, stored_password)
    else:
        password_valid = stored_password == old_password
    
    if not password_valid:
        return error_response('旧密码错误', status=400)
    
    hashed_password = hash_password(new_password)
    execute_db('UPDATE parents SET password = ? WHERE id = ?', (hashed_password, parent_id))
    return success_response(None, '密码修改成功')



@auth_bp.route('/api/verify-password', methods=['POST'])
def verify_password_endpoint():
    data = request.json
    parent_id = data.get('parent_id')
    password = data.get('password')
    
    if not parent_id or not password:
        return jsonify({'error': '参数不完整'}), 400
    
    result = execute_db(
        'SELECT id, password FROM parents WHERE id = ?',
        (parent_id,)
    )
    
    if not result:
        return jsonify({'valid': False}), 200
    
    stored_password = result[0][1]
    password_valid = False
    
    if is_bcrypt_hash(stored_password):
        password_valid = verify_password(password, stored_password)
    else:
        password_valid = stored_password == password
    
    return jsonify({'valid': password_valid}), 200

@auth_bp.route('/api/user/update', methods=['POST'])
def update_user_info():
    data = request.json
    parent_id = data.get('parent_id')
    username = data.get('username')
    email = data.get('email')
    avatar = data.get('avatar')
    
    if not parent_id:
        return error_response('缺少parent_id参数', status=400)
    
    if not check_user_exists(user_id=parent_id):
        return error_response('用户不存在', status=404)
    
    update_data = {}
    
    if username is not None:
        existing = execute_db('SELECT id FROM parents WHERE username = ? AND id != ?', (username, parent_id))
        if existing:
            return error_response('用户名已被使用', status=400)
        update_data['username'] = username
    
    if email is not None:
        update_data['email'] = email
    
    if avatar is not None:
        update_data['avatar'] = avatar
    
    if not update_data:
        return error_response('没有需要更新的字段', status=400)
    
    sql, params = build_update_sql('parents', update_data, 'id = ?')
    execute_db(sql, params + (parent_id,))
    
    return success_response(None, '更新成功')





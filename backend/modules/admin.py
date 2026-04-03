from flask import Blueprint, request, jsonify
from database import execute_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/users', methods=['GET'])
def get_users():
    result = execute_db('''
        SELECT p.id, p.uid, p.username, p.email, p.role, p.is_banned, p.created_at,
               (SELECT COUNT(*) FROM children WHERE parent_id = p.id) as child_count
        FROM parents p
        ORDER BY p.created_at DESC
    ''')
    
    users = [{
        'id': u[0],
        'uid': u[1],
        'username': u[2],
        'email': u[3],
        'role': u[4],
        'is_banned': u[5],
        'created_at': u[6],
        'child_count': u[7]
    } for u in result]
    
    return jsonify(users), 200

@admin_bp.route('/api/admin/ban_user', methods=['POST'])
def ban_user():
    data = request.json
    user_id = data.get('user_id')
    is_banned = data.get('is_banned')
    
    if user_id is None or is_banned is None:
        return jsonify({'error': '参数不完整'}), 400
    
    if is_banned not in [0, 1]:
        return jsonify({'error': 'is_banned参数只能是0或1'}), 400
    
    user = execute_db('SELECT id, role FROM parents WHERE id = ?', (user_id,))
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if user[0][1] == 'admin':
        return jsonify({'error': '不能封禁管理员账户'}), 403
    
    execute_db('UPDATE parents SET is_banned = ? WHERE id = ?', (is_banned, user_id))
    
    action = '封禁' if is_banned == 1 else '解封'
    return jsonify({'message': f'用户已{action}'}), 200

@admin_bp.route('/api/admin/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    user_id = data.get('user_id')
    
    if user_id is None:
        return jsonify({'error': '缺少user_id参数'}), 400
    
    user = execute_db('SELECT id FROM parents WHERE id = ?', (user_id,))
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    execute_db('UPDATE parents SET password = ? WHERE id = ?', ('123456', user_id))
    
    return jsonify({'message': '密码已重置为默认密码'}), 200

@admin_bp.route('/api/admin/edit_user', methods=['POST'])
def edit_user():
    data = request.json
    user_id = data.get('user_id')
    username = data.get('username')
    role = data.get('role')
    
    if user_id is None:
        return jsonify({'error': '缺少user_id参数'}), 400
    
    user = execute_db('SELECT id FROM parents WHERE id = ?', (user_id,))
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    if role is not None and role not in ['user', 'admin']:
        return jsonify({'error': '角色只能是user或admin'}), 400
    
    update_fields = []
    params = []
    
    if username is not None:
        update_fields.append('username = ?')
        params.append(username)
    
    if role is not None:
        update_fields.append('role = ?')
        params.append(role)
    
    if not update_fields:
        return jsonify({'error': '没有需要更新的字段'}), 400
    
    params.append(user_id)
    sql = f"UPDATE parents SET {', '.join(update_fields)} WHERE id = ?"
    execute_db(sql, tuple(params))
    
    return jsonify({'message': '用户信息更新成功'}), 200

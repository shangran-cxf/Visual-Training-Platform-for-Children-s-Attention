from flask import Blueprint, request, jsonify
from database import execute_db
from utils.password_utils import hash_password
from utils import build_update_sql, check_user_exists, is_admin, success_response, error_response

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/admin/users', methods=['GET'])
def get_users():
    result = execute_db('''
        SELECT p.id, p.uid, p.username, p.role, p.is_banned,
               (SELECT COUNT(*) FROM children WHERE parent_id = p.id) as child_count
        FROM parents p
        ORDER BY p.created_at DESC
    ''')
    
    users = [{
        'id': u[0],
        'uid': u[1],
        'username': u[2],
        'role': u[3],
        'is_banned': u[4],
        'child_count': u[5]
    } for u in result]
    
    return jsonify(users), 200

@admin_bp.route('/api/admin/ban_user', methods=['POST'])
def ban_user():
    data = request.json
    user_id = data.get('user_id')
    is_banned = data.get('is_banned')
    
    if user_id is None or is_banned is None:
        return error_response('参数不完整', status=400)
    
    if is_banned not in [0, 1]:
        return error_response('is_banned参数只能是0或1', status=400)
    
    if not check_user_exists(user_id=user_id):
        return error_response('用户不存在', status=404)
    
    if is_admin(user_id):
        return error_response('不能封禁管理员账户', status=403)
    
    execute_db('UPDATE parents SET is_banned = ? WHERE id = ?', (is_banned, user_id))
    
    return success_response(None, '操作成功')

@admin_bp.route('/api/admin/reset_password', methods=['POST'])
def reset_password():
    data = request.json
    user_id = data.get('user_id')
    
    if user_id is None:
        return error_response('缺少user_id参数', status=400)
    
    if not check_user_exists(user_id=user_id):
        return error_response('用户不存在', status=404)
    
    hashed_password = hash_password('123456')
    execute_db('UPDATE parents SET password = ? WHERE id = ?', (hashed_password, user_id))
    
    return success_response(None, '密码已重置为123456')

@admin_bp.route('/api/admin/edit_user', methods=['POST'])
def edit_user():
    data = request.json
    user_id = data.get('user_id')
    username = data.get('username')
    role = data.get('role')
    
    if user_id is None:
        return error_response('缺少user_id参数', status=400)
    
    if not check_user_exists(user_id=user_id):
        return error_response('用户不存在', status=404)
    
    if role is not None and role not in ['user', 'admin']:
        return error_response('角色只能是user或admin', status=400)
    
    update_data = {}
    
    if username is not None:
        update_data['username'] = username
    
    if role is not None:
        update_data['role'] = role
    
    if not update_data:
        return error_response('没有需要更新的字段', status=400)
    
    sql, params = build_update_sql('parents', update_data, 'id = ?')
    execute_db(sql, params + (user_id,))
    
    return success_response(None, '更新成功')

@admin_bp.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    users = execute_db('SELECT COUNT(*) FROM parents WHERE role = \'user\'')[0][0]
    admins = execute_db('SELECT COUNT(*) FROM parents WHERE role = \'admin\'')[0][0]
    banned = execute_db('SELECT COUNT(*) FROM parents WHERE is_banned = 1')[0][0]
    children = execute_db('SELECT COUNT(*) FROM children')[0][0]
    sessions = execute_db('SELECT COUNT(*) FROM training_sessions')[0][0]
    posts = execute_db('SELECT COUNT(*) FROM forum_posts')[0][0]
    
    return jsonify({
        'users': users,
        'admins': admins,
        'banned': banned,
        'children': children,
        'sessions': sessions,
        'posts': posts
    }), 200

@admin_bp.route('/api/admin/all-training', methods=['GET'])
def get_all_training():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    result = execute_db('''
        SELECT ts.id, c.name, p.username, ts.game_type, ts.start_time, ts.duration, ss.overall_score as final_score
        FROM training_sessions ts
        JOIN children c ON ts.child_id = c.id
        JOIN parents p ON c.parent_id = p.id
        LEFT JOIN session_summaries ss ON ts.id = ss.session_id
        ORDER BY ts.start_time DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    total = execute_db('SELECT COUNT(*) FROM training_sessions')[0][0]
    
    records = [{
        'id': r[0],
        'child_name': r[1],
        'parent_name': r[2],
        'game_type': r[3],
        'start_time': r[4],
        'duration': r[5],
        'score': r[6]
    } for r in result]
    
    return jsonify({'total': total, 'records': records}), 200

@admin_bp.route('/api/admin/all-children', methods=['GET'])
def get_all_children():
    result = execute_db('''
        SELECT c.id, c.name, c.age, p.username,
               (SELECT COUNT(*) FROM training_sessions WHERE child_id = c.id) as training_count
        FROM children c
        JOIN parents p ON c.parent_id = p.id
        ORDER BY c.created_at DESC
    ''')
    
    children = [{
        'id': c[0],
        'name': c[1],
        'age': c[2],
        'parent_name': c[3],
        'training_count': c[4]
    } for c in result]
    
    return jsonify(children), 200

@admin_bp.route('/api/admin/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not check_user_exists(user_id=user_id):
        return error_response('用户不存在', status=404)
    
    if is_admin(user_id):
        return error_response('不能删除管理员账户', status=403)
    
    child_ids = execute_db('SELECT id FROM children WHERE parent_id = ?', (user_id,))
    for (child_id,) in child_ids:
        execute_db('DELETE FROM user_badges WHERE child_id = ?', (child_id,))
        execute_db('DELETE FROM session_summaries WHERE child_id = ?', (child_id,))
        execute_db('DELETE FROM child_reports WHERE child_id = ?', (child_id,))
        execute_db('DELETE FROM detection_data WHERE child_id = ?', (child_id,))
    
    session_ids = execute_db('''
        SELECT ts.id FROM training_sessions ts
        JOIN children c ON ts.child_id = c.id
        WHERE c.parent_id = ?
    ''', (user_id,))
    for (session_id,) in session_ids:
        execute_db('DELETE FROM game_raw_data WHERE session_id = ?', (session_id,))
        execute_db('DELETE FROM vision_raw_data WHERE session_id = ?', (session_id,))
    
    execute_db('DELETE FROM training_sessions WHERE child_id IN (SELECT id FROM children WHERE parent_id = ?)', (user_id,))
    execute_db('DELETE FROM children WHERE parent_id = ?', (user_id,))
    execute_db('DELETE FROM forum_comments WHERE parent_id = ?', (user_id,))
    execute_db('DELETE FROM forum_votes WHERE parent_id = ?', (user_id,))
    execute_db('DELETE FROM favorites WHERE parent_id = ?', (user_id,))
    execute_db('DELETE FROM reports WHERE parent_id = ?', (user_id,))
    execute_db('DELETE FROM forum_posts WHERE parent_id = ?', (user_id,))
    execute_db('DELETE FROM parents WHERE id = ?', (user_id,))
    
    return success_response(None, '用户删除成功')

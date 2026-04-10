from flask import Blueprint, request, jsonify
from database import execute_db
from utils import build_update_sql, check_user_exists, success_response, error_response

children_bp = Blueprint('children', __name__)

@children_bp.route('/api/children', methods=['POST'])
def add_child():
    data = request.json
    parent_id = data.get('parent_id')
    name = data.get('name')
    age = data.get('age')
    
    if not parent_id or not name:
        return error_response('家长ID和孩子姓名不能为空', status=400)
    
    result, child_id = execute_db(
        'INSERT INTO children (parent_id, name, age) VALUES (?, ?, ?)',
        (parent_id, name, age), fetch_last_id=True
    )
    
    return success_response({'child_id': child_id}, '添加成功')

@children_bp.route('/api/children/<int:parent_id>', methods=['GET'])
def get_children(parent_id):
    result = execute_db(
        'SELECT id, name, age FROM children WHERE parent_id = ?',
        (parent_id,)
    )
    
    children = [{'id': c[0], 'name': c[1], 'age': c[2]} for c in result]
    return jsonify(children), 200

@children_bp.route('/api/children/<int:child_id>', methods=['DELETE'])
def delete_child(child_id):
    execute_db('DELETE FROM children WHERE id = ?', (child_id,))
    return success_response(None, '删除成功')

@children_bp.route('/api/children/<int:child_id>', methods=['PUT'])
def update_child(child_id):
    data = request.json
    name = data.get('name')
    age = data.get('age')
    
    child = execute_db('SELECT id FROM children WHERE id = ?', (child_id,))
    if not child:
        return error_response('孩子不存在', status=404)
    
    update_data = {}
    
    if name is not None:
        update_data['name'] = name
    
    if age is not None:
        update_data['age'] = age
    
    if not update_data:
        return error_response('没有需要更新的字段', status=400)
    
    sql, params = build_update_sql('children', update_data, 'id = ?')
    execute_db(sql, params + (child_id,))
    
    return success_response(None, '更新成功')

@children_bp.route('/api/children/<int:child_id>/stats', methods=['GET'])
def get_child_stats(child_id):
    child = execute_db('SELECT id FROM children WHERE id = ?', (child_id,))
    if not child:
        return error_response('孩子不存在', status=404)
    
    # 单次查询获取所有统计数据
    stats_result = execute_db('''
        SELECT 
            COUNT(ts.id) as training_count,
            COALESCE(SUM(ts.duration), 0) as total_time,
            COALESCE(AVG(ss.overall_score), 0) as avg_score,
            COUNT(ub.id) as badges_count
        FROM training_sessions ts
        LEFT JOIN session_summaries ss ON ts.id = ss.session_id
        LEFT JOIN user_badges ub ON ts.child_id = ub.child_id
        WHERE ts.child_id = ?
    ''', (child_id,))
    
    return success_response({
        'training_count': stats_result[0][0],
        'training_time': stats_result[0][1],
        'avg_score': round(stats_result[0][2], 2) if stats_result[0][2] else 0,
        'badges_count': stats_result[0][3]
    })

@children_bp.route('/api/children/<int:child_id>/recent-training', methods=['GET'])
def get_child_recent_training(child_id):
    limit = request.args.get('limit', 10)
    try:
        limit = int(limit)
    except ValueError:
        limit = 10
    
    child = execute_db('SELECT id FROM children WHERE id = ?', (child_id,))
    if not child:
        return error_response('孩子不存在', status=404)
    
    result = execute_db('''
        SELECT ss.game_type, ss.overall_score as final_score, ss.performance_level, ss.created_at
        FROM session_summaries ss
        WHERE ss.child_id = ?
        ORDER BY ss.created_at DESC
        LIMIT ?
    ''', (child_id, limit))
    
    training_records = [{
        'game_type': r[0],
        'score': r[1],
        'level': r[2],
        'date': r[3]
    } for r in result]
    
    return success_response(training_records)

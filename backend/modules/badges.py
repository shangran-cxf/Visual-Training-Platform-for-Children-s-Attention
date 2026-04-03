from flask import Blueprint, request, jsonify
from database import execute_db

badges_bp = Blueprint('badges', __name__)

@badges_bp.route('/api/badges', methods=['GET'])
def get_all_badges():
    result = execute_db(
        'SELECT id, name, description, icon, requirement_type, requirement_value, created_at FROM badges'
    )
    
    badges = [{
        'id': b[0],
        'name': b[1],
        'description': b[2],
        'icon': b[3],
        'requirement_type': b[4],
        'requirement_value': b[5],
        'created_at': b[6]
    } for b in result]
    
    return jsonify(badges), 200

@badges_bp.route('/api/badges/<int:child_id>', methods=['GET'])
def get_child_badges(child_id):
    result = execute_db(
        '''SELECT b.id, b.name, b.description, b.icon, b.requirement_type, 
                  b.requirement_value, ub.earned_at
           FROM badges b
           INNER JOIN user_badges ub ON b.id = ub.badge_id
           WHERE ub.child_id = ?
           ORDER BY ub.earned_at DESC''',
        (child_id,)
    )
    
    badges = [{
        'id': b[0],
        'name': b[1],
        'description': b[2],
        'icon': b[3],
        'requirement_type': b[4],
        'requirement_value': b[5],
        'earned_at': b[6]
    } for b in result]
    
    return jsonify(badges), 200

@badges_bp.route('/api/badges/award', methods=['POST'])
def award_badge():
    data = request.json
    child_id = data.get('child_id')
    badge_id = data.get('badge_id')
    
    if not child_id or not badge_id:
        return jsonify({'error': '孩子ID和勋章ID不能为空'}), 400
    
    existing = execute_db(
        'SELECT id FROM user_badges WHERE child_id = ? AND badge_id = ?',
        (child_id, badge_id)
    )
    
    if existing:
        return jsonify({'error': '该孩子已获得此勋章'}), 400
    
    execute_db(
        'INSERT INTO user_badges (child_id, badge_id) VALUES (?, ?)',
        (child_id, badge_id)
    )
    
    return jsonify({'message': '勋章授予成功'}), 201

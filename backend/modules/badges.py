from flask import Blueprint, request, jsonify
from database import execute_db
from config import BADGES

badges_bp = Blueprint('badges', __name__)

@badges_bp.route('/api/badges', methods=['GET'])
def get_all_badges():
    return jsonify(BADGES), 200

@badges_bp.route('/api/badges/<int:child_id>', methods=['GET'])
def get_child_badges(child_id):
    result = execute_db(
        '''SELECT badge_id, earned_at
           FROM user_badges
           WHERE child_id = ?
           ORDER BY earned_at DESC''',
        (child_id,)
    )
    
    badge_dict = {b['id']: b for b in BADGES}
    
    badges = []
    for row in result:
        badge_id = row[0]
        if badge_id in badge_dict:
            badge = badge_dict[badge_id].copy()
            badge['earned_at'] = row[1]
            badges.append(badge)
    
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

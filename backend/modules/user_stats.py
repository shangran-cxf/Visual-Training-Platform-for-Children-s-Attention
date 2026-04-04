from flask import Blueprint, jsonify
from database import execute_db
from utils import check_user_exists, success_response, error_response

user_stats_bp = Blueprint('user_stats', __name__)

@user_stats_bp.route('/api/user/level/<int:parent_id>', methods=['GET'])
def get_user_level(parent_id):
    post_count = execute_db('SELECT COUNT(*) FROM forum_posts WHERE parent_id = ?', (parent_id,))[0][0]
    comment_count = execute_db('SELECT COUNT(*) FROM forum_comments WHERE parent_id = ?', (parent_id,))[0][0]
    like_received = execute_db('''
        SELECT COUNT(*) FROM forum_votes v
        JOIN forum_posts p ON v.post_id = p.id
        WHERE p.parent_id = ? AND v.vote_type = 1
    ''', (parent_id,))[0][0]
    
    experience = post_count * 10 + comment_count * 5 + like_received * 2
    level = 1 + experience // 100
    
    return jsonify({'level': level, 'experience': experience}), 200

@user_stats_bp.route('/api/user/posts/<int:parent_id>', methods=['GET'])
def get_user_posts(parent_id):
    result = execute_db('''
        SELECT p.id, p.title, p.created_at, p.view_count,
               (SELECT COUNT(*) FROM forum_comments WHERE post_id = p.id) as comment_count,
               (SELECT COUNT(*) FROM forum_votes WHERE post_id = p.id AND vote_type = 1) as like_count
        FROM forum_posts p
        WHERE p.parent_id = ?
        ORDER BY p.created_at DESC
    ''', (parent_id,))
    
    posts = [{
        'id': p[0],
        'title': p[1],
        'created_at': p[2],
        'view_count': p[3],
        'comment_count': p[4],
        'like_count': p[5]
    } for p in result]
    
    return jsonify(posts), 200

@user_stats_bp.route('/api/user/stats/<int:parent_id>', methods=['GET'])
def get_user_stats(parent_id):
    if not check_user_exists(user_id=parent_id):
        return error_response('用户不存在', status=404)
    
    children = execute_db('SELECT id FROM children WHERE parent_id = ?', (parent_id,))
    child_ids = [c[0] for c in children]
    
    total_training_sessions = 0
    total_training_time = 0
    avg_score = 0
    
    if child_ids:
        placeholders = ','.join('?' * len(child_ids))
        total_training_sessions = execute_db(
            f'SELECT COUNT(*) FROM training_sessions WHERE child_id IN ({placeholders})',
            tuple(child_ids)
        )[0][0]
        
        total_training_time = execute_db(
            f'SELECT COALESCE(SUM(duration), 0) FROM training_sessions WHERE child_id IN ({placeholders})',
            tuple(child_ids)
        )[0][0]
        
        score_result = execute_db(
            f'SELECT AVG(final_score) FROM training_details WHERE child_id IN ({placeholders})',
            tuple(child_ids)
        )
        avg_score = round(score_result[0][0], 2) if score_result[0][0] else 0
    
    post_count = execute_db('SELECT COUNT(*) FROM forum_posts WHERE parent_id = ?', (parent_id,))[0][0]
    comment_count = execute_db('SELECT COUNT(*) FROM forum_comments WHERE parent_id = ?', (parent_id,))[0][0]
    
    return success_response({
        'children_count': len(child_ids),
        'training_count': total_training_sessions,
        'training_time': total_training_time,
        'avg_score': avg_score,
        'post_count': post_count,
        'comment_count': comment_count
    })

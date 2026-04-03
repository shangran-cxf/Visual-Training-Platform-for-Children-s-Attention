import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from database import execute_db
from config import GAME_TYPES, SCORING_WEIGHTS

data_collector_bp = Blueprint('data_collector', __name__)

def generate_session_token():
    return uuid.uuid4().hex

def is_request_processed(request_id):
    if not request_id:
        return False
    result = execute_db(
        'SELECT id FROM processed_requests WHERE request_id = ?',
        (request_id,)
    )
    return len(result) > 0

def mark_request_processed(request_id):
    if request_id:
        execute_db(
            'INSERT INTO processed_requests (request_id) VALUES (?)',
            (request_id,)
        )

def check_active_session(child_id, game_type):
    result = execute_db('''
        SELECT id FROM training_sessions 
        WHERE child_id = ? AND game_type = ? AND status = 'active'
    ''', (child_id, game_type))
    return result[0][0] if result else None

def get_session_info(session_id):
    result = execute_db('''
        SELECT id, child_id, game_type, session_token, device_id, start_time, 
               status, last_activity
        FROM training_sessions WHERE id = ?
    ''', (session_id,))
    if result:
        row = result[0]
        return {
            'id': row[0],
            'child_id': row[1],
            'game_type': row[2],
            'session_token': row[3],
            'device_id': row[4],
            'start_time': row[5],
            'status': row[6],
            'last_activity': row[7]
        }
    return None

def calculate_session_summary(session_id, child_id, game_type, final_score, total_accuracy):
    game_data = execute_db('''
        SELECT score, accuracy, level FROM game_raw_data 
        WHERE session_id = ? ORDER BY timestamp
    ''', (session_id,))
    
    total_score = final_score or 0
    total_errors = 0
    levels_completed = set()
    
    for row in game_data:
        if row[0]:
            total_score += row[0]
        if row[1] is not None:
            pass
        if row[2]:
            levels_completed.add(row[2])
    
    vision_data = execute_db('''
        SELECT attention_score, head_yaw, head_pitch, blink_rate, focus_duration, face_detected
        FROM vision_raw_data WHERE session_id = ? ORDER BY timestamp
    ''', (session_id,))
    
    attention_scores = []
    head_deviations = []
    blink_rates = []
    total_focus_time = 0
    distraction_count = 0
    
    for row in vision_data:
        if row[0] is not None:
            attention_scores.append(row[0])
        if row[1] is not None and row[2] is not None:
            deviation = (row[1] ** 2 + row[2] ** 2) ** 0.5
            head_deviations.append(deviation)
        if row[3] is not None:
            blink_rates.append(row[3])
        if row[4] is not None:
            total_focus_time += row[4]
        if row[5] == 0:
            distraction_count += 1
    
    avg_attention = sum(attention_scores) / len(attention_scores) if attention_scores else 0
    max_attention = max(attention_scores) if attention_scores else 0
    min_attention = min(attention_scores) if attention_scores else 0
    
    if len(attention_scores) > 1:
        variance = sum((x - avg_attention) ** 2 for x in attention_scores) / len(attention_scores)
        attention_stability = max(0, 100 - (variance ** 0.5))
    else:
        attention_stability = 100 if attention_scores else 0
    
    avg_head_deviation = sum(head_deviations) / len(head_deviations) if head_deviations else 0
    avg_blink_rate = sum(blink_rates) / len(blink_rates) if blink_rates else 0
    
    session_info = execute_db(
        'SELECT start_time FROM training_sessions WHERE id = ?',
        (session_id,)
    )
    total_time = 0
    if session_info:
        start_time = datetime.fromisoformat(session_info[0][0])
        total_time = int((datetime.now() - start_time).total_seconds())
    
    visual_score = avg_attention * SCORING_WEIGHTS.get('visual', 0.6)
    game_score = (total_accuracy or 0) * SCORING_WEIGHTS.get('game', 0.4)
    overall_score = visual_score + game_score
    
    if overall_score >= 90:
        performance_level = '优秀'
    elif overall_score >= 75:
        performance_level = '良好'
    elif overall_score >= 60:
        performance_level = '一般'
    else:
        performance_level = '需改进'
    
    return {
        'final_score': total_score,
        'total_accuracy': total_accuracy,
        'total_time': total_time,
        'total_errors': total_errors,
        'levels_completed': len(levels_completed),
        'avg_attention_score': round(avg_attention, 2),
        'max_attention_score': round(max_attention, 2),
        'min_attention_score': round(min_attention, 2),
        'attention_stability': round(attention_stability, 2),
        'avg_head_deviation': round(avg_head_deviation, 2),
        'avg_blink_rate': round(avg_blink_rate, 2),
        'total_focus_time': round(total_focus_time, 2),
        'distraction_count': distraction_count,
        'overall_score': round(overall_score, 2),
        'performance_level': performance_level
    }

def check_and_award_badges(child_id, summary):
    earned_badges = []
    
    training_count = execute_db(
        'SELECT COUNT(*) FROM session_summaries WHERE child_id = ?',
        (child_id,)
    )[0][0] + 1
    
    if training_count == 1:
        badge = execute_db(
            "SELECT id, name, icon FROM badges WHERE requirement_type = 'training_count' AND requirement_value = 1"
        )
        if badge:
            execute_db(
                'INSERT OR IGNORE INTO user_badges (child_id, badge_id) VALUES (?, ?)',
                (child_id, badge[0][0])
            )
            earned_badges.append({'id': badge[0][0], 'name': badge[0][1], 'icon': badge[0][2]})
    
    if training_count == 50:
        badge = execute_db(
            "SELECT id, name, icon FROM badges WHERE requirement_type = 'training_count' AND requirement_value = 50"
        )
        if badge:
            execute_db(
                'INSERT OR IGNORE INTO user_badges (child_id, badge_id) VALUES (?, ?)',
                (child_id, badge[0][0])
            )
            earned_badges.append({'id': badge[0][0], 'name': badge[0][1], 'icon': badge[0][2]})
    
    if summary.get('total_accuracy') == 100:
        badge = execute_db(
            "SELECT id, name, icon FROM badges WHERE requirement_type = 'perfect_accuracy'"
        )
        if badge:
            execute_db(
                'INSERT OR IGNORE INTO user_badges (child_id, badge_id) VALUES (?, ?)',
                (child_id, badge[0][0])
            )
            earned_badges.append({'id': badge[0][0], 'name': badge[0][1], 'icon': badge[0][2]})
    
    if summary.get('overall_score', 0) >= 95:
        badge = execute_db(
            "SELECT id, name, icon FROM badges WHERE requirement_type = 'total_score' AND requirement_value = 95"
        )
        if badge:
            execute_db(
                'INSERT OR IGNORE INTO user_badges (child_id, badge_id) VALUES (?, ?)',
                (child_id, badge[0][0])
            )
            earned_badges.append({'id': badge[0][0], 'name': badge[0][1], 'icon': badge[0][2]})
    
    return earned_badges

def generate_recommendations(summary, game_type):
    recommendations = []
    
    if summary.get('avg_attention_score', 0) < 70:
        recommendations.append('建议增加专注力训练，可以尝试持续性注意力游戏')
    
    if summary.get('attention_stability', 0) < 60:
        recommendations.append('注意力稳定性有待提高，建议减少训练环境干扰')
    
    if summary.get('total_accuracy', 0) < 70:
        recommendations.append('正确率偏低，建议降低难度等级循序渐进')
    
    if summary.get('distraction_count', 0) > 5:
        recommendations.append('训练过程中分心较多，建议选择安静环境进行训练')
    
    if summary.get('avg_head_deviation', 0) > 30:
        recommendations.append('头部姿态变化较大，注意保持正确的坐姿')
    
    game_info = GAME_TYPES.get(game_type, {})
    dimensions = game_info.get('dimensions', [])
    
    if 'working_memory' in dimensions and summary.get('overall_score', 0) >= 90:
        badge = execute_db(
            "SELECT id, name, icon FROM badges WHERE requirement_type = 'memory_score' AND requirement_value = 90"
        )
        if badge:
            recommendations.append(f'工作记忆表现出色！已解锁"{badge[0][1]}"成就')
    
    if 'visual_tracking' in dimensions and summary.get('overall_score', 0) >= 90:
        badge = execute_db(
            "SELECT id, name, icon FROM badges WHERE requirement_type = 'tracking_score' AND requirement_value = 90"
        )
        if badge:
            recommendations.append(f'视觉追踪表现出色！已解锁"{badge[0][1]}"成就')
    
    if not recommendations:
        recommendations.append('表现良好，继续保持！')
    
    return recommendations

@data_collector_bp.route('/api/training/session/start', methods=['POST'])
def start_session():
    data = request.json
    child_id = data.get('child_id')
    game_type = data.get('game_type')
    device_id = data.get('device_id')
    
    if not child_id or not game_type:
        return jsonify({'error': 'child_id 和 game_type 不能为空'}), 400
    
    if game_type not in GAME_TYPES:
        return jsonify({'error': f'无效的游戏类型，支持的类型: {list(GAME_TYPES.keys())}'}), 400
    
    child = execute_db('SELECT id FROM children WHERE id = ?', (child_id,))
    if not child:
        return jsonify({'error': '孩子不存在'}), 404
    
    active_session_id = check_active_session(child_id, game_type)
    if active_session_id:
        return jsonify({
            'error': '该孩子已有同类型的活跃会话',
            'active_session_id': active_session_id
        }), 409
    
    session_token = generate_session_token()
    
    result, session_id = execute_db('''
        INSERT INTO training_sessions (child_id, game_type, session_token, device_id, status)
        VALUES (?, ?, ?, ?, 'active')
    ''', (child_id, game_type, session_token, device_id), fetch_last_id=True)
    
    return jsonify({
        'message': '训练会话已创建',
        'session_id': session_id,
        'session_token': session_token,
        'game_type': game_type,
        'game_name': GAME_TYPES[game_type]['name']
    }), 201

@data_collector_bp.route('/api/training/game-data', methods=['POST'])
def upload_game_data():
    data = request.json
    session_id = data.get('session_id')
    request_id = data.get('request_id')
    event_type = data.get('event_type')
    event_data = data.get('event_data')
    score = data.get('score')
    accuracy = data.get('accuracy')
    level = data.get('level')
    
    if not session_id or not event_type:
        return jsonify({'error': 'session_id 和 event_type 不能为空'}), 400
    
    session_info = get_session_info(session_id)
    if not session_info:
        return jsonify({'error': '会话不存在'}), 404
    
    if session_info['status'] != 'active':
        return jsonify({'error': '会话已结束'}), 400
    
    if is_request_processed(request_id):
        return jsonify({'message': '请求已处理，跳过重复数据'}), 200
    
    event_data_json = json.dumps(event_data) if event_data else None
    
    execute_db('''
        INSERT INTO game_raw_data (session_id, event_type, event_data, score, accuracy, level)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (session_id, event_type, event_data_json, score, accuracy, level))
    
    mark_request_processed(request_id)
    
    execute_db(
        'UPDATE training_sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?',
        (session_id,)
    )
    
    return jsonify({'message': '游戏数据上传成功'}), 201

@data_collector_bp.route('/api/training/vision-data', methods=['POST'])
def upload_vision_data():
    data = request.json
    session_id = data.get('session_id')
    request_id = data.get('request_id')
    attention_score = data.get('attention_score')
    face_detected = data.get('face_detected', 1)
    head_yaw = data.get('head_yaw')
    head_pitch = data.get('head_pitch')
    face_area = data.get('face_area')
    blink_rate = data.get('blink_rate')
    focus_duration = data.get('focus_duration')
    
    if not session_id:
        return jsonify({'error': 'session_id 不能为空'}), 400
    
    session_info = get_session_info(session_id)
    if not session_info:
        return jsonify({'error': '会话不存在'}), 404
    
    if session_info['status'] != 'active':
        return jsonify({'error': '会话已结束'}), 400
    
    if is_request_processed(request_id):
        return jsonify({'message': '请求已处理，跳过重复数据'}), 200
    
    execute_db('''
        INSERT INTO vision_raw_data 
        (session_id, attention_score, face_detected, head_yaw, head_pitch, face_area, blink_rate, focus_duration)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, attention_score, face_detected, head_yaw, head_pitch, face_area, blink_rate, focus_duration))
    
    mark_request_processed(request_id)
    
    execute_db(
        'UPDATE training_sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?',
        (session_id,)
    )
    
    return jsonify({'message': '视觉数据上传成功'}), 201

@data_collector_bp.route('/api/training/session/end', methods=['POST'])
def end_session():
    data = request.json
    session_id = data.get('session_id')
    final_score = data.get('final_score', 0)
    total_accuracy = data.get('total_accuracy', 0)
    
    if not session_id:
        return jsonify({'error': 'session_id 不能为空'}), 400
    
    session_info = get_session_info(session_id)
    if not session_info:
        return jsonify({'error': '会话不存在'}), 404
    
    if session_info['status'] != 'active':
        return jsonify({'error': '会话已结束'}), 400
    
    summary = calculate_session_summary(
        session_id, 
        session_info['child_id'], 
        session_info['game_type'],
        final_score,
        total_accuracy
    )
    
    execute_db('''
        INSERT INTO session_summaries 
        (session_id, child_id, game_type, final_score, total_accuracy, total_time, 
         total_errors, levels_completed, avg_attention_score, max_attention_score, 
         min_attention_score, attention_stability, avg_head_deviation, avg_blink_rate, 
         total_focus_time, distraction_count, overall_score, performance_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id, session_info['child_id'], session_info['game_type'],
        summary['final_score'], summary['total_accuracy'], summary['total_time'],
        summary['total_errors'], summary['levels_completed'], summary['avg_attention_score'],
        summary['max_attention_score'], summary['min_attention_score'], summary['attention_stability'],
        summary['avg_head_deviation'], summary['avg_blink_rate'], summary['total_focus_time'],
        summary['distraction_count'], summary['overall_score'], summary['performance_level']
    ))
    
    execute_db('''
        UPDATE training_sessions 
        SET end_time = CURRENT_TIMESTAMP, status = 'completed', 
            duration = ?, last_activity = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (summary['total_time'], session_id))
    
    earned_badges = check_and_award_badges(session_info['child_id'], summary)
    recommendations = generate_recommendations(summary, session_info['game_type'])
    
    return jsonify({
        'message': '训练会话已结束',
        'session_id': session_id,
        'summary': summary,
        'earned_badges': earned_badges,
        'recommendations': recommendations
    }), 200

@data_collector_bp.route('/api/training/session/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'error': 'session_id 不能为空'}), 400
    
    session_info = get_session_info(session_id)
    if not session_info:
        return jsonify({'error': '会话不存在'}), 404
    
    if session_info['status'] != 'active':
        return jsonify({'error': '会话已结束', 'status': session_info['status']}), 400
    
    execute_db(
        'UPDATE training_sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?',
        (session_id,)
    )
    
    return jsonify({
        'message': '心跳更新成功',
        'session_id': session_id,
        'status': 'active'
    }), 200

@data_collector_bp.route('/api/training/session/interrupt', methods=['POST'])
def interrupt_session():
    data = request.json
    session_id = data.get('session_id')
    current_state = data.get('current_state')
    
    if not session_id:
        return jsonify({'error': 'session_id 不能为空'}), 400
    
    session_info = get_session_info(session_id)
    if not session_info:
        return jsonify({'error': '会话不存在'}), 404
    
    if session_info['status'] != 'active':
        return jsonify({'error': '会话已结束', 'status': session_info['status']}), 400
    
    if current_state:
        state_json = json.dumps(current_state)
        execute_db('''
            INSERT INTO game_raw_data (session_id, event_type, event_data)
            VALUES (?, 'interrupt', ?)
        ''', (session_id, state_json))
    
    execute_db('''
        UPDATE training_sessions 
        SET end_time = CURRENT_TIMESTAMP, status = 'interrupted', 
            last_activity = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (session_id,))
    
    return jsonify({
        'message': '会话已中断',
        'session_id': session_id,
        'status': 'interrupted'
    }), 200

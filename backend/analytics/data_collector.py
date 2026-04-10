import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from database import execute_db
from config import GAME_TYPES, SCORING_WEIGHTS, DEFAULT_GAME_DATA, BADGES
from analytics.scoring import calculate_score, calculate_vision_scores, get_performance_level
from utils.response_utils import success_response, error_response
from middleware import require_auth
from utils.error_codes import (
    VALIDATION_ERROR, NOT_FOUND, SESSION_NOT_FOUND,
    SESSION_EXPIRED, CHILD_NOT_BELONG, ACTIVE_SESSION_EXISTS,
    INTERNAL_ERROR
)

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
    game_config = GAME_TYPES.get(game_type, {})
    attention_type = game_config.get('attention_type', 'selective')
    
    game_data_rows = execute_db('''
        SELECT score, accuracy, level, time, correct, error, miss, leave, obstacle,
               total_target, total_step, total_click, total_trial, memory_load,
               order_error, late_error_ratio, mean_rt, reaction_times
        FROM game_raw_data 
        WHERE session_id = ? ORDER BY timestamp
    ''', (session_id,))
    
    aggregated_game_data = {
        'time': 0,
        'correct': 0,
        'error': 0,
        'miss': 0,
        'leave': 0,
        'obstacle': 0,
        'total_target': 1,
        'total_step': 1,
        'total_click': 1,
        'total_trial': 1,
        'memory_load': 1,
        'order_error': 0,
        'late_error_ratio': 0,
        'mean_rt': 1000,
        'reaction_times': []
    }
    
    levels_completed = set()
    reaction_times_all = []
    
    for row in game_data_rows:
        if row[0]:
            pass
        if row[1] is not None:
            pass
        if row[2]:
            levels_completed.add(row[2])
        
        if row[3] is not None:
            aggregated_game_data['time'] = max(aggregated_game_data['time'], row[3])
        if row[4] is not None:
            aggregated_game_data['correct'] += row[4]
        if row[5] is not None:
            aggregated_game_data['error'] += row[5]
        if row[6] is not None:
            aggregated_game_data['miss'] += row[6]
        if row[7] is not None:
            aggregated_game_data['leave'] += row[7]
        if row[8] is not None:
            aggregated_game_data['obstacle'] += row[8]
        if row[9] is not None and row[9] > 0:
            aggregated_game_data['total_target'] = row[9]
        if row[10] is not None and row[10] > 0:
            aggregated_game_data['total_step'] = row[10]
        if row[11] is not None and row[11] > 0:
            aggregated_game_data['total_click'] = row[11]
        if row[12] is not None and row[12] > 0:
            aggregated_game_data['total_trial'] = row[12]
        if row[13] is not None and row[13] > 0:
            aggregated_game_data['memory_load'] = row[13]
        if row[14] is not None:
            aggregated_game_data['order_error'] += row[14]
        if row[15] is not None:
            aggregated_game_data['late_error_ratio'] = row[15]
        if row[16] is not None:
            reaction_times_all.append(row[16])
        if row[17]:
            try:
                rts = json.loads(row[17]) if isinstance(row[17], str) else row[17]
                if isinstance(rts, list):
                    reaction_times_all.extend(rts)
            except:
                pass
    
    if reaction_times_all:
        aggregated_game_data['mean_rt'] = sum(reaction_times_all) / len(reaction_times_all)
    
    vision_data_rows = execute_db('''
        SELECT attention_score, head_yaw, head_pitch, face_area, blink_rate, 
               focus_duration, face_detected, face_distance, blink_count
        FROM vision_raw_data WHERE session_id = ? ORDER BY timestamp
    ''', (session_id,))
    
    vision_data_list = []
    attention_scores = []
    head_deviations = []
    blink_rates = []
    total_focus_time = 0
    distraction_count = 0
    
    for row in vision_data_rows:
        vision_point = {
            'attention_score': row[0],
            'head_yaw': row[1],
            'head_pitch': row[2],
            'face_area': row[3],
            'blink_rate': row[4],
            'focus_duration': row[5],
            'face_detected': row[6],
            'face_distance': row[7],
            'blink_count': row[8]
        }
        vision_data_list.append(vision_point)
        
        if row[0] is not None:
            attention_scores.append(row[0])
        if row[1] is not None and row[2] is not None:
            deviation = (row[1] ** 2 + row[2] ** 2) ** 0.5
            head_deviations.append(deviation)
        if row[4] is not None:
            blink_rates.append(row[4])
        if row[5] is not None:
            total_focus_time += row[5]
        if row[6] == 0:
            distraction_count += 1
    
    vision_scores = calculate_vision_scores(vision_data_list)
    
    score_result = calculate_score(attention_type, aggregated_game_data, vision_scores)
    
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
    
    
    return {
        'final_score': score_result.get('final_score', 0),
        'total_accuracy': total_accuracy,
        'total_time': total_time,
        'total_errors': aggregated_game_data['error'],
        'levels_completed': len(levels_completed),
        'avg_attention_score': round(avg_attention, 2),
        'max_attention_score': round(max_attention, 2),
        'min_attention_score': round(min_attention, 2),
        'attention_stability': round(attention_stability, 2),
        'avg_head_deviation': round(avg_head_deviation, 2),
        'avg_blink_rate': round(avg_blink_rate, 2),
        'total_focus_time': round(total_focus_time, 2),
        'distraction_count': distraction_count,
        'overall_score': score_result.get('final_score', 0),
        'performance_level': score_result.get('performance_level', '较弱'),
        'attention_type': attention_type,
        'score_details': score_result,
        'game_data': aggregated_game_data
    }

def check_and_award_badges(child_id, summary):
    earned_badges = []
    badge_dict = {b['id']: b for b in BADGES}
    
    training_count = execute_db(
        'SELECT COUNT(*) FROM session_summaries WHERE child_id = ?',
        (child_id,)
    )[0][0] + 1
    
    if training_count == 1:
        badge = next((b for b in BADGES if b['requirement_type'] == 'training_count' and b['requirement_value'] == 1), None)
        if badge:
            execute_db(
                'INSERT OR IGNORE INTO user_badges (child_id, badge_id) VALUES (?, ?)',
                (child_id, badge['id'])
            )
            earned_badges.append({'id': badge['id'], 'name': badge['name'], 'icon': badge['icon']})
    
    if training_count == 50:
        badge = next((b for b in BADGES if b['requirement_type'] == 'training_count' and b['requirement_value'] == 50), None)
        if badge:
            execute_db(
                'INSERT OR IGNORE INTO user_badges (child_id, badge_id) VALUES (?, ?)',
                (child_id, badge['id'])
            )
            earned_badges.append({'id': badge['id'], 'name': badge['name'], 'icon': badge['icon']})
    
    if summary.get('total_accuracy') == 100:
        badge = next((b for b in BADGES if b['requirement_type'] == 'perfect_accuracy'), None)
        if badge:
            execute_db(
                'INSERT OR IGNORE INTO user_badges (child_id, badge_id) VALUES (?, ?)',
                (child_id, badge['id'])
            )
            earned_badges.append({'id': badge['id'], 'name': badge['name'], 'icon': badge['icon']})
    
    if summary.get('overall_score', 0) >= 95:
        badge = next((b for b in BADGES if b['requirement_type'] == 'total_score' and b['requirement_value'] == 95), None)
        if badge:
            execute_db(
                'INSERT OR IGNORE INTO user_badges (child_id, badge_id) VALUES (?, ?)',
                (child_id, badge['id'])
            )
            earned_badges.append({'id': badge['id'], 'name': badge['name'], 'icon': badge['icon']})
    
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
        badge = next((b for b in BADGES if b['requirement_type'] == 'memory_score' and b['requirement_value'] == 90), None)
        if badge:
            recommendations.append(f'工作记忆表现出色！已解锁"{badge["name"]}"成就')
    
    if 'visual_tracking' in dimensions and summary.get('overall_score', 0) >= 90:
        badge = next((b for b in BADGES if b['requirement_type'] == 'tracking_score' and b['requirement_value'] == 90), None)
        if badge:
            recommendations.append(f'视觉追踪表现出色！已解锁"{badge["name"]}"成就')
    
    if not recommendations:
        recommendations.append('表现良好，继续保持！')
    
    return recommendations

@data_collector_bp.route('/api/training/session/start', methods=['POST'])
@require_auth
def start_session():
    data = request.json
    child_id = data.get('child_id')
    game_type = data.get('game_type')
    device_id = data.get('device_id')
    
    if not child_id or not game_type:
        return error_response('child_id 和 game_type 不能为空', VALIDATION_ERROR, 400)
    
    if game_type not in GAME_TYPES:
        return error_response(f'无效的游戏类型，支持的类型: {list(GAME_TYPES.keys())}', VALIDATION_ERROR, 400)
    
    child = execute_db('SELECT id, parent_id FROM children WHERE id = ?', (child_id,))
    if not child:
        return error_response('孩子不存在', NOT_FOUND, 404)
    
    if child[0][1] != request.user_id:
        return error_response('孩子不属于当前家长', CHILD_NOT_BELONG, 403)
    
    active_session_id = check_active_session(child_id, game_type)
    if active_session_id:
        # 如果存在活跃会话，直接返回该会话信息
        session_info = get_session_info(active_session_id)
        return success_response({
            'session_id': active_session_id,
            'session_token': session_info['session_token'],
            'game_type': game_type,
            'game_name': GAME_TYPES[game_type]['name']
        }, '使用已存在的活跃会话')
    
    session_token = generate_session_token()
    
    result, session_id = execute_db('''
        INSERT INTO training_sessions (child_id, game_type, session_token, device_id, status)
        VALUES (?, ?, ?, ?, 'active')
    ''', (child_id, game_type, session_token, device_id), fetch_last_id=True)
    
    return success_response({
        'session_id': session_id,
        'session_token': session_token,
        'game_type': game_type,
        'game_name': GAME_TYPES[game_type]['name']
    }, '训练会话已创建')

@data_collector_bp.route('/api/training/game-data', methods=['POST'])
@require_auth
def upload_game_data():
    data = request.json
    session_id = data.get('session_id')
    request_id = data.get('request_id')
    timestamp = data.get('timestamp')
    event_type = data.get('event_type')
    event_data = data.get('event_data')
    score = data.get('score')
    accuracy = data.get('accuracy')
    level = data.get('level')
    
    time = data.get('time')
    correct = data.get('correct')
    error = data.get('error')
    miss = data.get('miss')
    leave = data.get('leave')
    obstacle = data.get('obstacle')
    total_target = data.get('total_target')
    total_step = data.get('total_step')
    total_click = data.get('total_click')
    total_trial = data.get('total_trial')
    memory_load = data.get('memory_load')
    order_error = data.get('order_error')
    late_error_ratio = data.get('late_error_ratio')
    mean_rt = data.get('mean_rt')
    reaction_times = data.get('reaction_times')
    
    if not session_id or not event_type:
        return error_response('session_id 和 event_type 不能为空', VALIDATION_ERROR, 400)
    
    session_info = get_session_info(session_id)
    if not session_info:
        return error_response('训练会话不存在', SESSION_NOT_FOUND, 404)
    
    child = execute_db('SELECT parent_id FROM children WHERE id = ?', (session_info['child_id'],))
    if not child or child[0][0] != request.user_id:
        return error_response('无权操作该会话', CHILD_NOT_BELONG, 403)
    
    if session_info['status'] != 'active':
        return error_response('训练会话已结束', SESSION_EXPIRED, 410)
    
    if is_request_processed(request_id):
        return success_response(None, '请求已处理，跳过重复数据')
    
    event_data_json = json.dumps(event_data) if event_data else None
    reaction_times_json = json.dumps(reaction_times) if reaction_times else None
    
    execute_db('''
        INSERT INTO game_raw_data 
        (session_id, event_type, event_data, score, accuracy, level, timestamp,
         time, correct, error, miss, leave, obstacle, total_target, total_step, total_click, total_trial,
         memory_load, order_error, late_error_ratio, mean_rt, reaction_times)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, event_type, event_data_json, score, accuracy, level, timestamp,
          time, correct, error, miss, leave, obstacle, total_target, total_step, total_click, total_trial,
          memory_load, order_error, late_error_ratio, mean_rt, reaction_times_json))
    
    mark_request_processed(request_id)
    
    execute_db(
        'UPDATE training_sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?',
        (session_id,)
    )
    
    return success_response(None, '游戏数据上传成功')

@data_collector_bp.route('/api/training/vision-data', methods=['POST'])
@require_auth
def upload_vision_data():
    data = request.json
    session_id = data.get('session_id')
    request_id = data.get('request_id')
    timestamp = data.get('timestamp')
    attention_score = data.get('attention_score')
    face_detected = data.get('face_detected', 1)
    head_yaw = data.get('head_yaw')
    head_pitch = data.get('head_pitch')
    face_area = data.get('face_area')
    face_distance = data.get('face_distance')
    blink_rate = data.get('blink_rate')
    blink_count = data.get('blink_count')
    focus_duration = data.get('focus_duration')
    
    if not session_id:
        return error_response('session_id 不能为空', VALIDATION_ERROR, 400)
    
    session_info = get_session_info(session_id)
    if not session_info:
        return error_response('训练会话不存在', SESSION_NOT_FOUND, 404)
    
    child = execute_db('SELECT parent_id FROM children WHERE id = ?', (session_info['child_id'],))
    if not child or child[0][0] != request.user_id:
        return error_response('无权操作该会话', CHILD_NOT_BELONG, 403)
    
    if session_info['status'] != 'active':
        return error_response('训练会话已结束', SESSION_EXPIRED, 410)
    
    if is_request_processed(request_id):
        return success_response(None, '请求已处理，跳过重复数据')
    
    execute_db('''
        INSERT INTO vision_raw_data 
        (session_id, attention_score, face_detected, head_yaw, head_pitch, face_area, 
         blink_rate, focus_duration, face_distance, blink_count, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, attention_score, face_detected, head_yaw, head_pitch, face_area, 
          blink_rate, focus_duration, face_distance, blink_count, timestamp))
    
    mark_request_processed(request_id)
    
    execute_db(
        'UPDATE training_sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?',
        (session_id,)
    )
    
    return success_response(None, '视觉数据上传成功')

@data_collector_bp.route('/api/training/session/end', methods=['POST'])
@require_auth
def end_session():
    try:
        data = request.json
        session_id = data.get('session_id')
        final_score = data.get('final_score', 0)
        total_accuracy = data.get('total_accuracy', 0)
        
        print(f'=== end_session 调试信息 ===')
        print(f'session_id: {session_id}')
        print(f'final_score: {final_score}')
        print(f'total_accuracy: {total_accuracy}')
        print(f'request.user_id: {request.user_id}')
        
        if not session_id:
            return error_response('session_id 不能为空', VALIDATION_ERROR, 400)
        
        session_info = get_session_info(session_id)
        if not session_info:
            return error_response('训练会话不存在', SESSION_NOT_FOUND, 404)
        
        print(f'session_info: {session_info}')
        
        child = execute_db('SELECT parent_id FROM children WHERE id = ?', (session_info['child_id'],))
        if not child or child[0][0] != request.user_id:
            return error_response('无权操作该会话', CHILD_NOT_BELONG, 403)
        
        if session_info['status'] != 'active':
            return error_response('训练会话已结束', SESSION_EXPIRED, 410)
        
        summary = calculate_session_summary(
            session_id, 
            session_info['child_id'], 
            session_info['game_type'],
            final_score,
            total_accuracy
        )
        
        print(f'summary 计算完成')
        print(f'score_details: {summary.get("score_details")}')
        
        execute_db('''
            INSERT INTO session_summaries 
            (session_id, child_id, game_type, attention_type, final_score, total_accuracy, total_time, 
             total_errors, levels_completed, avg_attention_score, max_attention_score, 
             min_attention_score, attention_stability, avg_head_deviation, avg_blink_rate, 
             total_focus_time, distraction_count, overall_score, performance_level,
             accuracy_score, precision_score, speed_score, head_stable_score, face_stable_score,
             blink_stable_score, impulse_score, memory_score, no_fatigue_score, rt_score,
             order_score, stable_act_score, game_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, session_info['child_id'], session_info['game_type'], summary.get('attention_type'),
            summary['final_score'], summary['total_accuracy'], summary['total_time'],
            summary['total_errors'], summary['levels_completed'], summary['avg_attention_score'],
            summary['max_attention_score'], summary['min_attention_score'], summary['attention_stability'],
            summary['avg_head_deviation'], summary['avg_blink_rate'], summary['total_focus_time'],
            summary['distraction_count'], summary['overall_score'], summary['performance_level'],
            summary['score_details'].get('accuracy', 0),
            summary['score_details'].get('precision', 0),
            summary['score_details'].get('speed', 0),
            summary['score_details'].get('head_stable', 0),
            summary['score_details'].get('face_stable', 0),
            summary['score_details'].get('blink_stable', 0),
            summary['score_details'].get('impulse', 0),
            summary['score_details'].get('memory', 0),
            summary['score_details'].get('no_fatigue', 0),
            summary['score_details'].get('rt_score', 0),
            summary['score_details'].get('order', 0),
            summary['score_details'].get('stable_act', 0),
            json.dumps(summary.get('game_data', {}))
        ))
        
        print(f'session_summaries 插入成功')
        
        execute_db('''
            UPDATE training_sessions 
            SET end_time = CURRENT_TIMESTAMP, status = 'completed', 
                duration = ?, last_activity = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (summary['total_time'], session_id))
        
        print(f'training_sessions 更新成功')
        
        earned_badges = check_and_award_badges(session_info['child_id'], summary)
        recommendations = generate_recommendations(summary, session_info['game_type'])
        
        return success_response({
            'session_id': session_id,
            'summary': summary,
            'earned_badges': earned_badges,
            'recommendations': recommendations
        }, '训练会话已结束')
    except Exception as e:
        print(f'=== end_session 错误 ===')
        print(f'错误类型：{type(e).__name__}')
        print(f'错误信息：{str(e)}')
        import traceback
        print(f'堆栈跟踪：{traceback.format_exc()}')
        return error_response(f'服务器内部错误：{str(e)}', INTERNAL_ERROR, 500)

@data_collector_bp.route('/api/training/session/heartbeat', methods=['POST'])
@require_auth
def heartbeat():
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return error_response('session_id 不能为空', VALIDATION_ERROR, 400)
    
    session_info = get_session_info(session_id)
    if not session_info:
        return error_response('训练会话不存在', SESSION_NOT_FOUND, 404)
    
    child = execute_db('SELECT parent_id FROM children WHERE id = ?', (session_info['child_id'],))
    if not child or child[0][0] != request.user_id:
        return error_response('无权操作该会话', CHILD_NOT_BELONG, 403)
    
    if session_info['status'] != 'active':
        return error_response('训练会话已结束', SESSION_EXPIRED, 410)
    
    execute_db(
        'UPDATE training_sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?',
        (session_id,)
    )
    
    return success_response({
        'session_id': session_id,
        'status': 'active'
    }, '心跳更新成功')

@data_collector_bp.route('/api/training/session/interrupt', methods=['POST'])
@require_auth
def interrupt_session():
    data = request.json
    session_id = data.get('session_id')
    current_state = data.get('current_state')
    
    if not session_id:
        return error_response('session_id 不能为空', VALIDATION_ERROR, 400)
    
    session_info = get_session_info(session_id)
    if not session_info:
        return error_response('训练会话不存在', SESSION_NOT_FOUND, 404)
    
    child = execute_db('SELECT parent_id FROM children WHERE id = ?', (session_info['child_id'],))
    if not child or child[0][0] != request.user_id:
        return error_response('无权操作该会话', CHILD_NOT_BELONG, 403)
    
    if session_info['status'] != 'active':
        return error_response('训练会话已结束', SESSION_EXPIRED, 410)
    
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
    
    return success_response({
        'session_id': session_id,
        'status': 'interrupted'
    }, '会话已中断')


@data_collector_bp.route('/api/training/history/<int:child_id>', methods=['GET'])
@require_auth
def get_training_history(child_id):
    child = execute_db('SELECT parent_id FROM children WHERE id = ?', (child_id,))
    if not child:
        return error_response('孩子不存在', NOT_FOUND, 404)
    if child[0][0] != request.user_id:
        return error_response('孩子不属于当前家长', CHILD_NOT_BELONG, 403)
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    game_type = request.args.get('game_type')
    attention_type = request.args.get('attention_type')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = '''
        SELECT s.id, s.game_type, s.start_time, s.end_time, s.status,
               ss.attention_type, ss.overall_score as final_score, ss.performance_level,
               g.name as game_name
        FROM training_sessions s
        LEFT JOIN session_summaries ss ON s.id = ss.session_id
        LEFT JOIN (SELECT 'level1' as game_type, '线索筛选站' as name
                   UNION SELECT 'schulte', '太空小火箭'
                   UNION SELECT 'find-numbers', '垃圾小卫士'
                   UNION SELECT 'level2', '持续性注意训练'
                   UNION SELECT 'magic-maze', '魔法迷宫'
                   UNION SELECT 'water-plants', '浇花游戏'
                   UNION SELECT 'level3', '视觉追踪训练'
                   UNION SELECT 'sun-tracking', '追踪太阳'
                   UNION SELECT 'animal-searching', '寻找动物'
                   UNION SELECT 'level4', '工作记忆训练'
                   UNION SELECT 'card-matching', '记忆翻牌'
                   UNION SELECT 'reverse-memory', '倒序记忆'
                   UNION SELECT 'level5', '抑制控制训练'
                   UNION SELECT 'traffic-light', '红绿灯'
                   UNION SELECT 'command-adventure', '指令冒险') g ON s.game_type = g.game_type
        WHERE s.child_id = ?
    '''
    params = [child_id]
    
    if start_date:
        query += ' AND DATE(s.start_time) >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND DATE(s.start_time) <= ?'
        params.append(end_date)
    if game_type:
        query += ' AND s.game_type = ?'
        params.append(game_type)
    if attention_type:
        query += ' AND ss.attention_type = ?'
        params.append(attention_type)
    
    query += ' ORDER BY s.start_time DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    records = execute_db(query, tuple(params))
    
    count_query = '''
        SELECT COUNT(*) FROM training_sessions s
        LEFT JOIN session_summaries ss ON s.id = ss.session_id
        WHERE s.child_id = ?
    '''
    count_params = [child_id]
    if start_date:
        count_query += ' AND DATE(s.start_time) >= ?'
        count_params.append(start_date)
    if end_date:
        count_query += ' AND DATE(s.start_time) <= ?'
        count_params.append(end_date)
    if game_type:
        count_query += ' AND s.game_type = ?'
        count_params.append(game_type)
    if attention_type:
        count_query += ' AND ss.attention_type = ?'
        count_params.append(attention_type)
    
    total = execute_db(count_query, tuple(count_params))[0][0]
    
    history = []
    for row in records:
        history.append({
            'session_id': row[0],
            'game_type': row[1],
            'start_time': row[2],
            'end_time': row[3],
            'status': row[4],
            'attention_type': row[5],
            'final_score': row[6],
            'performance_level': row[7],
            'game_name': row[8] or row[1]
        })
    
    return success_response({
        'total': total,
        'limit': limit,
        'offset': offset,
        'records': history
    }, '查询成功')


@data_collector_bp.route('/api/training/detail/<int:session_id>', methods=['GET'])
@require_auth
def get_training_detail(session_id):
    session_info = execute_db('''
        SELECT s.id, s.child_id, s.game_type, s.start_time, s.end_time, s.status,
               c.name as child_name
        FROM training_sessions s
        LEFT JOIN children c ON s.child_id = c.id
        WHERE s.id = ?
    ''', (session_id,))
    
    if not session_info:
        return error_response('训练会话不存在', SESSION_NOT_FOUND, 404)
    
    child = execute_db('SELECT parent_id FROM children WHERE id = ?', (session_info[0][1],))
    if not child or child[0][0] != request.user_id:
        return error_response('无权访问该会话', CHILD_NOT_BELONG, 403)
    
    detail = execute_db('''
        SELECT session_id, child_id, game_type, attention_type,
               accuracy_score, precision_score, speed_score,
               head_stable_score, face_stable_score, blink_stable_score,
               impulse_score, memory_score, no_fatigue_score, rt_score, order_score, stable_act_score,
               overall_score as final_score, performance_level, game_data, created_at
        FROM session_summaries
        WHERE session_id = ?
    ''', (session_id,))
    
    game_config = GAME_TYPES.get(session_info[0][2], {})
    
    result = {
        'session_id': session_info[0][0],
        'child_id': session_info[0][1],
        'child_name': session_info[0][6],
        'game_type': session_info[0][2],
        'game_name': game_config.get('name', session_info[0][2]),
        'attention_type': None,
        'start_time': session_info[0][3],
        'end_time': session_info[0][4],
        'status': session_info[0][5],
        'details': {},
        'game_data': {},
        'vision_summary': {}
    }
    
    if detail:
        d = detail[0]
        result['attention_type'] = d[3]
        result['final_score'] = d[16]
        result['performance_level'] = d[17]
        result['details'] = {
            'accuracy_score': d[4],
            'precision_score': d[5],
            'speed_score': d[6],
            'head_stable_score': d[7],
            'face_stable_score': d[8],
            'blink_stable_score': d[9],
            'impulse_score': d[10],
            'memory_score': d[11],
            'no_fatigue_score': d[12],
            'rt_score': d[13],
            'order_score': d[14],
            'stable_act_score': d[15]
        }
        if d[18]:
            try:
                result['game_data'] = json.loads(d[18])
            except:
                result['game_data'] = {}
    
    vision_data = execute_db('''
        SELECT attention_score, head_yaw, head_pitch, face_distance, blink_count
        FROM vision_raw_data
        WHERE session_id = ?
        ORDER BY timestamp
    ''', (session_id,))
    
    if vision_data:
        head_yaws = [v[1] for v in vision_data if v[1] is not None]
        head_pitchs = [v[2] for v in vision_data if v[2] is not None]
        face_distances = [v[3] for v in vision_data if v[3] is not None]
        blink_counts = [v[4] for v in vision_data if v[4] is not None]
        
        import math
        avg_head_deviation = 0
        if head_yaws and head_pitchs:
            deviations = [math.sqrt(y**2 + p**2) for y, p in zip(head_yaws, head_pitchs)]
            avg_head_deviation = sum(deviations) / len(deviations)
        
        avg_blink_rate = sum(blink_counts) / len(blink_counts) * 2 if blink_counts else 0
        
        result['vision_summary'] = {
            'avg_head_deviation': round(avg_head_deviation, 2),
            'avg_blink_rate': round(avg_blink_rate, 2),
            'sample_count': len(vision_data)
        }
    
    return success_response(result, '查询成功')


@data_collector_bp.route('/api/training/trend/<int:child_id>', methods=['GET'])
@require_auth
def get_training_trend(child_id):
    try:
        child = execute_db('SELECT parent_id FROM children WHERE id = ?', (child_id,))
        if not child:
            return error_response('孩子不存在', NOT_FOUND, 404)
        if child[0][0] != request.user_id:
            return error_response('孩子不属于当前家长', CHILD_NOT_BELONG, 403)
        
        attention_type = request.args.get('attention_type')
        days = request.args.get('days', 30, type=int)
        
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        
        query = '''
        SELECT ss.attention_type, DATE(s.start_time) as date, 
               AVG(ss.overall_score) as avg_score,
               COUNT(*) as session_count
        FROM session_summaries ss
        JOIN training_sessions s ON CAST(ss.session_id AS INTEGER) = s.id
        WHERE s.child_id = ? AND DATE(s.start_time) >= ?
    '''
        params = [child_id, start_date.strftime('%Y-%m-%d')]
        
        if attention_type:
            query += ' AND ss.attention_type = ?'
            params.append(attention_type)
        
        query += ' GROUP BY ss.attention_type, DATE(s.start_time) ORDER BY date'
        
        print(f"执行查询: {query}")
        print(f"参数: {params}")
        
        records = execute_db(query, tuple(params))
        print(f"查询结果数量: {len(records)}")
        
        from collections import defaultdict
        trend_data = defaultdict(lambda: {'avg_score': 0, 'trend': 'stable', 'records': []})
        
        attention_types = ['selective', 'sustained', 'tracking', 'memory', 'inhibitory']
        
        for row in records:
            try:
                at = row[0]
                date = row[1]
                avg_score = row[2]
                if avg_score is not None:
                    trend_data[at]['records'].append({
                        'date': date,
                        'score': round(avg_score, 2)
                    })
            except Exception as e:
                print(f"处理记录时出错: {e}")
                continue
        
        for at in attention_types:
            if at in trend_data:
                records_list = trend_data[at]['records']
                if records_list:
                    scores = [r['score'] for r in records_list]
                    trend_data[at]['avg_score'] = round(sum(scores) / len(scores), 2)
                    
                    if len(scores) >= 2:
                        first_half = sum(scores[:len(scores)//2]) / (len(scores)//2) if len(scores)//2 > 0 else 0
                        second_half = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2) if len(scores) - len(scores)//2 > 0 else 0
                        
                        if second_half > first_half * 1.05:
                            trend_data[at]['trend'] = 'up'
                        elif second_half < first_half * 0.95:
                            trend_data[at]['trend'] = 'down'
                        else:
                            trend_data[at]['trend'] = 'stable'
        
        overall_query = '''
            SELECT AVG(ss.overall_score), COUNT(*)
            FROM session_summaries ss
            JOIN training_sessions s ON CAST(ss.session_id AS INTEGER) = s.id
            WHERE s.child_id = ? AND DATE(s.start_time) >= ?
        '''
        overall_params = [child_id, start_date.strftime('%Y-%m-%d')]
        if attention_type:
            overall_query += ' AND s.attention_type = ?'
            overall_params.append(attention_type)
        
        print(f"执行总体查询: {overall_query}")
        print(f"总体查询参数: {overall_params}")
        
        overall_result = execute_db(overall_query, tuple(overall_params))
        print(f"总体查询结果: {overall_result}")
        
        overall_avg = overall_result[0][0] if overall_result and overall_result[0][0] else 0
        total_sessions = overall_result[0][1] if overall_result else 0
        
        print(f"总体平均分数: {overall_avg}")
        print(f"总会话数: {total_sessions}")
        
        result = {
            'child_id': child_id,
            'period': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'days': days
            },
            'trend': {
                'selective': trend_data.get('selective', {'avg_score': 0, 'trend': 'stable', 'records': []}),
                'sustained': trend_data.get('sustained', {'avg_score': 0, 'trend': 'stable', 'records': []}),
                'tracking': trend_data.get('tracking', {'avg_score': 0, 'trend': 'stable', 'records': []}),
                'memory': trend_data.get('memory', {'avg_score': 0, 'trend': 'stable', 'records': []}),
                'inhibitory': trend_data.get('inhibitory', {'avg_score': 0, 'trend': 'stable', 'records': []})
            },
            'overall': {
                'avg_score': round(overall_avg, 2),
                'total_sessions': total_sessions
            }
        }
        
        print(f"返回结果: {result}")
        return success_response(result, '查询成功')
    except Exception as e:
        print(f"处理训练趋势查询时出错: {e}")
        import traceback
        traceback.print_exc()
        return error_response('服务器内部错误', 'INTERNAL_ERROR', 500)


@data_collector_bp.route('/api/upload/detection', methods=['POST'])
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
        return error_response('孩子ID不能为空', 'MISSING_CHILD_ID', 400)
    
    execute_db('''
        INSERT INTO detection_data (child_id, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (child_id, selective_attention, sustained_attention, visual_tracking, working_memory, inhibitory_control, total_score))
    
    return success_response({'child_id': child_id}, '检测数据上传成功')


@data_collector_bp.route('/api/get/detection', methods=['GET'])
def get_detection():
    child_id = request.args.get('child_id')
    
    if not child_id:
        return error_response('孩子ID不能为空', 'MISSING_CHILD_ID', 400)
    
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
    
    return success_response(data, '获取检测数据成功')


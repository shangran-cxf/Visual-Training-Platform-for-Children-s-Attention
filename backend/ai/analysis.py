import json
import requests
from datetime import datetime
from flask import Blueprint, request, g
from database import execute_db
from utils.response_utils import success_response, error_response
from middleware import require_auth
from .config import AI_CONFIG, is_ai_configured

ai_bp = Blueprint('ai', __name__)

ATTENTION_DIMENSION_NAMES = {
    'selective_attention': '选择性注意',
    'sustained_attention': '持续性注意',
    'visual_tracking': '视觉追踪',
    'working_memory': '工作记忆',
    'inhibitory_control': '抑制控制'
}

PERFORMANCE_LEVELS = {
    'excellent': {'min': 90, 'max': 100, 'name': '优秀'},
    'good': {'min': 75, 'max': 89, 'name': '良好'},
    'average': {'min': 50, 'max': 74, 'name': '一般'},
    'weak': {'min': 0, 'max': 49, 'name': '较弱'}
}

def get_child_basic_info(child_id):
    result = execute_db(
        'SELECT id, name, age FROM children WHERE id = ?',
        (child_id,)
    )
    if result:
        return {
            'id': result[0][0],
            'name': result[0][1],
            'age': result[0][2]
        }
    return None

def get_child_training_stats(child_id):
    training_count = execute_db(
        'SELECT COUNT(*) FROM training_sessions WHERE child_id = ?',
        (child_id,)
    )[0][0]
    
    total_time = execute_db(
        'SELECT COALESCE(SUM(duration), 0) FROM training_sessions WHERE child_id = ?',
        (child_id,)
    )[0][0]
    
    avg_score_result = execute_db(
        'SELECT AVG(overall_score) FROM session_summaries WHERE child_id = ?',
        (child_id,)
    )
    avg_score = round(avg_score_result[0][0], 2) if avg_score_result[0][0] else 0
    
    return {
        'training_count': training_count,
        'total_time': total_time,
        'avg_score': avg_score
    }

def get_child_detection_data(child_id):
    result = execute_db('''
        SELECT selective_attention, sustained_attention, visual_tracking, 
               working_memory, inhibitory_control, total_score, timestamp
        FROM detection_data
        WHERE child_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    ''', (child_id,))
    
    if result:
        row = result[0]
        return {
            'selective_attention': row[0],
            'sustained_attention': row[1],
            'visual_tracking': row[2],
            'working_memory': row[3],
            'inhibitory_control': row[4],
            'total_score': row[5],
            'timestamp': row[6]
        }
    return None

def get_child_training_trend(child_id, days=30):
    from datetime import datetime, timedelta
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = '''
        SELECT ss.attention_type, DATE(s.start_time) as date, 
               AVG(ss.overall_score) as avg_score
        FROM session_summaries ss
        JOIN training_sessions s ON ss.session_id = s.id
        WHERE s.child_id = ? AND DATE(s.start_time) >= ?
        GROUP BY ss.attention_type, DATE(s.start_time)
        ORDER BY date
    '''
    
    records = execute_db(query, (child_id, start_date.strftime('%Y-%m-%d')))
    
    trend_data = {}
    for row in records:
        attention_type = row[0]
        date = row[1]
        avg_score = row[2]
        
        if attention_type not in trend_data:
            trend_data[attention_type] = []
        trend_data[attention_type].append({
            'date': date,
            'score': round(avg_score, 2)
        })
    
    return trend_data

def get_performance_level(score):
    if score >= 90:
        return '优秀'
    elif score >= 75:
        return '良好'
    elif score >= 50:
        return '一般'
    else:
        return '较弱'

def build_analysis_prompt(child_info, stats, detection, trend):
    prompt_parts = [
        "你是一位专业的儿童注意力训练分析师。请根据以下儿童训练数据，生成一份专业、详细的训练评析报告。",
        "",
        "## 儿童基本信息",
        f"- 姓名：{child_info.get('name', '未知')}",
        f"- 年龄：{child_info.get('age', '未知')}岁",
        "",
        "## 训练统计",
        f"- 累计训练次数：{stats.get('training_count', 0)}次",
        f"- 累计训练时长：{stats.get('total_time', 0)}分钟",
        f"- 平均得分：{stats.get('avg_score', 0)}分",
        ""
    ]
    
    if detection:
        prompt_parts.extend([
            "## 能力评估数据（最新）",
            f"- 选择性注意：{round(detection.get('selective_attention', 0) * 100, 1)}% ({get_performance_level(detection.get('selective_attention', 0) * 100)})",
            f"- 持续性注意：{round(detection.get('sustained_attention', 0) * 100, 1)}% ({get_performance_level(detection.get('sustained_attention', 0) * 100)})",
            f"- 视觉追踪：{round(detection.get('visual_tracking', 0) * 100, 1)}% ({get_performance_level(detection.get('visual_tracking', 0) * 100)})",
            f"- 工作记忆：{round(detection.get('working_memory', 0) * 100, 1)}% ({get_performance_level(detection.get('working_memory', 0) * 100)})",
            f"- 抑制控制：{round(detection.get('inhibitory_control', 0) * 100, 1)}% ({get_performance_level(detection.get('inhibitory_control', 0) * 100)})",
            f"- 综合得分：{round(detection.get('total_score', 0) * 100, 1)}%",
            ""
        ])
    
    if trend:
        prompt_parts.append("## 训练趋势分析")
        for attention_type, records in trend.items():
            if records:
                scores = [r['score'] for r in records]
                avg = sum(scores) / len(scores)
                trend_direction = '上升' if len(scores) >= 2 and scores[-1] > scores[0] else ('下降' if len(scores) >= 2 and scores[-1] < scores[0] else '稳定')
                prompt_parts.append(f"- {attention_type}：平均{round(avg, 1)}分，趋势{trend_direction}")
        prompt_parts.append("")
    
    prompt_parts.extend([
        "## 请生成以下内容：",
        "1. **整体表现概述**：简要总结儿童的训练整体表现",
        "2. **各维度分析**：分别分析五个注意力维度的表现，指出优势和待提升领域",
        "3. **训练建议**：针对薄弱环节给出具体的训练建议",
        "4. **家庭指导**：给家长的家庭训练指导建议",
        "",
        "请用专业但易懂的语言撰写，内容要有针对性和实用性。"
    ])
    
    return "\n".join(prompt_parts)

def call_ai_api(prompt):
    if not is_ai_configured():
        return None, "AI 服务未配置，请在 backend/ai/config.py 中填写 api_url、api_key 和 model"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {AI_CONFIG["api_key"]}'
    }
    
    payload = {
        'model': AI_CONFIG['model'],
        'messages': [
            {
                'role': 'system',
                'content': '你是一位专业的儿童注意力训练分析师，擅长分析儿童注意力训练数据并给出专业的评析和建议。'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'max_tokens': AI_CONFIG['max_tokens'],
        'temperature': AI_CONFIG['temperature']
    }
    
    try:
        response = requests.post(
            AI_CONFIG['api_url'],
            headers=headers,
            json=payload,
            timeout=AI_CONFIG['timeout']
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'], None
            else:
                return None, f"AI API 返回格式异常: {result}"
        else:
            return None, f"AI API 请求失败: HTTP {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        return None, "AI API 请求超时"
    except requests.exceptions.RequestException as e:
        return None, f"AI API 请求异常: {str(e)}"
    except Exception as e:
        return None, f"AI API 调用失败: {str(e)}"

@ai_bp.route('/api/ai/training-analysis', methods=['POST'])
@require_auth
def generate_training_analysis():
    data = request.json
    child_id = data.get('child_id')
    
    if not child_id:
        return error_response('child_id 不能为空', 'VALIDATION_ERROR', 400)
    
    child_info = get_child_basic_info(child_id)
    if not child_info:
        return error_response('儿童不存在', 'NOT_FOUND', 404)
    
    child_record = execute_db('SELECT parent_id FROM children WHERE id = ?', (child_id,))
    if child_record and child_record[0][0] != request.user_id:
        return error_response('无权访问该儿童数据', 'PERMISSION_DENIED', 403)
    
    stats = get_child_training_stats(child_id)
    detection = get_child_detection_data(child_id)
    trend = get_child_training_trend(child_id)
    
    prompt = build_analysis_prompt(child_info, stats, detection, trend)
    
    analysis, error = call_ai_api(prompt)
    
    if error:
        return error_response(error, 'AI_ERROR', 500)
    
    return success_response({
        'child_id': child_id,
        'child_name': child_info.get('name'),
        'analysis': analysis,
        'generated_at': datetime.now().isoformat(),
        'data_summary': {
            'training_count': stats.get('training_count', 0),
            'total_time': stats.get('total_time', 0),
            'avg_score': stats.get('avg_score', 0),
            'detection': detection,
            'trend_summary': {k: len(v) for k, v in trend.items()} if trend else {}
        }
    }, '评析生成成功')

@ai_bp.route('/api/ai/status', methods=['GET'])
def get_ai_status():
    return success_response({
        'configured': is_ai_configured(),
        'model': AI_CONFIG.get('model') if is_ai_configured() else None
    }, '查询成功')

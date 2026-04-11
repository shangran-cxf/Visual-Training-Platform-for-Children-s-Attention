import json
from openai import OpenAI
from datetime import datetime, timedelta
from flask import Blueprint, request, g
from database import execute_db
from utils.response_utils import success_response, error_response
from middleware import require_auth
from .config import AI_CONFIG, PROMPT_TEMPLATES, CACHE_CONFIG, is_ai_configured
from .validator import (
    is_empty_data,
    get_cached_report_if_unchanged,
    cache_report,
    get_empty_report
)

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

def get_evaluation_data(child_id):
    stats = get_child_training_stats(child_id)
    detection = get_child_detection_data(child_id)
    trend = get_child_training_trend(child_id)
    
    return {
        'training_count': stats.get('training_count', 0),
        'total_time': stats.get('total_time', 0),
        'avg_score': stats.get('avg_score', 0),
        'detection': detection,
        'trend': trend
    }

def get_history_evaluation_data(child_id, days=30):
    stats = get_child_training_stats(child_id)
    trend = get_child_training_trend(child_id, days)
    
    return {
        'training_count': stats.get('training_count', 0),
        'total_time': stats.get('total_time', 0),
        'avg_score': stats.get('avg_score', 0),
        'trend': trend
    }

def get_analysis_data(child_id):
    stats = get_child_training_stats(child_id)
    detection = get_child_detection_data(child_id)
    trend = get_child_training_trend(child_id)
    
    return {
        'training_count': stats.get('training_count', 0),
        'total_time': stats.get('total_time', 0),
        'avg_score': stats.get('avg_score', 0),
        'detection': detection,
        'trend': trend
    }

def build_prompt_from_template(template_key, **kwargs):
    if template_key not in PROMPT_TEMPLATES:
        return None, f"模板 '{template_key}' 不存在"
    
    template = PROMPT_TEMPLATES[template_key]
    user_prompt = template['user_prompt_template']
    
    try:
        formatted_prompt = user_prompt.format(**kwargs)
        return {
            'system_prompt': template['system_prompt'],
            'user_prompt': formatted_prompt
        }, None
    except KeyError as e:
        return None, f"模板变量缺失: {str(e)}"

def validate_json_response(response_text):
    try:
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            return None, "AI 返回的内容中未找到有效的 JSON 格式"
        
        json_str = response_text[json_start:json_end]
        parsed_json = json.loads(json_str)
        return parsed_json, None
    except json.JSONDecodeError as e:
        return None, f"JSON 解析失败: {str(e)}"

def call_ai_service(system_prompt, user_prompt, expect_json=True):
    if not is_ai_configured():
        return None, "AI 服务未配置，请在 backend/ai/config.py 中填写 base_url、api_key 和 model"
    
    try:
        client = OpenAI(
            api_key=AI_CONFIG["api_key"],
            base_url=AI_CONFIG["base_url"],
            timeout=AI_CONFIG["timeout"]
        )
        
        response = client.chat.completions.create(
            model=AI_CONFIG['model'],
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            max_tokens=AI_CONFIG['max_tokens'],
            temperature=AI_CONFIG['temperature']
        )
        
        content = response.choices[0].message.content
        
        if expect_json:
            parsed_json, error = validate_json_response(content)
            if error:
                return None, error
            return parsed_json, None
        else:
            return content, None
            
    except Exception as e:
        return None, f"AI API 调用失败: {str(e)}"

def format_training_data_for_prompt(child_id):
    detection = get_child_detection_data(child_id)
    trend = get_child_training_trend(child_id)
    
    if detection:
        lines = []
        lines.append(f"- 选择性注意：{round(detection.get('selective_attention', 0) * 100, 1)}% ({get_performance_level(detection.get('selective_attention', 0) * 100)})")
        lines.append(f"- 持续性注意：{round(detection.get('sustained_attention', 0) * 100, 1)}% ({get_performance_level(detection.get('sustained_attention', 0) * 100)})")
        lines.append(f"- 视觉追踪：{round(detection.get('visual_tracking', 0) * 100, 1)}% ({get_performance_level(detection.get('visual_tracking', 0) * 100)})")
        lines.append(f"- 工作记忆：{round(detection.get('working_memory', 0) * 100, 1)}% ({get_performance_level(detection.get('working_memory', 0) * 100)})")
        lines.append(f"- 抑制控制：{round(detection.get('inhibitory_control', 0) * 100, 1)}% ({get_performance_level(detection.get('inhibitory_control', 0) * 100)})")
        lines.append(f"- 综合得分：{round(detection.get('total_score', 0) * 100, 1)}%")
        return "\n".join(lines)
    
    if trend:
        lines = ["暂无能力评估数据，以下为训练趋势数据："]
        for attention_type, records in trend.items():
            if records:
                scores = [r['score'] for r in records]
                avg = sum(scores) / len(scores)
                trend_direction = '上升' if len(scores) >= 2 and scores[-1] > scores[0] else ('下降' if len(scores) >= 2 and scores[-1] < scores[0] else '稳定')
                type_name = ATTENTION_DIMENSION_NAMES.get(attention_type, attention_type)
                lines.append(f"- {type_name}：平均 {round(avg, 1)} 分，趋势 {trend_direction}，共 {len(records)} 次记录")
        return "\n".join(lines)
    
    return "暂无最新训练数据"

def format_detection_data_for_prompt(child_id):
    detection = get_child_detection_data(child_id)
    trend = get_child_training_trend(child_id)
    
    if detection:
        lines = []
        lines.append(f"- 选择性注意：{round(detection.get('selective_attention', 0) * 100, 1)}%")
        lines.append(f"- 持续性注意：{round(detection.get('sustained_attention', 0) * 100, 1)}%")
        lines.append(f"- 视觉追踪：{round(detection.get('visual_tracking', 0) * 100, 1)}%")
        lines.append(f"- 工作记忆：{round(detection.get('working_memory', 0) * 100, 1)}%")
        lines.append(f"- 抑制控制：{round(detection.get('inhibitory_control', 0) * 100, 1)}%")
        lines.append(f"- 综合得分：{round(detection.get('total_score', 0) * 100, 1)}%")
        lines.append(f"- 评估时间：{detection.get('timestamp', '未知')}")
        return "\n".join(lines)
    
    if trend:
        lines = ["暂无能力评估数据，以下为训练趋势数据："]
        for attention_type, records in trend.items():
            if records:
                scores = [r['score'] for r in records]
                avg = sum(scores) / len(scores)
                type_name = ATTENTION_DIMENSION_NAMES.get(attention_type, attention_type)
                lines.append(f"- {type_name}：平均 {round(avg, 1)} 分，共 {len(records)} 次记录")
        return "\n".join(lines)
    
    return "暂无能力评估数据"

def format_trend_data_for_prompt(child_id, days=30):
    trend = get_child_training_trend(child_id, days)
    if not trend:
        return "暂无训练趋势数据"
    
    lines = []
    for attention_type, records in trend.items():
        if records:
            scores = [r['score'] for r in records]
            avg = sum(scores) / len(scores)
            trend_direction = '上升' if len(scores) >= 2 and scores[-1] > scores[0] else ('下降' if len(scores) >= 2 and scores[-1] < scores[0] else '稳定')
            lines.append(f"- {attention_type}：平均 {round(avg, 1)} 分，趋势 {trend_direction}，共 {len(records)} 次记录")
    
    return "\n".join(lines) if lines else "暂无训练趋势数据"

def validate_child_access(child_id, user_id):
    child_info = get_child_basic_info(child_id)
    if not child_info:
        return None, '儿童不存在', 404
    
    child_record = execute_db('SELECT parent_id FROM children WHERE id = ?', (child_id,))
    if child_record and child_record[0][0] != user_id:
        return None, '无权访问该儿童数据', 403
    
    return child_info, None, None

@ai_bp.route('/api/ai/current-training-evaluation', methods=['POST'])
@require_auth
def generate_current_training_evaluation():
    data = request.json
    child_id = data.get('child_id')
    
    if not child_id:
        return error_response('child_id 不能为空', 'VALIDATION_ERROR', 400)
    
    child_info, error_msg, error_code = validate_child_access(child_id, request.user_id)
    if error_msg:
        return error_response(error_msg, 'ACCESS_ERROR', error_code)
    
    evaluation_data = get_evaluation_data(child_id)
    
    if is_empty_data(evaluation_data):
        return success_response({
            'child_id': child_id,
            'child_name': child_info.get('name'),
            'evaluation': get_empty_report('current_training'),
            'generated_at': datetime.now().isoformat(),
            'is_cached': False,
            'is_empty': True
        }, '暂无训练数据，返回预设报告')
    
    cached_report = get_cached_report_if_unchanged(child_id, evaluation_data, CACHE_CONFIG)
    if cached_report:
        return success_response({
            'child_id': child_id,
            'child_name': child_info.get('name'),
            'evaluation': cached_report,
            'generated_at': datetime.now().isoformat(),
            'is_cached': True
        }, '返回缓存报告')
    
    prompts, error = build_prompt_from_template(
        'current_training_evaluation',
        child_name=child_info.get('name', '未知'),
        child_age=child_info.get('age', '未知'),
        training_data=format_training_data_for_prompt(child_id),
        detection_data=format_detection_data_for_prompt(child_id)
    )
    
    if error:
        return error_response(error, 'PROMPT_ERROR', 500)
    
    result, error = call_ai_service(
        prompts['system_prompt'],
        prompts['user_prompt'],
        expect_json=True
    )
    
    if error:
        return error_response(error, 'AI_ERROR', 500)
    
    cache_report(child_id, evaluation_data, result, 'current_training')
    
    return success_response({
        'child_id': child_id,
        'child_name': child_info.get('name'),
        'evaluation': result,
        'generated_at': datetime.now().isoformat(),
        'is_cached': False
    }, '当前训练评价生成成功')

@ai_bp.route('/api/ai/history-training-evaluation', methods=['POST'])
@require_auth
def generate_history_training_evaluation():
    data = request.json
    child_id = data.get('child_id')
    days = data.get('days', 30)
    
    if not child_id:
        return error_response('child_id 不能为空', 'VALIDATION_ERROR', 400)
    
    child_info, error_msg, error_code = validate_child_access(child_id, request.user_id)
    if error_msg:
        return error_response(error_msg, 'ACCESS_ERROR', error_code)
    
    evaluation_data = get_history_evaluation_data(child_id, days)
    
    if is_empty_data(evaluation_data):
        return success_response({
            'child_id': child_id,
            'child_name': child_info.get('name'),
            'evaluation': get_empty_report('history_training'),
            'generated_at': datetime.now().isoformat(),
            'data_period_days': days,
            'is_cached': False,
            'is_empty': True
        }, '暂无训练数据，返回预设报告')
    
    cached_report = get_cached_report_if_unchanged(child_id, evaluation_data, CACHE_CONFIG)
    if cached_report:
        return success_response({
            'child_id': child_id,
            'child_name': child_info.get('name'),
            'evaluation': cached_report,
            'generated_at': datetime.now().isoformat(),
            'data_period_days': days,
            'is_cached': True
        }, '返回缓存报告')
    
    stats = get_child_training_stats(child_id)
    
    prompts, error = build_prompt_from_template(
        'history_training_evaluation',
        child_name=child_info.get('name', '未知'),
        child_age=child_info.get('age', '未知'),
        training_count=stats.get('training_count', 0),
        total_time=stats.get('total_time', 0),
        avg_score=stats.get('avg_score', 0),
        trend_data=format_trend_data_for_prompt(child_id, days)
    )
    
    if error:
        return error_response(error, 'PROMPT_ERROR', 500)
    
    result, error = call_ai_service(
        prompts['system_prompt'],
        prompts['user_prompt'],
        expect_json=True
    )
    
    if error:
        return error_response(error, 'AI_ERROR', 500)
    
    cache_report(child_id, evaluation_data, result, 'history_training')
    
    return success_response({
        'child_id': child_id,
        'child_name': child_info.get('name'),
        'evaluation': result,
        'generated_at': datetime.now().isoformat(),
        'data_period_days': days,
        'is_cached': False
    }, '历史训练评价生成成功')

@ai_bp.route('/api/ai/generate', methods=['POST'])
@require_auth
def generate_with_custom_prompt():
    data = request.json
    custom_prompt = data.get('prompt')
    template_key = data.get('template')
    template_data = data.get('data', {})
    expect_json = data.get('expect_json', True)
    
    if not custom_prompt and not template_key:
        return error_response('必须提供 prompt 或 template 参数', 'VALIDATION_ERROR', 400)
    
    if template_key:
        prompts, error = build_prompt_from_template(template_key, **template_data)
        if error:
            return error_response(error, 'PROMPT_ERROR', 500)
        
        system_prompt = prompts['system_prompt']
        user_prompt = prompts['user_prompt']
    else:
        system_prompt = '你是一位专业的儿童注意力训练分析师。请根据用户的请求提供专业的分析和建议。'
        user_prompt = custom_prompt
    
    result, error = call_ai_service(system_prompt, user_prompt, expect_json)
    
    if error:
        return error_response(error, 'AI_ERROR', 500)
    
    return success_response({
        'result': result,
        'generated_at': datetime.now().isoformat()
    }, 'AI 生成成功')

@ai_bp.route('/api/ai/training-analysis', methods=['POST'])
@require_auth
def generate_training_analysis():
    data = request.json
    child_id = data.get('child_id')
    
    if not child_id:
        return error_response('child_id 不能为空', 'VALIDATION_ERROR', 400)
    
    child_info, error_msg, error_code = validate_child_access(child_id, request.user_id)
    if error_msg:
        return error_response(error_msg, 'ACCESS_ERROR', error_code)
    
    analysis_data = get_analysis_data(child_id)
    
    if is_empty_data(analysis_data):
        return success_response({
            'child_id': child_id,
            'child_name': child_info.get('name'),
            'analysis': get_empty_report('training_analysis').get('analysis'),
            'generated_at': datetime.now().isoformat(),
            'data_summary': {
                'training_count': 0,
                'total_time': 0,
                'avg_score': 0,
                'detection': None,
                'trend_summary': {}
            },
            'is_cached': False,
            'is_empty': True
        }, '暂无训练数据，返回预设报告')
    
    cached_report = get_cached_report_if_unchanged(child_id, analysis_data, CACHE_CONFIG)
    if cached_report:
        stats = get_child_training_stats(child_id)
        detection = get_child_detection_data(child_id)
        trend = get_child_training_trend(child_id)
        return success_response({
            'child_id': child_id,
            'child_name': child_info.get('name'),
            'analysis': cached_report.get('analysis'),
            'generated_at': datetime.now().isoformat(),
            'data_summary': {
                'training_count': stats.get('training_count', 0),
                'total_time': stats.get('total_time', 0),
                'avg_score': stats.get('avg_score', 0),
                'detection': detection,
                'trend_summary': {k: len(v) for k, v in trend.items()} if trend else {}
            },
            'is_cached': True
        }, '返回缓存报告')
    
    stats = get_child_training_stats(child_id)
    detection = get_child_detection_data(child_id)
    trend = get_child_training_trend(child_id)
    
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
    
    prompt = "\n".join(prompt_parts)
    
    system_prompt = '你是一位专业的儿童注意力训练分析师，擅长分析儿童注意力训练数据并给出专业的评析和建议。'
    
    analysis, error = call_ai_service(system_prompt, prompt, expect_json=False)
    
    if error:
        return error_response(error, 'AI_ERROR', 500)
    
    cache_report(child_id, analysis_data, {'analysis': analysis}, 'training_analysis')
    
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
        },
        'is_cached': False
    }, '评析生成成功')

@ai_bp.route('/api/ai/status', methods=['GET'])
def get_ai_status():
    return success_response({
        'configured': is_ai_configured(),
        'model': AI_CONFIG.get('model') if is_ai_configured() else None,
        'available_templates': list(PROMPT_TEMPLATES.keys()),
        'cache_enabled': CACHE_CONFIG.get('enabled', True)
    }, '查询成功')

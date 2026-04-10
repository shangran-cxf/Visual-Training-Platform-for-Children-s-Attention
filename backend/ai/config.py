AI_CONFIG = {
    'base_url': 'https://api.modelarts-maas.com/openai/v1',  # API 地址
    'api_key': 'k6JrgF6Rdj7A7qjlC_IupDkN0UkA5YPvbiOfL9hPN1Sl_vMqyMiliEcy5qOrk5uz33xMQKyc_91bOo2KyTtaiA',   # API Key
    'model': 'deepseek-v3.1-terminus',     # 模型名称
    'timeout': 30,
    'max_tokens': 1000,
    'temperature': 0.7,
    'output_format': 'json',
    'max_response_length': 500,
}

CACHE_CONFIG = {
    'enabled': True,
    'expire_hours': 24,
    'max_cache_size': 1000,
}

PROMPT_TEMPLATES = {
    'current_training_evaluation': {
        'name': '当前训练数据评价',
        'system_prompt': '你是一位专业的儿童注意力训练分析师。请根据提供的训练数据，生成专业、客观的评价报告。你的回答必须是严格的JSON格式，不要包含任何其他文字说明。',
        'user_prompt_template': '''请根据以下儿童的当前训练数据生成评价报告。

## 儿童基本信息
- 姓名：{child_name}
- 年龄：{child_age}岁

## 最新训练数据
{training_data}

## 能力评估
{detection_data}

## 输出要求
请严格按照以下JSON格式输出，不要添加任何其他内容：
{{
  "summary": "整体表现概述（50-100字）",
  "strengths": [
    "优势1",
    "优势2"
  ],
  "weaknesses": [
    "待提升领域1",
    "待提升领域2"
  ],
  "suggestions": [
    "训练建议1",
    "训练建议2"
  ],
  "home_guidance": "家庭训练指导建议（50-100字）"
}}

注意：
1. 必须返回有效的JSON格式
2. summary和home_guidance字数控制在50-100字
3. strengths、weaknesses、suggestions各包含2-3条内容
4. 内容要具体、有针对性''',
    },
    
    'history_training_evaluation': {
        'name': '历史训练状态评价',
        'system_prompt': '你是一位专业的儿童注意力训练分析师。请根据提供的历史训练数据，分析训练趋势和进步情况。你的回答必须是严格的JSON格式，不要包含任何其他文字说明。',
        'user_prompt_template': '''请根据以下儿童的历史训练数据生成趋势分析报告。

## 儿童基本信息
- 姓名：{child_name}
- 年龄：{child_age}岁

## 训练统计
- 累计训练次数：{training_count}次
- 累计训练时长：{total_time}分钟
- 平均得分：{avg_score}分

## 训练趋势数据
{trend_data}

## 输出要求
请严格按照以下JSON格式输出，不要添加任何其他内容：
{{
  "overall_progress": "整体进步情况（50-100字）",
  "trend_analysis": [
    {{
      "dimension": "注意力维度名称",
      "trend": "上升/下降/稳定",
      "description": "具体分析（30-50字）"
    }}
  ],
  "milestones": [
    "重要里程碑1",
    "重要里程碑2"
  ],
  "recommendations": [
    "未来训练建议1",
    "未来训练建议2"
  ],
  "encouragement": "鼓励话语（30-50字）"
}}

注意：
1. 必须返回有效的JSON格式
2. overall_progress和encouragement字数控制在规定范围内
3. trend_analysis包含3-5个维度的分析
4. 内容要基于数据，客观真实''',
    },
}

def is_ai_configured():
    return bool(AI_CONFIG.get('base_url') and AI_CONFIG.get('api_key') and AI_CONFIG.get('model'))

def is_cache_enabled():
    return CACHE_CONFIG.get('enabled', True)

def get_cache_expire_hours():
    return CACHE_CONFIG.get('expire_hours', 24)

import os
from pathlib import Path

_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    with open(_env_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

AI_CONFIG = {
    "base_url": os.environ.get("AI_BASE_URL", ""),  # API 地址
    "api_key": os.environ.get("AI_API_KEY", ""),  # API Key
    "model": os.environ.get("AI_MODEL", ""),  # 模型名称
    "timeout": int(os.environ.get("AI_TIMEOUT", "30")),
    "max_tokens": int(os.environ.get("AI_MAX_TOKENS", "1000")),
    "temperature": float(os.environ.get("AI_TEMPERATURE", "0.7")),
    "output_format": "json",
    "max_response_length": 500,
}

CACHE_CONFIG = {
    "enabled": True,
    "expire_hours": 24,
    "max_cache_size": 1000,
}

PROMPT_TEMPLATES = {
    "current_training_evaluation": {
        "name": "当前训练数据评价",
        "system_prompt": "你是一位专业又亲切的儿童注意力训练专家。请用温暖、专业的语言，为家长提供直观易懂的训练反馈。你的回答必须是严格的JSON格式，不要包含任何其他文字说明。",
        "user_prompt_template": """请根据以下儿童的训练数据，为家长生成一份专业、易懂、实用的评价反馈。

## 儿童信息
姓名：{child_name}，年龄：{child_age}岁

## 训练数据
{training_data}

## 能力评估
{detection_data}

## 输出要求
请严格按照以下JSON格式输出：
{{
  "summary": "一句话总结（40-60字，突出核心结论）",
  "strengths": [
    "优势描述（15-60字）",
    "优势描述（15-60字）"
  ],
  "weaknesses": [
    "待提升点（15-60字）",
    "待提升点（15-60字）"
  ],
  "suggestions": [
    "具体建议（15-60字）",
    "具体建议（15-60字）"
  ],
  "home_guidance": "家庭训练建议（60-180字，详细、分点）"
}}

写作要求：
1. 语言亲切自然，像和朋友交流一样
2. 每条内容尽量精炼有力，避免冗长重复
3. 必须用数据说话，但不要堆砌数字
4. 建议要具体可操作，家长容易执行
5. 必须返回有效的JSON格式""",
    },
    "history_training_evaluation": {
        "name": "历史训练状态评价",
        "system_prompt": "你是一位专业又亲切的儿童注意力训练专家。请用温暖、专业的语言，为家长分析孩子的训练进步情况。你的回答必须是严格的JSON格式，不要包含任何其他文字说明。",
        "user_prompt_template": """请根据以下儿童的历史训练数据，为家长生成一份专业、易懂、鼓舞人心的进步分析。

## 儿童信息
姓名：{child_name}，年龄：{child_age}岁

## 训练概况
训练{training_count}次，共{total_time}分钟，平均{avg_score}分

## 训练趋势
{trend_data}

## 输出要求
请严格按照以下JSON格式输出：
{{
  "overall_progress": "一句话总结进步（40-60字）",
  "trend_analysis": [
    {{
      "dimension": "能力维度",
      "trend": "上升/下降/稳定",
      "description": "简短分析（15-60字）"
    }}
  ],
  "milestones": [
    "亮点成就",
    "亮点成就"
  ],
  "recommendations": [
    "下一步建议（15-60字）",
    "下一步建议（15-60字）"
  ],
  "encouragement": "暖心鼓励（15-60字）"
}}

写作要求：
1. 语言亲切温暖，让家长感受到孩子的进步
2. 突出亮点，淡化不足，以鼓励为主
3. 每条内容尽量精炼有力，避免冗长重复
4. 建议要具体可行，家长容易执行
5. 必须返回有效的JSON格式""",
    },
}


def is_ai_configured():
    return bool(AI_CONFIG.get("base_url") and AI_CONFIG.get("api_key") and AI_CONFIG.get("model"))


def is_cache_enabled():
    return CACHE_CONFIG.get("enabled", True)


def get_cache_expire_hours():
    return CACHE_CONFIG.get("expire_hours", 24)

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
    "max_tokens": int(os.environ.get("AI_MAX_TOKENS", "1500")),
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
        "name": "训练综合评估报告",
        "system_prompt": (
            "你是一位专业又亲切的儿童注意力训练专家。"
            "请用温暖、专业的语言，为家长提供直观易懂的训练反馈。\n"
            "## 分析原则\n"
            "1. 不罗列数据——解读数据背后的含义，关注维度间的关联"
            "（如工作记忆弱可能影响其他能力的发挥）\n"
            "2. 趋势变化要分析可能原因，不只描述方向\n"
            "3. 每条建议要针对具体数据表现，家长能直接执行\n"
            "你的回答必须是严格的 JSON 格式。"
        ),
        "user_prompt_template": (
            "请根据以下儿童训练数据，为家长生成一份专业、易懂、实用的综合评估报告。\n\n"
            "## 儿童信息\n"
            "姓名：{child_name}，年龄：{child_age}岁\n\n"
            "## 训练数据\n"
            "{training_data}\n\n"
            "## 能力评估\n"
            "{detection_data}\n\n"
            "## 历史趋势（近30天）\n"
            "{trend_data}\n\n"
            "## 输出 JSON 格式\n"
            "{{\n"
            '  "summary": "综合总结（40-60字，含核心发现和趋势变化）",\n'
            '  "strengths": ["优势（15-50字）", "优势（15-50字）"],\n'
            '  "weaknesses": ["待提升点（15-50字）", "待提升点（15-50字）"],\n'
            '  "suggestions": ["具体建议（15-50字）", "具体建议（15-50字）"],\n'
            '  "home_guidance": "家庭指导（60-150字，分点、可执行）",\n'
            '  "trend_analysis": [\n'
            '    {{"name": "维度名", "trend": "上升/下降/稳定", "detail": "简短分析（15-40字）"}}\n'
            "  ]\n"
            "}}\n\n"
            "写作要求：\n"
            "1. 语言亲切自然，像和朋友交流一样\n"
            "2. 每条内容精炼有力，避免冗长重复\n"
            "3. 分析数据间关系而非罗列数字\n"
            "4. 建议具体可操作，家长容易执行"
        ),
    },
}


def is_ai_configured():
    return bool(AI_CONFIG.get("base_url") and AI_CONFIG.get("api_key") and AI_CONFIG.get("model"))


def is_cache_enabled():
    return CACHE_CONFIG.get("enabled", True)


def get_cache_expire_hours():
    return CACHE_CONFIG.get("expire_hours", 24)

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DATABASE_PATH

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
DATABASE_DIR = os.path.join(PROJECT_ROOT, "database")
DB_PATH = DATABASE_PATH

SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production-2024"

APP_CONFIG = {
    "debug": os.environ.get("FLASK_DEBUG", "true").lower() in ("true", "1", "yes"),
    "host": os.environ.get("FLASK_HOST", "0.0.0.0"),
    "port": int(os.environ.get("FLASK_PORT", "5000")),
    "secret_key": SECRET_KEY,
}

GAME_TYPES = {
    "level1": {"name": "线索筛选站", "attention_type": "selective", "dimensions": ["selective_attention"]},
    "schulte": {"name": "太空小火箭", "attention_type": "selective", "dimensions": ["selective_attention"]},
    "find-numbers": {"name": "垃圾小卫士", "attention_type": "selective", "dimensions": ["selective_attention"]},
    "level2": {"name": "持续性注意训练", "attention_type": "sustained", "dimensions": ["sustained_attention"]},
    "magic-maze": {"name": "魔法迷宫", "attention_type": "sustained", "dimensions": ["sustained_attention"]},
    "water-plants": {"name": "浇花游戏", "attention_type": "sustained", "dimensions": ["sustained_attention"]},
    "level3": {"name": "视觉追踪训练", "attention_type": "tracking", "dimensions": ["visual_tracking"]},
    "sun-tracking": {"name": "追踪太阳", "attention_type": "tracking", "dimensions": ["visual_tracking"]},
    "animal-searching": {"name": "寻找动物", "attention_type": "tracking", "dimensions": ["visual_tracking"]},
    "level4": {"name": "工作记忆训练", "attention_type": "memory", "dimensions": ["working_memory"]},
    "card-matching": {"name": "记忆翻牌", "attention_type": "memory", "dimensions": ["working_memory"]},
    "reverse-memory": {"name": "倒序记忆", "attention_type": "memory", "dimensions": ["working_memory"]},
    "level5": {"name": "抑制控制训练", "attention_type": "inhibitory", "dimensions": ["inhibitory_control"]},
    "traffic-light": {"name": "红绿灯", "attention_type": "inhibitory", "dimensions": ["inhibitory_control"]},
    "command-adventure": {"name": "指令冒险", "attention_type": "inhibitory", "dimensions": ["inhibitory_control"]},
    "comprehensive": {
        "name": "综合训练",
        "attention_type": "comprehensive",
        "dimensions": [
            "selective_attention",
            "sustained_attention",
            "visual_tracking",
            "working_memory",
            "inhibitory_control",
        ],
    },
}

ATTENTION_TYPES = {
    "selective": {
        "name": "选择性注意",
        "description": "目标搜索 + 抗干扰 + 速度",
        "games": ["level1", "schulte", "find-numbers"],
    },
    "sustained": {
        "name": "持续性注意",
        "description": "维持专注 + 抗疲劳 + 稳定性",
        "games": ["level2", "magic-maze", "water-plants"],
    },
    "tracking": {
        "name": "视觉追踪",
        "description": "眼手协调 + 动态跟踪 + 连续专注",
        "games": ["level3", "sun-tracking", "animal-searching"],
    },
    "memory": {
        "name": "工作记忆",
        "description": "短时存储 + 顺序保持 + 提取速度",
        "games": ["level4", "card-matching", "reverse-memory"],
    },
    "inhibitory": {
        "name": "抑制控制",
        "description": "抑制冲动 + 遵守规则 + 抗干扰",
        "games": ["level5", "traffic-light", "command-adventure"],
    },
}

ATTENTION_DIMENSIONS = {
    "selective_attention": "选择性注意力",
    "sustained_attention": "持续性注意力",
    "visual_tracking": "视觉追踪",
    "working_memory": "工作记忆",
    "inhibitory_control": "抑制控制",
}

SCORING_WEIGHTS = {
    "selective": {"accuracy": 0.35, "precision": 0.25, "speed": 0.20, "head_stable": 0.10, "blink_stable": 0.10},
    "sustained": {"stable_act": 0.30, "no_fatigue": 0.25, "speed": 0.20, "head_stable": 0.15, "blink_stable": 0.10},
    "tracking": {"accuracy": 0.35, "rt_score": 0.25, "speed": 0.20, "head_stable": 0.12, "face_stable": 0.05, "blink_stable": 0.03},
    "memory": {"accuracy": 0.40, "order": 0.20, "speed": 0.20, "head_stable": 0.12, "blink_stable": 0.08},
    "inhibitory": {"impulse": 0.40, "accuracy": 0.30, "head_stable": 0.15, "face_stable": 0.08, "blink_stable": 0.07},
}

PERFORMANCE_LEVELS = {
    "excellent": {"min": 90, "max": 100, "name": "优秀"},
    "good": {"min": 75, "max": 89, "name": "良好"},
    "average": {"min": 50, "max": 74, "name": "一般"},
    "weak": {"min": 0, "max": 49, "name": "较弱"},
}

DEFAULT_GAME_DATA = {
    "time": 0,
    "correct": 0,
    "error": 0,
    "miss": 0,
    "leave": 0,
    "obstacle": 0,
    "total_target": 1,
    "total_step": 1,
    "total_click": 1,
    "total_trial": 1,
    "memory_load": 1,
    "order_error": 0,
    "late_error_ratio": 0.0,
    "mean_rt": 1000,
}

# ──────────────────────────────────────────────
# Per-game, per-difficulty sub-score weight overrides
# Key format: "game_type:difficulty"
# When an entry exists, it replaces SCORING_WEIGHTS[attention_type].
# When absent, fallback to type-level weights.
# Weight design: low difficulty → accuracy/speed (fundamentals);
#                high difficulty → precision/impulse/order (advanced sub-skills).
# ──────────────────────────────────────────────
GAME_DIFFICULTY_WEIGHTS = {
    # ── Selective Attention ──
    "schulte:3": {"accuracy": 0.40, "precision": 0.20, "speed": 0.20, "head_stable": 0.10, "blink_stable": 0.10},
    "schulte:5": {"accuracy": 0.30, "precision": 0.25, "speed": 0.25, "head_stable": 0.10, "blink_stable": 0.10},
    "schulte:7": {"accuracy": 0.25, "precision": 0.30, "speed": 0.25, "head_stable": 0.10, "blink_stable": 0.10},
    "find-numbers:1": {"accuracy": 0.35, "precision": 0.25, "speed": 0.20, "head_stable": 0.10, "blink_stable": 0.10},
    "find-numbers:2": {"accuracy": 0.30, "precision": 0.25, "speed": 0.25, "head_stable": 0.10, "blink_stable": 0.10},
    "find-numbers:3": {"accuracy": 0.25, "precision": 0.25, "speed": 0.30, "head_stable": 0.10, "blink_stable": 0.10},
    # ── Sustained Attention ──
    "magic-maze:easy": {
        "stable_act": 0.35,
        "no_fatigue": 0.25,
        "speed": 0.20,
        "head_stable": 0.10,
        "blink_stable": 0.10,
    },
    "magic-maze:medium": {
        "stable_act": 0.25,
        "no_fatigue": 0.30,
        "speed": 0.25,
        "head_stable": 0.10,
        "blink_stable": 0.10,
    },
    "magic-maze:hard": {
        "stable_act": 0.20,
        "no_fatigue": 0.35,
        "speed": 0.25,
        "head_stable": 0.10,
        "blink_stable": 0.10,
    },
    # ── Tracking ──
    "sun-tracking:easy": {"accuracy": 0.35, "rt_score": 0.25, "speed": 0.20, "head_stable": 0.12, "face_stable": 0.05, "blink_stable": 0.03},
    "sun-tracking:medium": {
        "accuracy": 0.30,
        "rt_score": 0.30,
        "speed": 0.20,
        "head_stable": 0.12,
        "face_stable": 0.05,
        "blink_stable": 0.03,
    },
    "sun-tracking:hard": {"accuracy": 0.25, "rt_score": 0.35, "speed": 0.20, "head_stable": 0.12, "face_stable": 0.05, "blink_stable": 0.03},
    "animal-searching:easy": {
        "accuracy": 0.40,
        "rt_score": 0.20,
        "speed": 0.20,
        "head_stable": 0.12,
        "face_stable": 0.08,
    },
    "animal-searching:medium": {
        "accuracy": 0.30,
        "rt_score": 0.30,
        "speed": 0.20,
        "head_stable": 0.12,
        "face_stable": 0.08,
    },
    "animal-searching:hard": {
        "accuracy": 0.25,
        "rt_score": 0.35,
        "speed": 0.20,
        "head_stable": 0.12,
        "face_stable": 0.08,
    },
    # ── Working Memory ──
    "card-matching:easy": {"accuracy": 0.45, "order": 0.15, "speed": 0.20, "head_stable": 0.12, "blink_stable": 0.08},
    "card-matching:medium": {"accuracy": 0.35, "order": 0.25, "speed": 0.20, "head_stable": 0.12, "blink_stable": 0.08},
    "card-matching:hard": {"accuracy": 0.30, "order": 0.30, "speed": 0.20, "head_stable": 0.12, "blink_stable": 0.08},
    "reverse-memory:easy": {"accuracy": 0.40, "order": 0.20, "speed": 0.20, "head_stable": 0.12, "blink_stable": 0.08},
    "reverse-memory:medium": {
        "accuracy": 0.30,
        "order": 0.30,
        "speed": 0.20,
        "head_stable": 0.12,
        "blink_stable": 0.08,
    },
    "reverse-memory:hard": {"accuracy": 0.25, "order": 0.35, "speed": 0.20, "head_stable": 0.12, "blink_stable": 0.08},
    # ── Inhibitory Control ──
    "traffic-light:easy": {
        "impulse": 0.45,
        "accuracy": 0.25,
        "head_stable": 0.15,
        "face_stable": 0.08,
        "blink_stable": 0.07,
    },
    "traffic-light:medium": {
        "impulse": 0.35,
        "accuracy": 0.35,
        "head_stable": 0.15,
        "face_stable": 0.08,
        "blink_stable": 0.07,
    },
    "traffic-light:hard": {
        "impulse": 0.30,
        "accuracy": 0.40,
        "head_stable": 0.15,
        "face_stable": 0.08,
        "blink_stable": 0.07,
    },
    "command-adventure:easy": {
        "impulse": 0.45,
        "accuracy": 0.25,
        "head_stable": 0.15,
        "face_stable": 0.08,
        "blink_stable": 0.07,
    },
    "command-adventure:medium": {
        "impulse": 0.35,
        "accuracy": 0.35,
        "head_stable": 0.15,
        "face_stable": 0.08,
        "blink_stable": 0.07,
    },
    "command-adventure:hard": {
        "impulse": 0.30,
        "accuracy": 0.40,
        "head_stable": 0.15,
        "face_stable": 0.08,
        "blink_stable": 0.07,
    },
}

# Difficulty multiplier: harder difficulties receive a score bonus
DIFFICULTY_MULTIPLIERS = {
    "easy": 0.95,
    "medium": 1.00,
    "hard": 1.05,
    1: 0.95,
    2: 1.00,
    3: 1.05,
    5: 1.03,
    7: 1.06,
}

# How each game's score distributes across attention dimensions (sum = 1.0)
GAME_DIMENSION_CONTRIBUTIONS = {
    "schulte": {"selective_attention": 0.60, "sustained_attention": 0.40},
    "find-numbers": {"selective_attention": 0.50, "visual_tracking": 0.50},
    "card-matching": {"working_memory": 0.60, "sustained_attention": 0.40},
    "reverse-memory": {"working_memory": 1.00},
    "traffic-light": {"inhibitory_control": 0.60, "sustained_attention": 0.40},
    "command-adventure": {"inhibitory_control": 1.00},
    "magic-maze": {"visual_tracking": 0.50, "sustained_attention": 0.50},
    "sun-tracking": {"visual_tracking": 1.00},
    "animal-searching": {"selective_attention": 0.50, "visual_tracking": 0.50},
    "water-plants": {"sustained_attention": 0.60, "inhibitory_control": 0.40},
    "level1": {"selective_attention": 1.00},
    "level2": {"sustained_attention": 1.00},
    "level3": {"visual_tracking": 1.00},
    "level4": {"working_memory": 1.00},
    "level5": {"inhibitory_control": 1.00},
    "comprehensive": {
        "selective_attention": 0.20,
        "sustained_attention": 0.20,
        "visual_tracking": 0.20,
        "working_memory": 0.20,
        "inhibitory_control": 0.20,
    },
}

# Cross-game score calibration (mean, std_dev) for z-score normalization
# Initial estimates — should be recalibrated from production data periodically
GAME_SCORE_CALIBRATION = {
    "schulte": {"mean": 65, "std": 18},
    "find-numbers": {"mean": 62, "std": 20},
    "magic-maze": {"mean": 58, "std": 22},
    "water-plants": {"mean": 70, "std": 15},
    "sun-tracking": {"mean": 60, "std": 20},
    "animal-searching": {"mean": 55, "std": 25},
    "card-matching": {"mean": 50, "std": 25},
    "reverse-memory": {"mean": 45, "std": 28},
    "traffic-light": {"mean": 55, "std": 25},
    "command-adventure": {"mean": 50, "std": 28},
    "level1": {"mean": 65, "std": 18},
    "level2": {"mean": 60, "std": 22},
    "level3": {"mean": 60, "std": 20},
    "level4": {"mean": 50, "std": 25},
    "level5": {"mean": 55, "std": 25},
    "comprehensive": {"mean": 60, "std": 20},
}

TIME_DECAY_HALF_LIFE_DAYS = 30
ENABLE_CROSS_GAME_NORMALIZATION = True

CATEGORIES = [
    {"id": 1, "name": "育儿经验", "description": "分享育儿心得和经验", "icon": "👶", "sort_order": 1},
    {"id": 2, "name": "注意力训练", "description": "讨论注意力训练方法和技巧", "icon": "🎯", "sort_order": 2},
    {"id": 3, "name": "学习资源", "description": "分享学习资料和资源", "icon": "📚", "sort_order": 3},
    {"id": 4, "name": "问题求助", "description": "遇到问题寻求帮助", "icon": "❓", "sort_order": 4},
    {"id": 5, "name": "闲聊灌水", "description": "轻松闲聊，分享生活", "icon": "💬", "sort_order": 5},
]

BADGES = [
    {
        "id": 1,
        "name": "初学者",
        "description": "完成第一次训练",
        "icon": "🎯",
        "requirement_type": "training_count",
        "requirement_value": 1,
    },
    {
        "id": 2,
        "name": "坚持者",
        "description": "连续训练7天",
        "icon": "🔥",
        "requirement_type": "consecutive_days",
        "requirement_value": 7,
    },
    {
        "id": 3,
        "name": "专注达人",
        "description": "完成50次训练",
        "icon": "⭐",
        "requirement_type": "training_count",
        "requirement_value": 50,
    },
    {
        "id": 4,
        "name": "完美表现",
        "description": "单次训练正确率达到100%",
        "icon": "💯",
        "requirement_type": "perfect_accuracy",
        "requirement_value": 1,
    },
    {
        "id": 5,
        "name": "速度之星",
        "description": "在规定时间内完成训练",
        "icon": "⚡",
        "requirement_type": "speed_complete",
        "requirement_value": 1,
    },
    {
        "id": 6,
        "name": "记忆大师",
        "description": "工作记忆得分超过90分",
        "icon": "🧠",
        "requirement_type": "memory_score",
        "requirement_value": 90,
    },
    {
        "id": 7,
        "name": "追踪专家",
        "description": "视觉追踪得分超过90分",
        "icon": "👁️",
        "requirement_type": "tracking_score",
        "requirement_value": 90,
    },
    {
        "id": 8,
        "name": "注意力王者",
        "description": "总分超过95分",
        "icon": "👑",
        "requirement_type": "total_score",
        "requirement_value": 95,
    },
]

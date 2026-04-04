import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'attention.db')

SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'

DATABASE_CONFIG = {
    'db_path': DB_PATH
}

APP_CONFIG = {
    'debug': True,
    'host': '0.0.0.0',
    'port': 5000,
    'secret_key': SECRET_KEY
}

GAME_TYPES = {
    'level1': {
        'name': '线索筛选站',
        'attention_type': 'selective',
        'dimensions': ['selective_attention']
    },
    'schulte': {
        'name': '太空小火箭',
        'attention_type': 'selective',
        'dimensions': ['selective_attention']
    },
    'find-numbers': {
        'name': '垃圾小卫士',
        'attention_type': 'selective',
        'dimensions': ['selective_attention']
    },
    'level2': {
        'name': '持续性注意训练',
        'attention_type': 'sustained',
        'dimensions': ['sustained_attention']
    },
    'magic-maze': {
        'name': '魔法迷宫',
        'attention_type': 'sustained',
        'dimensions': ['sustained_attention']
    },
    'water-plants': {
        'name': '浇花游戏',
        'attention_type': 'sustained',
        'dimensions': ['sustained_attention']
    },
    'level3': {
        'name': '视觉追踪训练',
        'attention_type': 'tracking',
        'dimensions': ['visual_tracking']
    },
    'sun-tracking': {
        'name': '追踪太阳',
        'attention_type': 'tracking',
        'dimensions': ['visual_tracking']
    },
    'animal-searching': {
        'name': '寻找动物',
        'attention_type': 'tracking',
        'dimensions': ['visual_tracking']
    },
    'level4': {
        'name': '工作记忆训练',
        'attention_type': 'memory',
        'dimensions': ['working_memory']
    },
    'card-matching': {
        'name': '记忆翻牌',
        'attention_type': 'memory',
        'dimensions': ['working_memory']
    },
    'reverse-memory': {
        'name': '倒序记忆',
        'attention_type': 'memory',
        'dimensions': ['working_memory']
    },
    'level5': {
        'name': '抑制控制训练',
        'attention_type': 'inhibitory',
        'dimensions': ['inhibitory_control']
    },
    'traffic-light': {
        'name': '红绿灯',
        'attention_type': 'inhibitory',
        'dimensions': ['inhibitory_control']
    },
    'command-adventure': {
        'name': '指令冒险',
        'attention_type': 'inhibitory',
        'dimensions': ['inhibitory_control']
    }
}

ATTENTION_TYPES = {
    'selective': {
        'name': '选择性注意',
        'description': '目标搜索 + 抗干扰 + 速度',
        'games': ['level1', 'schulte', 'find-numbers']
    },
    'sustained': {
        'name': '持续性注意',
        'description': '维持专注 + 抗疲劳 + 稳定性',
        'games': ['level2', 'magic-maze', 'water-plants']
    },
    'tracking': {
        'name': '视觉追踪',
        'description': '眼手协调 + 动态跟踪 + 连续专注',
        'games': ['level3', 'sun-tracking', 'animal-searching']
    },
    'memory': {
        'name': '工作记忆',
        'description': '短时存储 + 顺序保持 + 提取速度',
        'games': ['level4', 'card-matching', 'reverse-memory']
    },
    'inhibitory': {
        'name': '抑制控制',
        'description': '抑制冲动 + 遵守规则 + 抗干扰',
        'games': ['level5', 'traffic-light', 'command-adventure']
    }
}

ATTENTION_DIMENSIONS = {
    'selective_attention': '选择性注意力',
    'sustained_attention': '持续性注意力',
    'visual_tracking': '视觉追踪',
    'working_memory': '工作记忆',
    'inhibitory_control': '抑制控制'
}

SCORING_WEIGHTS = {
    'selective': {
        'accuracy': 0.35,
        'precision': 0.25,
        'speed': 0.20,
        'head_stable': 0.10,
        'blink_stable': 0.10
    },
    'sustained': {
        'stable_act': 0.30,
        'no_fatigue': 0.25,
        'speed': 0.20,
        'head_stable': 0.15,
        'blink_stable': 0.10
    },
    'tracking': {
        'accuracy': 0.35,
        'rt_score': 0.25,
        'speed': 0.20,
        'head_stable': 0.12,
        'face_stable': 0.08
    },
    'memory': {
        'accuracy': 0.40,
        'order': 0.20,
        'speed': 0.20,
        'head_stable': 0.12,
        'blink_stable': 0.08
    },
    'inhibitory': {
        'impulse': 0.40,
        'accuracy': 0.30,
        'head_stable': 0.15,
        'face_stable': 0.08,
        'blink_stable': 0.07
    }
}

PERFORMANCE_LEVELS = {
    'excellent': {'min': 90, 'max': 100, 'name': '优秀'},
    'good': {'min': 75, 'max': 89, 'name': '良好'},
    'average': {'min': 50, 'max': 74, 'name': '一般'},
    'weak': {'min': 0, 'max': 49, 'name': '较弱'}
}

DEFAULT_GAME_DATA = {
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
    'late_error_ratio': 0.0,
    'mean_rt': 1000
}

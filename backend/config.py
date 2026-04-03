import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', 'frontend')
DATA_DIR = os.path.join(BASE_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'attention.db')

DATABASE_CONFIG = {
    'db_path': DB_PATH
}

APP_CONFIG = {
    'debug': True,
    'host': '0.0.0.0',
    'port': 5000
}

GAME_TYPES = {
    'schulte': {
        'name': '舒尔特方格',
        'dimensions': ['selective_attention', 'sustained_attention']
    },
    'find-numbers': {
        'name': '找数字',
        'dimensions': ['selective_attention', 'visual_tracking']
    },
    'card-matching': {
        'name': '记忆翻牌',
        'dimensions': ['working_memory', 'sustained_attention']
    },
    'reverse-memory': {
        'name': '倒序记忆',
        'dimensions': ['working_memory']
    },
    'traffic-light': {
        'name': '红绿灯',
        'dimensions': ['inhibitory_control', 'sustained_attention']
    },
    'command-adventure': {
        'name': '指令冒险',
        'dimensions': ['inhibitory_control']
    },
    'magic-maze': {
        'name': '魔法迷宫',
        'dimensions': ['visual_tracking', 'sustained_attention']
    },
    'sun-tracking': {
        'name': '追踪太阳',
        'dimensions': ['visual_tracking']
    },
    'animal-searching': {
        'name': '寻找动物',
        'dimensions': ['selective_attention', 'visual_tracking']
    },
    'water-plants': {
        'name': '浇花游戏',
        'dimensions': ['sustained_attention', 'inhibitory_control']
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
    'visual': 0.6,
    'game': 0.4,
    'head_stability': 0.2,
    'focus_quality': 0.2,
    'blink_score': 0.1,
    'distance_score': 0.1,
    'accuracy': 0.2,
    'speed': 0.1,
    'completion': 0.1
}

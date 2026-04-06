const API_CONFIG = {
    BASE_URL: 'http://localhost:5000',
    TIMEOUT: 30000,
    CONTENT_TYPE: 'application/json',
    TOKEN_KEY: 'auth_token'
};

const ERROR_CODES = {
    AUTH_ERROR: 'AUTH_ERROR',
    PERMISSION_DENIED: 'PERMISSION_DENIED',
    NOT_FOUND: 'NOT_FOUND',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    SESSION_NOT_FOUND: 'SESSION_NOT_FOUND',
    SESSION_EXPIRED: 'SESSION_EXPIRED',
    CHILD_NOT_BELONG: 'CHILD_NOT_BELONG',
    ACTIVE_SESSION_EXISTS: 'ACTIVE_SESSION_EXISTS',
    INTERNAL_ERROR: 'INTERNAL_ERROR'
};

const GAME_TYPES = {
    level1: { name: '线索筛选站', attention_type: 'selective' },
    schulte: { name: '太空小火箭', attention_type: 'selective' },
    'find-numbers': { name: '垃圾小卫士', attention_type: 'selective' },
    level2: { name: '持续性注意训练', attention_type: 'sustained' },
    'magic-maze': { name: '魔法迷宫', attention_type: 'sustained' },
    'water-plants': { name: '浇花游戏', attention_type: 'sustained' },
    level3: { name: '视觉追踪训练', attention_type: 'tracking' },
    'sun-tracking': { name: '追踪太阳', attention_type: 'tracking' },
    'animal-searching': { name: '寻找动物', attention_type: 'tracking' },
    level4: { name: '工作记忆训练', attention_type: 'memory' },
    'card-matching': { name: '记忆翻牌', attention_type: 'memory' },
    'reverse-memory': { name: '倒序记忆', attention_type: 'memory' },
    level5: { name: '抑制控制训练', attention_type: 'inhibitory' },
    'traffic-light': { name: '红绿灯', attention_type: 'inhibitory' },
    'command-adventure': { name: '指令冒险', attention_type: 'inhibitory' }
};

const ATTENTION_TYPES = {
    selective: '选择性注意',
    sustained: '持续性注意',
    tracking: '视觉追踪',
    memory: '工作记忆',
    inhibitory: '抑制控制'
};

export { API_CONFIG, ERROR_CODES, GAME_TYPES, ATTENTION_TYPES };

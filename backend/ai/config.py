AI_CONFIG = {
    'api_url': '',
    'api_key': '',
    'model': '',
    'timeout': 30,
    'max_tokens': 1000,
    'temperature': 0.7,
}

def is_ai_configured():
    return bool(AI_CONFIG.get('api_url') and AI_CONFIG.get('api_key') and AI_CONFIG.get('model'))

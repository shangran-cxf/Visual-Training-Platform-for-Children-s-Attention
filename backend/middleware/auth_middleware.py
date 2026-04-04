import functools
from flask import request, jsonify
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from config import SECRET_KEY

serializer = URLSafeTimedSerializer(SECRET_KEY, salt='auth-token')

def generate_token(user_id: int, role: str) -> str:
    """
    生成 JWT token
    
    Args:
        user_id: 用户ID
        role: 用户角色
    
    Returns:
        str: 生成的 token
    """
    payload = {'user_id': user_id, 'role': role}
    return serializer.dumps(payload)

def verify_token(token: str) -> dict:
    """
    验证 token 并返回用户信息
    
    Args:
        token: 要验证的 token
    
    Returns:
        dict: 包含 user_id 和 role 的字典，验证失败返回 None
    """
    try:
        payload = serializer.loads(token, max_age=7 * 24 * 60 * 60)
        return payload
    except (BadSignature, SignatureExpired):
        return None

def require_auth(f):
    """
    验证用户是否登录的装饰器
    将 user_id 和 role 注入到 request 对象
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        if not token:
            return jsonify({'error': '缺少认证令牌'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': '无效或过期的令牌'}), 401
        
        request.user_id = payload.get('user_id')
        request.user_role = payload.get('role')
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    """
    验证用户是否为管理员的装饰器
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        if not token:
            return jsonify({'error': '缺少认证令牌'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': '无效或过期的令牌'}), 401
        
        if payload.get('role') != 'admin':
            return jsonify({'error': '权限不足，需要管理员权限'}), 403
        
        request.user_id = payload.get('user_id')
        request.user_role = payload.get('role')
        
        return f(*args, **kwargs)
    
    return decorated_function

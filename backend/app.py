from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
import traceback
import os

from config import FRONTEND_DIR, APP_CONFIG

# 打印FRONTEND_DIR路径
print(f'FRONTEND_DIR: {FRONTEND_DIR}')
print(f'FRONTEND_DIR exists: {os.path.exists(FRONTEND_DIR)}')
from database import init_db, execute_db
from modules import auth_bp, children_bp, forum_bp, knowledge_bp, badges_bp, admin_bp, user_stats_bp
from analytics import data_collector_bp
from middleware import verify_token
from utils.error_codes import (
    BAD_REQUEST, AUTH_ERROR, PERMISSION_DENIED, 
    NOT_FOUND, INTERNAL_ERROR, VALIDATION_ERROR
)
from utils.response_utils import error_response

app = Flask(__name__)
# app.static_folder = FRONTEND_DIR
CORS(app)

init_db()

PUBLIC_PATHS = [
    '/api/login',
    '/api/register',
    '/api/verify-password',
]

@app.before_request
def verify_auth_token():
    if request.path in PUBLIC_PATHS:
        return
    
    if request.path.startswith('/api/user/info') and request.method == 'GET':
        return
    
    if request.path.startswith('/api/user/by-') and request.method == 'GET':
        return
    
    if request.path.startswith('/api/user/level/') and request.method == 'GET':
        return
    
    if request.path.startswith('/api/user/posts/') and request.method == 'GET':
        return
    
    if request.path.startswith('/api/user/stats/') and request.method == 'GET':
        return
    
    if not request.path.startswith('/api/'):
        return
    
    token = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]
    
    if token:
        payload = verify_token(token)
        if payload:
            g.user_id = payload.get('user_id')
            g.user_role = payload.get('role')
            request.user_id = payload.get('user_id')
            request.user_role = payload.get('role')
        else:
            g.user_id = None
            g.user_role = None
    else:
        g.user_id = None
        g.user_role = None

@app.errorhandler(400)
def handle_bad_request(error):
    return error_response(
        message=str(error.description) if hasattr(error, 'description') else '请求参数错误',
        code=BAD_REQUEST,
        status=400
    )

@app.errorhandler(401)
def handle_unauthorized(error):
    return error_response(
        message=str(error.description) if hasattr(error, 'description') else '认证失败',
        code=AUTH_ERROR,
        status=401
    )

@app.errorhandler(403)
def handle_forbidden(error):
    return error_response(
        message=str(error.description) if hasattr(error, 'description') else '权限不足',
        code=PERMISSION_DENIED,
        status=403
    )

@app.errorhandler(404)
def handle_not_found(error):
    if request.path.startswith('/api/'):
        return error_response(
            message='请求的资源不存在',
            code=NOT_FOUND,
            status=404
        )
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.errorhandler(405)
def handle_method_not_allowed(error):
    return error_response(
        message='请求方法不允许',
        code=BAD_REQUEST,
        status=405
    )

@app.errorhandler(500)
def handle_internal_error(error):
    app.logger.error(f'Internal Server Error: {str(error)}\n{traceback.format_exc()}')
    return error_response(
        message='服务器内部错误',
        code=INTERNAL_ERROR,
        status=500
    )

@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error(f'Unhandled Exception: {str(error)}\n{traceback.format_exc()}')
    return error_response(
        message='服务器内部错误',
        code=INTERNAL_ERROR,
        status=500
    )

app.register_blueprint(auth_bp)
app.register_blueprint(children_bp)
app.register_blueprint(forum_bp, url_prefix='/api/forum')
app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
app.register_blueprint(badges_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_stats_bp)

app.register_blueprint(data_collector_bp)

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    import os
    upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
    return send_from_directory(upload_folder, filename)

if __name__ == '__main__':
    app.run(
        debug=APP_CONFIG['debug'],
        host=APP_CONFIG['host'],
        port=APP_CONFIG['port']
    )

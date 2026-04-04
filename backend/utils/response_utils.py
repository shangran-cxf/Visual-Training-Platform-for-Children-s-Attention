from flask import jsonify
from utils.error_codes import ERROR_MESSAGES, HTTP_STATUS_MAP


def success_response(data=None, message: str = '操作成功') -> tuple:
    response = {
        'success': True,
        'message': message,
        'data': data
    }
    return jsonify(response), 200


def error_response(message: str = None, code: str = 'ERROR', status: int = 400) -> tuple:
    if message is None:
        message = ERROR_MESSAGES.get(code, '操作失败')
    if status is None:
        status = HTTP_STATUS_MAP.get(code, 400)
    response = {
        'success': False,
        'error': {
            'code': code,
            'message': message
        }
    }
    return jsonify(response), status


def make_error_response(code: str, message: str = None, status: int = None) -> tuple:
    if message is None:
        message = ERROR_MESSAGES.get(code, '操作失败')
    if status is None:
        status = HTTP_STATUS_MAP.get(code, 500)
    return error_response(message, code, status)

import { ERROR_CODES } from './config.js';
import { removeToken } from './request.js';

const ERROR_MESSAGES = {
    [ERROR_CODES.AUTH_ERROR]: '认证失败，请重新登录',
    [ERROR_CODES.PERMISSION_DENIED]: '权限不足',
    [ERROR_CODES.CHILD_NOT_BELONG]: '无权访问该孩子数据',
    [ERROR_CODES.NOT_FOUND]: '资源不存在',
    [ERROR_CODES.SESSION_NOT_FOUND]: '训练会话不存在',
    [ERROR_CODES.SESSION_EXPIRED]: '训练会话已过期',
    [ERROR_CODES.ACTIVE_SESSION_EXISTS]: '已存在活跃的训练会话',
    [ERROR_CODES.VALIDATION_ERROR]: '请求参数错误',
    [ERROR_CODES.INTERNAL_ERROR]: '服务器错误，请稍后重试'
};

function getErrorMessage(code) {
    return ERROR_MESSAGES[code] || '未知错误';
}

function handleApiError(response, statusCode) {
    if (response && response.error) {
        const { code, message } = response.error;
        
        if (code === ERROR_CODES.AUTH_ERROR) {
            removeToken();
            if (typeof window !== 'undefined') {
                window.location.href = '/login.html';
            }
        }
        
        return {
            success: false,
            error: {
                code,
                message: message || getErrorMessage(code)
            }
        };
    }
    
    return {
        success: false,
        error: {
            code: ERROR_CODES.INTERNAL_ERROR,
            message: `请求失败 (${statusCode})`
        }
    };
}

function showError(code, customMessage = null) {
    const message = customMessage || getErrorMessage(code);
    
    if (typeof window !== 'undefined' && window.alert) {
        alert(message);
    }
    
    return message;
}

function handleSessionExpired() {
    showError(ERROR_CODES.SESSION_EXPIRED);
    if (typeof window !== 'undefined') {
        window.location.href = '/training/index.html';
    }
}

function handleActiveSessionExists(sessionId) {
    const continueTraining = confirm('已有进行中的训练，是否继续？');
    if (continueTraining && sessionId) {
        return sessionId;
    }
    return null;
}

export {
    ERROR_MESSAGES,
    getErrorMessage,
    handleApiError,
    showError,
    handleSessionExpired,
    handleActiveSessionExists
};

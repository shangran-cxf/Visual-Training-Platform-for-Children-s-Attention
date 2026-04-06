import { API_CONFIG, ERROR_CODES } from './config.js';
import { handleApiError, getErrorMessage } from './errors.js';

function getToken() {
    return localStorage.getItem(API_CONFIG.TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(API_CONFIG.TOKEN_KEY, token);
}

function removeToken() {
    localStorage.removeItem(API_CONFIG.TOKEN_KEY);
}

function isAuthenticated() {
    return !!getToken();
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

async function apiRequest(url, options = {}) {
    const token = getToken();
    
    const headers = {
        'Content-Type': API_CONFIG.CONTENT_TYPE,
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT);
    
    try {
        const response = await fetch(`${API_CONFIG.BASE_URL}${url}`, {
            ...options,
            headers,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const data = await response.json();
        
        if (!response.ok || (data && data.success === false)) {
            return handleApiError(data, response.status);
        }
        
        return data;
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            return {
                success: false,
                error: {
                    code: 'TIMEOUT',
                    message: '请求超时，请稍后重试'
                }
            };
        }
        
        return {
            success: false,
            error: {
                code: ERROR_CODES.INTERNAL_ERROR,
                message: '网络错误，请检查网络连接'
            }
        };
    }
}

async function apiGet(url, params = {}) {
    const queryString = new URLSearchParams(
        Object.entries(params).filter(([_, v]) => v !== undefined && v !== null)
    ).toString();
    
    const fullUrl = queryString ? `${url}?${queryString}` : url;
    
    return apiRequest(fullUrl, { method: 'GET' });
}

async function apiPost(url, data = {}) {
    return apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

export {
    getToken,
    setToken,
    removeToken,
    isAuthenticated,
    generateUUID,
    apiRequest,
    apiGet,
    apiPost
};

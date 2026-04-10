// 通用工具函数

// Canvas 基础绘图工具
const CanvasUtil = {
    createCanvas: (width, height) => {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        return canvas;
    },

    drawCartoonElement: (ctx, x, y, width, height, color, type = 'circle') => {
        ctx.fillStyle = color;
        if (type === 'circle') {
            ctx.beginPath();
            ctx.arc(x, y, width / 2, 0, Math.PI * 2);
            ctx.fill();
        } else if (type === 'rect') {
            ctx.fillRect(x - width / 2, y - height / 2, width, height);
        }
    },

    drawText: (ctx, text, x, y, size = 16, color = '#333') => {
        ctx.font = `${size}px Arial`;
        ctx.fillStyle = color;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, x, y);
    }
};

// 事件监听工具
const EventUtil = {
    addClickEvent: (element, callback) => {
        element.addEventListener('click', callback);
        element.addEventListener('touchstart', callback);
    },

    addKeyEvent: (callback) => {
        document.addEventListener('keydown', callback);
    },

    addEyeTrackingEvent: (callback) => {
        document.addEventListener('mousemove', (e) => {
            callback({ x: e.clientX, y: e.clientY });
        });
    }
};

// 本地存储工具
const StorageUtil = {
    setItem: (key, value) => {
        localStorage.setItem(key, JSON.stringify(value));
    },

    getItem: (key) => {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
    },

    removeItem: (key) => {
        localStorage.removeItem(key);
    },

    clear: () => {
        localStorage.clear();
    }
};

// 音频/语音调用工具
const AudioUtil = {
    playAudio: (url) => {
        const audio = new Audio(url);
        audio.play();
        return audio;
    },

    speak: (text, rate = 1) => {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = rate;
            speechSynthesis.speak(utterance);
            return utterance;
        }
        return null;
    },

    stopSpeaking: () => {
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
    }
};

/**
 * 用户状态管理工具
 * 
 * 重要说明：
 * - 身份认证只验证 role（admin/user），不验证 mode
 * - mode（parent/child）是用户状态，用于区分当前使用模式
 * - mode 不应用于页面访问权限判断
 */
const UserStateUtil = {
    USER_INFO_KEY: 'userInfo',

    getUserInfo: () => {
        return StorageUtil.getItem(UserStateUtil.USER_INFO_KEY);
    },

    setUserInfo: (info) => {
        StorageUtil.setItem(UserStateUtil.USER_INFO_KEY, info);
    },

    clearUserInfo: () => {
        StorageUtil.removeItem(UserStateUtil.USER_INFO_KEY);
    },

    // ========== 身份认证相关（用于权限判断）==========

    getRole: () => {
        const info = UserStateUtil.getUserInfo();
        return info ? info.role : null;
    },

    isAdmin: () => {
        return UserStateUtil.getRole() === 'admin';
    },

    isUser: () => {
        return UserStateUtil.getRole() === 'user';
    },

    isLoggedIn: () => {
        return UserStateUtil.getUserInfo() !== null;
    },

    // ========== 用户状态相关（不用于权限判断）==========

    getMode: () => {
        const info = UserStateUtil.getUserInfo();
        return info ? info.mode : null;
    },

    isParentMode: () => {
        return UserStateUtil.getMode() === 'parent';
    },

    isChildMode: () => {
        return UserStateUtil.getMode() === 'child';
    },

    setMode: (mode) => {
        const info = UserStateUtil.getUserInfo();
        if (info) {
            info.mode = mode;
            UserStateUtil.setUserInfo(info);
        }
    },

    getCurrentChildId: () => {
        const info = UserStateUtil.getUserInfo();
        return info ? info.currentChildId : null;
    },

    setCurrentChildId: (childId) => {
        const info = UserStateUtil.getUserInfo();
        if (info) {
            info.currentChildId = childId;
            UserStateUtil.setUserInfo(info);
        }
    },

    getCurrentChildName: () => {
        const info = UserStateUtil.getUserInfo();
        return info ? info.currentChildName : null;
    },

    setCurrentChildName: (name) => {
        const info = UserStateUtil.getUserInfo();
        if (info) {
            info.currentChildName = name;
            UserStateUtil.setUserInfo(info);
        }
    },

    getChildren: () => {
        const info = UserStateUtil.getUserInfo();
        return info ? info.children : [];
    },

    selectChild: (childId, childName) => {
        const info = UserStateUtil.getUserInfo();
        if (info) {
            info.currentChildId = childId;
            info.currentChildName = childName;
            info.mode = 'child';
            UserStateUtil.setUserInfo(info);
        }
    },

    switchToParentMode: () => {
        UserStateUtil.setMode('parent');
    },

    switchToChildMode: (childId, childName) => {
        UserStateUtil.selectChild(childId, childName);
    },

    // ========== 权限验证函数（只验证登录和 role）==========

    requireLogin: (redirectUrl = 'login.html') => {
        if (!UserStateUtil.isLoggedIn()) {
            window.location.href = redirectUrl;
            return false;
        }
        return true;
    },

    requireAdmin: (redirectUrl = 'index.html') => {
        if (!UserStateUtil.isAdmin()) {
            window.location.href = redirectUrl;
            return false;
        }
        return true;
    },

    initFromLoginResponse: (response) => {
        console.log('登录响应:', response);
        const userInfo = {
            parent_id: response.parent_id || response.user_id || response.id,
            userId: response.parent_id || response.user_id || response.id,
            uid: response.uid,
            username: response.username,
            email: response.email,
            role: response.role,
            children: response.children || [],
            mode: null,
            currentChildId: null,
            currentChildName: null
        };
        console.log('存储的用户信息:', userInfo);
        UserStateUtil.setUserInfo(userInfo);
        if (response.token) {
            localStorage.setItem('auth_token', response.token);
        }
        return userInfo;
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CanvasUtil,
        EventUtil,
        StorageUtil,
        AudioUtil,
        UserStateUtil,
        ApiUtil
    };
}

const ApiUtil = {
    getToken: () => {
        return localStorage.getItem('auth_token');
    },

    handleResponse: async (response) => {
        const data = await response.json();
        if (data.success === false) {
            throw new Error(data.error?.message || '请求失败');
        }
        return data.data !== undefined ? data.data : data;
    },

    handleError: (error) => {
        console.error('API Error:', error);
        throw error;
    },

    fetch: async (url, options = {}) => {
        try {
            const response = await fetch(url, options);
            return await ApiUtil.handleResponse(response);
        } catch (error) {
            return ApiUtil.handleError(error);
        }
    },

    apiGet: async (url, params = {}) => {
        const queryString = new URLSearchParams(
            Object.entries(params).filter(([_, v]) => v !== undefined && v !== null)
        ).toString();

        const fullUrl = queryString ? `${url}?${queryString}` : url;

        const token = ApiUtil.getToken();
        const headers = {
            'Content-Type': 'application/json'
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(fullUrl, {
            method: 'GET',
            headers
        });

        return response;
    },

    apiPost: async (url, data = {}) => {
        const token = ApiUtil.getToken();
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(url, {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });
        
        return response;
    }
};

const GameTimeUtil = {
    gameStartTime: null,
    currentGame: null,
    
    startGame: function(gameName) {
        this.gameStartTime = Date.now();
        this.currentGame = gameName;
        console.log(`🎮 游戏开始: ${gameName}`);
    },
    
    endGame: function(gameName) {
        const endTime = Date.now();
        
        if (!this.gameStartTime) {
            this.gameStartTime = endTime - 60000;
            console.warn('GameTimeUtil: 游戏开始时间未记录，使用默认值');
        }
        
        const duration = Math.floor((endTime - this.gameStartTime) / 1000);
        
        const gameData = {
            gameName: gameName || this.currentGame || 'unknown',
            startTime: new Date(this.gameStartTime).toISOString(),
            endTime: new Date(endTime).toISOString(),
            duration: duration
        };
        
        console.log(`🎮 游戏结束: ${gameData.gameName}, 用时: ${duration}秒`);
        
        try {
            const history = StorageUtil.getItem('game_time_history') || [];
            history.push(gameData);
            if (history.length > 50) history.shift();
            StorageUtil.setItem('game_time_history', history);
        } catch (e) {
            console.warn('GameTimeUtil: 无法保存游戏历史', e);
        }
        
        this.gameStartTime = null;
        this.currentGame = null;
        
        return gameData;
    },
    
    getGameDuration: function() {
        if (!this.gameStartTime) return 0;
        return Math.floor((Date.now() - this.gameStartTime) / 1000);
    },
    
    isGameRunning: function() {
        return this.gameStartTime !== null;
    }
};

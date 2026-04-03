// 通用工具函数

// Canvas 基础绘图工具
const CanvasUtil = {
    // 创建 Canvas 元素
    createCanvas: (width, height) => {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        return canvas;
    },

    // 绘制卡通元素
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

    // 绘制文本
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
    // 添加点击/触控事件
    addClickEvent: (element, callback) => {
        element.addEventListener('click', callback);
        element.addEventListener('touchstart', callback);
    },

    // 添加键盘事件
    addKeyEvent: (callback) => {
        document.addEventListener('keydown', callback);
    },

    // 视线追踪事件（模拟）
    addEyeTrackingEvent: (callback) => {
        // 实际项目中可集成视觉模型
        document.addEventListener('mousemove', (e) => {
            callback({ x: e.clientX, y: e.clientY });
        });
    }
};

// 本地存储工具
const StorageUtil = {
    // 存储数据
    setItem: (key, value) => {
        localStorage.setItem(key, JSON.stringify(value));
    },

    // 获取数据
    getItem: (key) => {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
    },

    // 删除数据
    removeItem: (key) => {
        localStorage.removeItem(key);
    },

    // 清空所有数据
    clear: () => {
        localStorage.clear();
    }
};

// 音频/语音调用工具
const AudioUtil = {
    // 播放音频
    playAudio: (url) => {
        const audio = new Audio(url);
        audio.play();
        return audio;
    },

    // 语音合成
    speak: (text, rate = 1) => {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = rate;
            speechSynthesis.speak(utterance);
            return utterance;
        }
        return null;
    },

    // 停止语音
    stopSpeaking: () => {
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
    }
};

// 游戏时间统计工具
const GameTimeUtil = {
    // 结束游戏并统计时间
    endGame: (gameName) => {
        // 从localStorage获取游戏开始时间
        const gameStartTime = localStorage.getItem('gameStartTime');
        const currentGame = localStorage.getItem('currentGame');
        
        if (gameStartTime) {
            // 计算游戏使用时间
            const gameEndTime = new Date().getTime();
            const duration = Math.floor((gameEndTime - parseInt(gameStartTime)) / 1000); // 转换为秒
            
            // 获取今天的日期作为键
            const today = new Date().toISOString().split('T')[0];
            
            // 从localStorage读取现有数据
            const trainingData = JSON.parse(localStorage.getItem('trainingData') || '{}');
            
            // 初始化今天的数据
            if (!trainingData[today]) {
                trainingData[today] = {
                    totalTime: 0,
                    comprehensiveTraining: 0,
                    games: {}
                };
            }
            
            // 更新游戏时间
            const gameKey = gameName || currentGame;
            if (gameKey) {
                if (!trainingData[today].games[gameKey]) {
                    trainingData[today].games[gameKey] = 0;
                }
                trainingData[today].games[gameKey] += duration;
            }
            
            // 更新总训练时间
            trainingData[today].totalTime += duration;
            
            // 保存回localStorage
            localStorage.setItem('trainingData', JSON.stringify(trainingData));
            
            // 清除游戏开始时间
            localStorage.removeItem('gameStartTime');
            localStorage.removeItem('currentGame');
            
            console.log('游戏时间已保存:', duration, '秒');
            return duration;
        }
        return 0;
    },
    
    // 获取今日游戏时间统计
    getTodayStats: () => {
        const today = new Date().toISOString().split('T')[0];
        const trainingData = JSON.parse(localStorage.getItem('trainingData') || '{}');
        return trainingData[today] || {
            totalTime: 0,
            comprehensiveTraining: 0,
            games: {}
        };
    }
};

// 导出工具函数
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CanvasUtil,
        EventUtil,
        StorageUtil,
        AudioUtil,
        GameTimeUtil
    };
}
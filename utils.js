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

// 导出工具函数
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CanvasUtil,
        EventUtil,
        StorageUtil,
        AudioUtil
    };
}
/**
 * 可移动小球 + 专注力检测面板 + 卡通云朵提示
 */

(function() {
    // ========== 所有变量声明放在最前面 ==========
    let faceLandmarker = null;
    let videoElement = null;
    let stream = null;
    let animationId = null;
    let isDetecting = false;
    
    // 监测数据
    let detectionData = {
        attentionScore: 0,
        isFaceDetected: false,
        headYaw: 0,
        headPitch: 0,
        faceArea: 0,
        blinkRate: 0,
        focusDuration: 0
    };
    
    let lastBlinkTime = 0;
    let blinkCount = 0;
    let focusStartTime = Date.now();
    
    // 提醒状态变量
    let wasDistracted = false;
    let wasTooClose = false;
    let wasTooFar = false;
    let lastTipTime = 0;
    
    // 当前提示显示状态
    let isDistractedTipShowing = false;
    let isTooCloseTipShowing = false;
    let isTooFarTipShowing = false;
    let isNoFaceTipShowing = false;
    
    // 当前显示的云朵
    let currentCloud = null;
    let currentTipType = null;
    
    // 面板状态 ← 这些一定要在 init 之前
    let isPanelOpen = false;
    let floatingBall = null;
    let panel = null;
    let panelUpdateInterval = null;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    async function init() {
        createFloatingBall();
        await startCamera();
        startDetection();
    }
    
    // ==================== 云朵提示 ====================
    function showCloudTip(message, type, persistent = false) {
        // 如果已经是相同类型的提示，不重复创建
        if (currentTipType === type && currentCloud) return;
        
        // 移除旧提示
        if (currentCloud) {
            currentCloud.remove();
            currentCloud = null;
        }
        
        // 创建云朵容器
        const cloud = document.createElement('div');
        cloud.id = 'cloud-tip';
        cloud.innerHTML = `
            <div style="
                position: relative;
                background: white;
                border-radius: 30px;
                padding: 10px 18px;
                min-width: 130px;
                max-width: 220px;
                text-align: center;
                font-family: 'Comic Neue', 'Comic Sans MS', 'Chalkboard SE', cursive;
                font-size: 14px;
                font-weight: bold;
                color: #5a4a2a;
                box-shadow: 0 6px 16px rgba(0,0,0,0.2);
                border: 2px solid #ffe0b5;
                background: linear-gradient(135deg, #fff9e8, #fff5e0);
                animation: cloudFloat 0.3s ease-out;
            ">
                <span style="display: block;">${message}</span>
                <div style="
                    position: absolute;
                    bottom: -12px;
                    left: 15px;
                    width: 25px;
                    height: 25px;
                    background: white;
                    border-radius: 50%;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                    border: 2px solid #ffe0b5;
                "></div>
                <div style="
                    position: absolute;
                    bottom: -20px;
                    left: 38px;
                    width: 18px;
                    height: 18px;
                    background: white;
                    border-radius: 50%;
                    border: 2px solid #ffe0b5;
                "></div>
                <div style="
                    position: absolute;
                    bottom: -16px;
                    left: 58px;
                    width: 22px;
                    height: 22px;
                    background: white;
                    border-radius: 50%;
                    border: 2px solid #ffe0b5;
                "></div>
            </div>
        `;
        
        // 添加动画样式
        const style = document.getElementById('cloud-style');
        if (!style) {
            const newStyle = document.createElement('style');
            newStyle.id = 'cloud-style';
            newStyle.textContent = `
                @keyframes cloudFloat {
                    0% { opacity: 0; transform: translateY(10px) scale(0.9); }
                    100% { opacity: 1; transform: translateY(0) scale(1); }
                }
                @keyframes cloudPulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.02); }
                    100% { transform: scale(1); }
                }
            `;
            document.head.appendChild(newStyle);
        }
        
        // 获取小球位置
        const ballRect = floatingBall.getBoundingClientRect();
        
        // 设置云朵位置（在小球上方）
        let top = ballRect.top - 65;
        let left = ballRect.left + ballRect.width / 2 - 70;
        
        // 边界处理
        if (top < 10) {
            top = ballRect.bottom + 10;
        }
        if (left < 10) {
            left = 10;
        }
        if (left + 150 > window.innerWidth) {
            left = window.innerWidth - 160;
        }
        
        Object.assign(cloud.style, {
            position: 'fixed',
            top: top + 'px',
            left: left + 'px',
            zIndex: '10000',
            cursor: 'default',
            pointerEvents: 'none'
        });
        
        // 持续显示的提示添加脉冲动画
        if (persistent) {
            cloud.style.animation = 'cloudPulse 1.5s ease-in-out infinite';
        }
        
        document.body.appendChild(cloud);
        currentCloud = cloud;
        currentTipType = type;
    }
    
    function hideCloudTip() {
        if (currentCloud) {
            currentCloud.remove();
            currentCloud = null;
            currentTipType = null;
        }
    }
    
    // ==================== 小球创建 ====================
    function createFloatingBall() {
        floatingBall = document.createElement('div');
        floatingBall.id = 'floating-attention-ball';
        floatingBall.innerHTML = `
            <div style="
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, #4caf50, #81c784);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
                position: relative;
            ">
                <span style="font-size: 24px;">🎯</span>
                <div id="ball-score" style="
                    position: absolute;
                    bottom: -5px;
                    right: -5px;
                    background: #ff9800;
                    color: white;
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">0</div>
            </div>
        `;
        
        Object.assign(floatingBall.style, {
            position: 'fixed',
            bottom: '100px',
            right: '20px',
            zIndex: '9998',
            cursor: 'move',
            userSelect: 'none'
        });
        
        floatingBall.addEventListener('click', (e) => {
            e.stopPropagation();
            togglePanel();
        });
        
        makeDraggable(floatingBall, true);
        document.body.appendChild(floatingBall);
    }
    
    function makeDraggable(element, withPanel = false) {
        let isDragging = false;
        let startX, startY, startLeft, startTop;
        let panelStartLeft, panelStartTop;
        
        element.addEventListener('mousedown', (e) => {
            if (e.target === element || element.contains(e.target)) {
                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;
                startLeft = element.offsetLeft;
                startTop = element.offsetTop;
                
                if (withPanel && panel && isPanelOpen) {
                    panelStartLeft = panel.offsetLeft;
                    panelStartTop = panel.offsetTop;
                }
                
                element.style.cursor = 'grabbing';
                e.preventDefault();
            }
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            let deltaX = e.clientX - startX;
            let deltaY = e.clientY - startY;
            
            let newLeft = startLeft + deltaX;
            let newTop = startTop + deltaY;
            
            newLeft = Math.max(0, Math.min(window.innerWidth - element.offsetWidth, newLeft));
            newTop = Math.max(0, Math.min(window.innerHeight - element.offsetHeight, newTop));
            
            element.style.left = newLeft + 'px';
            element.style.top = newTop + 'px';
            element.style.right = 'auto';
            element.style.bottom = 'auto';
            
            if (withPanel && panel && isPanelOpen) {
                let panelNewLeft = panelStartLeft + deltaX;
                let panelNewTop = panelStartTop + deltaY;
                
                panelNewLeft = Math.max(0, Math.min(window.innerWidth - panel.offsetWidth, panelNewLeft));
                panelNewTop = Math.max(0, Math.min(window.innerHeight - panel.offsetHeight, panelNewTop));
                
                panel.style.left = panelNewLeft + 'px';
                panel.style.top = panelNewTop + 'px';
                panel.style.right = 'auto';
                panel.style.bottom = 'auto';
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                element.style.cursor = 'move';
            }
        });
    }
    
    // ==================== 面板 ====================
    function createPanel() {
        panel = document.createElement('div');
        panel.id = 'attention-panel';
        panel.innerHTML = `
            <div style="
                background: rgba(30, 30, 40, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                width: 320px;
                color: white;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                border: 1px solid rgba(255,255,255,0.2);
                overflow: hidden;
            ">
                <div style="
                    padding: 15px 20px;
                    background: linear-gradient(135deg, #4caf50, #81c784);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    cursor: move;
                " id="panel-header">
                    <span style="font-weight: bold;">🔍 专注力检测</span>
                    <button id="close-panel" style="
                        background: none;
                        border: none;
                        color: white;
                        font-size: 20px;
                        cursor: pointer;
                        width: 30px;
                        height: 30px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">✕</button>
                </div>
                
                <div style="padding: 20px;">
                    <div style="margin-bottom: 15px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span>🎯 专注度</span>
                            <span id="panel-score">0分</span>
                        </div>
                        <div style="background: rgba(255,255,255,0.2); border-radius: 10px; height: 8px; overflow: hidden;">
                            <div id="panel-score-bar" style="width: 0%; height: 100%; background: #4caf50; border-radius: 10px; transition: width 0.3s;"></div>
                        </div>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <span>👤 人脸状态</span>
                        <span id="panel-face-status">--</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <span>📐 头部转角</span>
                        <span id="panel-head-angle">0°</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <span>📏 屏幕距离</span>
                        <span id="panel-distance">--</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <span>👁️ 眨眼频率</span>
                        <span id="panel-blink-rate">0次/秒</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 12px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                        <span>⏱️ 持续专注</span>
                        <span id="panel-focus-time">00:00</span>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button id="panel-close-btn" style="
                            flex: 1;
                            background: rgba(255,255,255,0.2);
                            border: none;
                            color: white;
                            padding: 8px;
                            border-radius: 10px;
                            cursor: pointer;
                        ">🔒 关闭面板</button>
                    </div>
                </div>
            </div>
        `;
        
        Object.assign(panel.style, {
            position: 'fixed',
            bottom: '170px',
            right: '20px',
            zIndex: '9999',
            display: 'none'
        });
        
        panel.querySelector('#close-panel').addEventListener('click', () => closePanel());
        panel.querySelector('#panel-close-btn').addEventListener('click', () => closePanel());
        
        const header = panel.querySelector('#panel-header');
        makeDraggableElement(panel, header);
        
        document.body.appendChild(panel);
    }
    
    function makeDraggableElement(element, handle) {
        let isDragging = false;
        let startX, startY, startLeft, startTop;
        
        handle.addEventListener('mousedown', (e) => {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            startLeft = element.offsetLeft;
            startTop = element.offsetTop;
            handle.style.cursor = 'grabbing';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            
            let newLeft = startLeft + (e.clientX - startX);
            let newTop = startTop + (e.clientY - startY);
            
            newLeft = Math.max(0, Math.min(window.innerWidth - element.offsetWidth, newLeft));
            newTop = Math.max(0, Math.min(window.innerHeight - element.offsetHeight, newTop));
            
            element.style.left = newLeft + 'px';
            element.style.top = newTop + 'px';
            element.style.right = 'auto';
            element.style.bottom = 'auto';
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                handle.style.cursor = 'move';
            }
        });
    }
    
    function togglePanel() {
        if (isPanelOpen) closePanel();
        else openPanel();
    }
    
    function openPanel() {
        if (!panel) createPanel();
        
        const ballRect = floatingBall.getBoundingClientRect();
        let panelLeft = ballRect.right + 10;
        let panelTop = ballRect.top;
        
        if (panelLeft + 320 > window.innerWidth) {
            panelLeft = ballRect.left - 330;
        }
        if (panelTop + 400 > window.innerHeight) {
            panelTop = window.innerHeight - 420;
        }
        if (panelTop < 10) panelTop = 10;
        
        panel.style.left = panelLeft + 'px';
        panel.style.top = panelTop + 'px';
        panel.style.right = 'auto';
        panel.style.bottom = 'auto';
        panel.style.display = 'block';
        
        isPanelOpen = true;
        updatePanelData();
        if (panelUpdateInterval) clearInterval(panelUpdateInterval);
        panelUpdateInterval = setInterval(updatePanelData, 500);
    }
    
    function closePanel() {
        if (panel) panel.style.display = 'none';
        isPanelOpen = false;
        if (panelUpdateInterval) {
            clearInterval(panelUpdateInterval);
            panelUpdateInterval = null;
        }
    }
    
    function updatePanelData() {
        if (!panel) return;
        panel.querySelector('#panel-score').textContent = detectionData.attentionScore + '分';
        panel.querySelector('#panel-score-bar').style.width = detectionData.attentionScore + '%';
        panel.querySelector('#panel-face-status').textContent = detectionData.isFaceDetected ? '✅ 已检测' : '❌ 未检测';
        
        let angleText = detectionData.headYaw > 0 ? `右转 ${Math.abs(detectionData.headYaw).toFixed(0)}°` : 
                       detectionData.headYaw < 0 ? `左转 ${Math.abs(detectionData.headYaw).toFixed(0)}°` : '正对';
        panel.querySelector('#panel-head-angle').textContent = angleText;
        
        let distanceText = detectionData.faceArea > 0.5 ? '⚠️ 太近' : 
                          detectionData.faceArea < 0.08 ? '⚠️ 太远' : '✅ 适中';
        panel.querySelector('#panel-distance').textContent = distanceText;
        panel.querySelector('#panel-blink-rate').textContent = (detectionData.blinkRate / 60).toFixed(1) + '次/秒';
        
        const minutes = Math.floor(detectionData.focusDuration / 60);
        const seconds = detectionData.focusDuration % 60;
        panel.querySelector('#panel-focus-time').textContent = `${minutes.toString().padStart(2,'0')}:${seconds.toString().padStart(2,'0')}`;
    }
    
    function updateBallScore() {
        const scoreElement = floatingBall?.querySelector('#ball-score');
        if (scoreElement) {
            scoreElement.textContent = detectionData.attentionScore;
            const ballDiv = floatingBall.querySelector('div');
            if (detectionData.attentionScore >= 80) ballDiv.style.background = 'linear-gradient(135deg, #4caf50, #81c784)';
            else if (detectionData.attentionScore >= 60) ballDiv.style.background = 'linear-gradient(135deg, #ff9800, #ffb74d)';
            else ballDiv.style.background = 'linear-gradient(135deg, #f44336, #ef5350)';
        }
    }
    
    async function startCamera() {
        console.log('正在请求摄像头...');
        
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            console.log('摄像头权限已获取');
        } catch (err) {
            console.error('摄像头获取失败:', err);
            return;
        }
        
        videoElement = document.createElement('video');
        videoElement.autoplay = true;
        videoElement.muted = true;
        videoElement.playsInline = true;
        videoElement.style.cssText = 'position: fixed; top: 0; left: 0; width: 1px; height: 1px; opacity: 0; pointer-events: none;';
        document.body.appendChild(videoElement);
        
        videoElement.srcObject = stream;
        await videoElement.play();
        console.log('摄像头已启动');
        
        await waitForFilesetResolver();
        
        const vision = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/wasm");
        faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
            baseOptions: {
                modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
                delegate: "GPU"
            },
            runningMode: "VIDEO",
            numFaces: 1,
            minFaceDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });
        isDetecting = true;
        console.log('人脸检测模型已加载');
    }
    
    function waitForFilesetResolver() {
        return new Promise((resolve) => {
            if (typeof FilesetResolver !== 'undefined') {
                resolve();
                return;
            }
            const checkInterval = setInterval(() => {
                if (typeof FilesetResolver !== 'undefined') {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
        });
    }
    
    function startDetection() {
        function detect() {
            if (!isDetecting || !faceLandmarker || !videoElement) {
                animationId = requestAnimationFrame(detect);
                return;
            }
            if (videoElement.videoWidth && videoElement.videoHeight) {
                const results = faceLandmarker.detectForVideo(videoElement, performance.now());
                
                if (results.faceLandmarks && results.faceLandmarks.length > 0) {
                    const landmarks = results.faceLandmarks[0];
                    
                    // 检测到人脸时，清除无人脸提示
                    if (isNoFaceTipShowing) {
                        isNoFaceTipShowing = false;
                        hideCloudTip();
                    }
                    
                    const leftCheek = landmarks[234];
                    const rightCheek = landmarks[454];
                    const nose = landmarks[1];
                    const chin = landmarks[152];
                    const forehead = landmarks[10];
                    
                    const faceWidth = Math.abs(leftCheek.x - rightCheek.x);
                    const noseOffset = (nose.x - (leftCheek.x + rightCheek.x) / 2) / faceWidth;
                    const yaw = noseOffset * 60;
                    
                    const faceHeight = Math.abs(chin.y - forehead.y);
                    const noseYOffset = (nose.y - (forehead.y + chin.y) / 2) / faceHeight;
                    const pitch = noseYOffset * 45;
                    
                    const faceArea = faceWidth * faceHeight;
                    
                    // ===== 眨眼检测 =====
                    const leftEyeTop = landmarks[159];
                    const leftEyeBottom = landmarks[145];
                    const rightEyeTop = landmarks[386];
                    const rightEyeBottom = landmarks[374];
                    
                    const leftDistance = Math.abs(leftEyeTop.y - leftEyeBottom.y);
                    const rightDistance = Math.abs(rightEyeTop.y - rightEyeBottom.y);
                    const eyeDistance = (leftDistance + rightDistance) / 2;
                    
                    const now = Date.now();
                    
                    if (eyeDistance < 0.01 && now - lastBlinkTime > 300) {
                        blinkCount++;
                        lastBlinkTime = now;
                        console.log('✅ 检测到眨眼! 总次数:', blinkCount);
                    }
                    
                    const elapsedMinutes = (now - focusStartTime) / 60000;
                    const blinkRate = elapsedMinutes > 0 ? blinkCount / elapsedMinutes : 0;
                    
                    let score = 100;
                    score -= Math.min(40, Math.abs(yaw) * 1.2);
                    score -= Math.min(30, Math.abs(pitch) * 0.8);
                    if (faceArea > 0.5) score -= 15;
                    if (faceArea < 0.15) score -= 10;
                    score = Math.max(0, Math.min(100, Math.floor(score)));
                    
                    detectionData = {
                        attentionScore: score,
                        isFaceDetected: true,
                        headYaw: yaw,
                        headPitch: pitch,
                        faceArea: faceArea,
                        blinkRate: blinkRate,
                        focusDuration: Math.floor((now - focusStartTime) / 1000)
                    };
                    
                    // ===== 云朵提醒（优先级：无人脸 > 太近 > 太远 > 转头）=====
                    let currentProblem = null;
                    let currentMessage = '';
                    
                    // 1. 距离过近
                    if (faceArea > 0.5) {
                        currentProblem = 'too_close';
                        currentMessage = '📏 离远一点~';
                    }
                    // 2. 距离过远
                    else if (faceArea < 0.08 && faceArea > 0) {
                        currentProblem = 'too_far';
                        currentMessage = '🔍 靠近一点嘛';
                    }
                    // 3. 视线离开屏幕
                    else if (Math.abs(yaw) > 25 || Math.abs(pitch) > 20) {
                        currentProblem = 'distracted';
                        currentMessage = '👀 看这里！';
                    }
                    // 4. 正常，没有提示
                    else {
                        currentProblem = null;
                    }
                    
                    // 更新提示显示
                    if (currentProblem) {
                        if (currentTipType !== currentProblem) {
                            showCloudTip(currentMessage, currentProblem, true);
                        }
                    } else {
                        if (currentTipType !== null) {
                            hideCloudTip();
                        }
                    }
                    
                } else {
                    detectionData = {
                        ...detectionData,
                        isFaceDetected: false,
                        attentionScore: 0
                    };
                    
                    // 检测不到人脸时提醒（最高优先级）
                    if (currentTipType !== 'no_face') {
                        showCloudTip('😊 请正对摄像头', 'no_face', true);
                    }
                }
                
                updateBallScore();
                if (isPanelOpen) updatePanelData();
            }
            animationId = requestAnimationFrame(detect);
        }
        detect();
    }
})();
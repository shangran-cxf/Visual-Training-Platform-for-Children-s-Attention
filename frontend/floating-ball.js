/**
 * 可移动小球 + 专注力检测面板 + 卡通云朵提示
 * EAR算法版：使用眼睛纵横比检测眨眼，更准确稳定
 * 改进特性：多级窗口频率计算 + 自适应平滑 + 实时变化检测
 */

(function () {
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
    focusDuration: 0,
  };

  // ========== EAR 眨眼检测变量 ==========
  // 眼睛关键点索引 (MediaPipe 468点模型)
  const LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144];
  const RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380];

  let earValue = 1.0; // 当前EAR值
  let isEyeClosed = false; // 当前眼睛状态
  let totalBlinks = 0; // 总眨眼次数
  let blinkTimes = []; // 眨眼时间戳

  // 多级窗口配置
  const WINDOWS = [
    { name: 'short', duration: 4000 }, // 4秒快速窗口
    { name: 'medium', duration: 8000 }, // 8秒平衡窗口
    { name: 'long', duration: 30000 }, // 30秒稳定窗口
  ];

  let blinkRateHistory = []; // 频率历史记录
  const HISTORY_SIZE = 20; // 历史记录长度

  // EAR阈值
  const EAR_THRESHOLD = 0.2;
  const EAR_RECOVER_THRESHOLD = 0.28;
  const MIN_BLINK_INTERVAL = 200; // 最小眨眼间隔(ms)

  // 眨眼基线相关
  let baselineBlinkRate = null;
  let baselineSamples = [];
  let isBaselineCollecting = true;
  let baselineStartTime = null;
  const BASELINE_DURATION = 5000; // 缩短到5秒

  // 眨眼状态（用于显示）
  let blinkTrend = 'up'; // up, down
  let blinkChangeIntensity = 0; // 0-1，变化强度

  // 专注计时变量
  let focusStartTime = null;
  let totalFocusDuration = 0;
  // 当前显示的云朵
  let currentCloud = null;
  let currentTipType = null;

  // 面板状态
  let isPanelOpen = false;
  let floatingBall = null;
  let panel = null;
  let panelUpdateInterval = null;
  let panelCloseTimer = null;

  // ========== 拖拽联动变量 ==========
  let activeDragElement = null;
  let dragStartX = 0,
    dragStartY = 0;
  let dragStartLeft = 0,
    dragStartTop = 0;
  let dragStartPanelLeft = 0,
    dragStartPanelTop = 0;
  let dragStartCloudLeft = 0,
    dragStartCloudTop = 0;

  // ========== 统一距离判断函数 ==========
  function getDistanceStatus(faceArea) {
    if (faceArea > 0.45) return 'too_close';
    if (faceArea < 0.05) return 'too_far';
    return 'normal';
  }

  // ========== EAR 眨眼检测核心函数 ==========
  // 计算眼睛纵横比 (EAR)
  function calculateEAR(landmarks, eyeIndices, frameWidth, frameHeight) {
    const points = eyeIndices.map((idx) => ({
      x: landmarks[idx].x * frameWidth,
      y: landmarks[idx].y * frameHeight,
    }));

    // 垂直距离 A (p1-p5) 和 B (p2-p4)
    const A = Math.hypot(points[1].x - points[5].x, points[1].y - points[5].y);
    const B = Math.hypot(points[2].x - points[4].x, points[2].y - points[4].y);
    // 水平距离 C (p0-p3)
    const C = Math.hypot(points[0].x - points[3].x, points[0].y - points[3].y);

    return (A + B) / (2.0 * C);
  }

  // 多级窗口自适应融合眨眼频率计算
  function calculateBlinkRate() {
    const now = Date.now();

    // 计算各级窗口频率
    const shortWindow = 4000; // 4秒
    const mediumWindow = 8000; // 8秒
    const longWindow = 30000; // 30秒

    const shortBlinks = blinkTimes.filter((t) => t >= now - shortWindow);
    const mediumBlinks = blinkTimes.filter((t) => t >= now - mediumWindow);
    const longBlinks = blinkTimes.filter((t) => t >= now - longWindow);

    const shortRate = shortBlinks.length > 0 ? (shortBlinks.length / shortWindow) * 1000 * 60 : 0;
    const mediumRate = mediumBlinks.length > 0 ? (mediumBlinks.length / mediumWindow) * 1000 * 60 : 0;
    const longRate = longBlinks.length > 0 ? (longBlinks.length / longWindow) * 1000 * 60 : 0;

    // 计算变化强度（用于自适应融合）
    let changeIntensity = 0;
    if (blinkRateHistory.length >= 3) {
      const recent = blinkRateHistory.slice(-3);
      const diffs = [Math.abs(recent[1] - recent[0]), Math.abs(recent[2] - recent[1])];
      const avgDiff = (diffs[0] + diffs[1]) / 2;
      changeIntensity = Math.min(1, avgDiff / 5); // 归一化到0-1
    }

    // 自适应融合权重
    // 变化大时偏向短窗口（快响应），变化小时偏向长窗口（稳定）
    let shortWeight, longWeight;
    if (changeIntensity > 0.5) {
      // 剧烈变化：短窗口60%，长窗口30%
      shortWeight = 0.6;
      longWeight = 0.3;
    } else if (changeIntensity > 0.2) {
      // 中等变化：短窗口40%，长窗口40%
      shortWeight = 0.4;
      longWeight = 0.4;
    } else {
      // 小变化：短窗口20%，长窗口70%
      shortWeight = 0.2;
      longWeight = 0.7;
    }
    const mediumWeight = 1 - shortWeight - longWeight;

    // 融合三个窗口的频率
    let fusedRate = shortRate * shortWeight + mediumRate * mediumWeight + longRate * longWeight;

    // 获取当前频率
    let currentBlinkRate = detectionData.blinkRate || 0;

    // 使用平滑滤波进一步稳定输出
    if (currentBlinkRate === 0) {
      currentBlinkRate = fusedRate;
    } else {
      currentBlinkRate = currentBlinkRate * 0.8 + fusedRate * 0.2;
    }

    // 更新历史用于趋势检测
    blinkRateHistory.push(currentBlinkRate);
    if (blinkRateHistory.length > HISTORY_SIZE) {
      blinkRateHistory.shift();
    }

    // 检测趋势和变化强度
    detectTrend();
    detectChangeIntensity();

    // 返回整数，至少显示1
    const result = Math.round(currentBlinkRate);
    return result > 0 ? result : 1;
  }

  // 检测趋势
  function detectTrend() {
    if (blinkRateHistory.length < 3) {
      return; // 不更新趋势，保持之前的状态
    }

    const recent = blinkRateHistory.slice(-3);
    const diffs = [recent[1] - recent[0], recent[2] - recent[1]];
    const avgDiff = diffs.reduce((a, b) => a + b, 0) / diffs.length;

    // 只有明显变化才更新趋势
    if (avgDiff > 0.3) {
      blinkTrend = 'up';
    } else if (avgDiff < -0.3) {
      blinkTrend = 'down';
    }
    // 小变化不更新趋势，保持之前的状态
  }

  // 检测变化强度
  function detectChangeIntensity() {
    if (blinkRateHistory.length < 5) {
      blinkChangeIntensity = 0;
      return;
    }

    const recent = blinkRateHistory.slice(-5);
    const maxDiff = Math.max(...recent) - Math.min(...recent);
    const avg = recent.reduce((a, b) => a + b, 0) / recent.length;

    blinkChangeIntensity = Math.min(1.0, maxDiff / (avg + 0.1));
  }

  // 更新EAR值并检测眨眼
  function updateEARAndDetectBlink(landmarks, frameWidth, frameHeight) {
    if (!landmarks || frameWidth === 0 || frameHeight === 0) return;

    try {
      // 计算左右眼EAR
      const leftEAR = calculateEAR(landmarks, LEFT_EYE_INDICES, frameWidth, frameHeight);
      const rightEAR = calculateEAR(landmarks, RIGHT_EYE_INDICES, frameWidth, frameHeight);
      earValue = (leftEAR + rightEAR) / 2;

      const now = Date.now();
      const currentIsClosed = earValue < EAR_THRESHOLD;

      // 检测闭眼->睁眼的转换（完成一次眨眼）
      if (isEyeClosed && !currentIsClosed) {
        isEyeClosed = false;

        // 检查最小间隔，过滤快速连续眨眼
        if (blinkTimes.length === 0 || now - blinkTimes[blinkTimes.length - 1] >= MIN_BLINK_INTERVAL) {
          totalBlinks++;
          blinkTimes.push(now);
          console.log(`👁️ 眨眼检测！总次数：${totalBlinks}, EAR: ${earValue.toFixed(3)}`);
        }
      }

      // 更新闭眼状态
      if (currentIsClosed) {
        isEyeClosed = true;
      }

      // 清理旧记录
      const oldestAllowed = now - WINDOWS[WINDOWS.length - 1].duration;
      while (blinkTimes.length > 0 && blinkTimes[0] < oldestAllowed) {
        blinkTimes.shift();
      }

      // 调试：输出EAR值
      // console.log(`EAR: ${earValue.toFixed(3)}, 闭眼: ${currentIsClosed}`);
    } catch (err) {
      console.warn('EAR计算失败:', err);
    }
  }

  // 更新眨眼频率和状态（每帧调用）
  function updateBlinkRate() {
    // 计算眨眼频率
    const currentRate = calculateBlinkRate();
    detectionData.blinkRate = currentRate;

    // 快速建立基线：直接使用默认值，跳过长收集阶段
    if (isBaselineCollecting) {
      // 短暂等待1秒后就直接开始
      if (Date.now() - baselineStartTime > 1000) {
        isBaselineCollecting = false;
        baselineBlinkRate = 12; // 默认眨眼频率12次/分
        // console.log(`📊 眨眼基线快速建立: ${baselineBlinkRate} 次/分`);
      }
    }

    return currentRate;
  }

  // 获取眨眼状态描述
  function getBlinkStatus() {
    if (isBaselineCollecting) {
      return { text: '收集中', color: '#888', advice: '正在建立个人基线' };
    }
    if (!baselineBlinkRate || baselineBlinkRate === 0) {
      return { text: '正常', color: '#4CAF50', advice: '状态良好' };
    }

    const ratio = detectionData.blinkRate / baselineBlinkRate;

    if (ratio > 1.5) {
      return { text: '偏高', color: '#FF9800', advice: '可能有点疲劳了' };
    } else if (ratio > 1.2) {
      return { text: '稍高', color: '#FFC107', advice: '注意休息' };
    } else if (ratio < 0.7) {
      return { text: '偏低', color: '#2196F3', advice: '非常专注' };
    } else {
      return { text: '正常', color: '#4CAF50', advice: '状态良好' };
    }
  }

  // ========== 初始化 ==========
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

  // ========== 云朵提示 ==========
  function showCloudTip(message, type, persistent = false) {
    if (currentTipType === type && currentCloud) return;

    if (currentCloud) {
      currentCloud.remove();
      currentCloud = null;
    }

    const cloud = document.createElement('div');
    cloud.id = 'cloud-tip';
    cloud.innerHTML = `
            <div style="
                position: relative;
                background: #fff;
                border-radius: 14px;
                padding: 10px 18px;
                text-align: center;
                font-family: system-ui, -apple-system, sans-serif;
                font-size: 13px;
                color: #555;
                box-shadow: 0 4px 16px rgba(0,0,0,0.1);
                animation: cloudFloatIn 0.3s ease-out;
            ">
                ${message}
                <div style="
                    position: absolute;
                    bottom: -7px;
                    left: 24px;
                    width: 14px;
                    height: 7px;
                    background: #fff;
                    clip-path: polygon(0 0, 100% 0, 50% 100%);
                "></div>
            </div>
        `;

    const style = document.getElementById('cloud-style');
    if (!style) {
      const newStyle = document.createElement('style');
      newStyle.id = 'cloud-style';
      newStyle.textContent = `
                @keyframes cloudFloatIn {
                    0% { opacity: 0; transform: translateY(8px) scale(0.95); }
                    100% { opacity: 1; transform: translateY(0) scale(1); }
                }
                @keyframes cloudPulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.04); }
                }
            `;
      document.head.appendChild(newStyle);
    }

    const ballRect = floatingBall.getBoundingClientRect();
    let top = ballRect.top - 52;
    let left = ballRect.left + ballRect.width / 2 - 60;

    if (top < 10) top = ballRect.bottom + 10;
    if (left < 10) left = 10;
    if (left + 140 > window.innerWidth) left = window.innerWidth - 150;

    Object.assign(cloud.style, {
      position: 'fixed',
      top: top + 'px',
      left: left + 'px',
      zIndex: '10000',
      cursor: 'move',
      pointerEvents: 'auto',
    });

    if (persistent) {
      cloud.style.animation = 'cloudFloatIn 0.3s ease-out, cloudPulse 1.5s ease-in-out 0.3s infinite';
    }

    document.body.appendChild(cloud);
    currentCloud = cloud;
    currentTipType = type;

    makeDraggable(cloud, 'cloud');
  }

  function hideCloudTip() {
    if (currentCloud) {
      currentCloud.remove();
      currentCloud = null;
      currentTipType = null;
    }
  }

  // ========== 拖拽联动核心函数 ==========
  function makeDraggable(element, type = 'ball') {
    element.addEventListener('mousedown', (e) => {
      if (e.target !== element && !element.contains(e.target)) return;

      activeDragElement = type;
      dragStartX = e.clientX;
      dragStartY = e.clientY;

      dragStartLeft = parseFloat(floatingBall.style.left) || window.innerWidth - 70;
      dragStartTop = parseFloat(floatingBall.style.top) || 100;

      if (panel && isPanelOpen) {
        dragStartPanelLeft = parseFloat(panel.style.left) || window.innerWidth - 296;
        dragStartPanelTop = parseFloat(panel.style.top) || 100;
      }

      if (currentCloud) {
        dragStartCloudLeft = parseFloat(currentCloud.style.left) || window.innerWidth - 160;
        dragStartCloudTop = parseFloat(currentCloud.style.top) || 35;
      }

      element.style.cursor = 'grabbing';
      e.preventDefault();
    });

    element.addEventListener(
      'touchstart',
      (e) => {
        if (e.target !== element && !element.contains(e.target)) return;
        if (e.touches.length !== 1) return; // 只处理单指

        activeDragElement = type;
        var touch = e.touches[0];
        dragStartX = touch.clientX;
        dragStartY = touch.clientY;

        dragStartLeft = parseFloat(floatingBall.style.left) || window.innerWidth - 70;
        dragStartTop = parseFloat(floatingBall.style.top) || 100;

        if (panel && isPanelOpen) {
          dragStartPanelLeft = parseFloat(panel.style.left) || window.innerWidth - 296;
          dragStartPanelTop = parseFloat(panel.style.top) || 100;
        }

        if (currentCloud) {
          dragStartCloudLeft = parseFloat(currentCloud.style.left) || window.innerWidth - 160;
          dragStartCloudTop = parseFloat(currentCloud.style.top) || 35;
        }

        e.preventDefault(); // 防止页面滚动
      },
      { passive: false },
    );
  }

  document.addEventListener('mousemove', (e) => {
    if (!activeDragElement) return;

    const deltaX = e.clientX - dragStartX;
    const deltaY = e.clientY - dragStartY;

    let newLeft = dragStartLeft + deltaX;
    let newTop = dragStartTop + deltaY;

    newLeft = Math.max(0, Math.min(window.innerWidth - 50, newLeft));
    newTop = Math.max(0, Math.min(window.innerHeight - 50, newTop));

    floatingBall.style.left = newLeft + 'px';
    floatingBall.style.top = newTop + 'px';
    floatingBall.style.right = 'auto';
    floatingBall.style.bottom = 'auto';

    if (panel && isPanelOpen) {
      let panelNewLeft = dragStartPanelLeft + deltaX;
      let panelNewTop = dragStartPanelTop + deltaY;

      panelNewLeft = Math.max(0, Math.min(window.innerWidth - 284, panelNewLeft));
      panelNewTop = Math.max(0, Math.min(window.innerHeight - 430, panelNewTop));

      panel.style.left = panelNewLeft + 'px';
      panel.style.top = panelNewTop + 'px';
      panel.style.right = 'auto';
      panel.style.bottom = 'auto';
    }

    if (currentCloud) {
      let cloudNewLeft = dragStartCloudLeft + deltaX;
      let cloudNewTop = dragStartCloudTop + deltaY;

      cloudNewLeft = Math.max(0, Math.min(window.innerWidth - 150, cloudNewLeft));
      cloudNewTop = Math.max(0, Math.min(window.innerHeight - 100, cloudNewTop));

      currentCloud.style.left = cloudNewLeft + 'px';
      currentCloud.style.top = cloudNewTop + 'px';
      currentCloud.style.right = 'auto';
      currentCloud.style.bottom = 'auto';
    }
  });

  document.addEventListener(
    'touchmove',
    (e) => {
      if (!activeDragElement) return;
      if (e.touches.length !== 1) return;

      var touch = e.touches[0];
      var deltaX = touch.clientX - dragStartX;
      var deltaY = touch.clientY - dragStartY;

      var newLeft = dragStartLeft + deltaX;
      var newTop = dragStartTop + deltaY;

      newLeft = Math.max(0, Math.min(window.innerWidth - 50, newLeft));
      newTop = Math.max(0, Math.min(window.innerHeight - 50, newTop));

      floatingBall.style.left = newLeft + 'px';
      floatingBall.style.top = newTop + 'px';
      floatingBall.style.right = 'auto';
      floatingBall.style.bottom = 'auto';

      if (panel && isPanelOpen) {
        var panelNewLeft = dragStartPanelLeft + deltaX;
        var panelNewTop = dragStartPanelTop + deltaY;
        panelNewLeft = Math.max(0, Math.min(window.innerWidth - 284, panelNewLeft));
        panelNewTop = Math.max(0, Math.min(window.innerHeight - 430, panelNewTop));
        panel.style.left = panelNewLeft + 'px';
        panel.style.top = panelNewTop + 'px';
        panel.style.right = 'auto';
        panel.style.bottom = 'auto';
      }

      if (currentCloud) {
        var cloudNewLeft = dragStartCloudLeft + deltaX;
        var cloudNewTop = dragStartCloudTop + deltaY;
        cloudNewLeft = Math.max(0, Math.min(window.innerWidth - 150, cloudNewLeft));
        cloudNewTop = Math.max(0, Math.min(window.innerHeight - 100, cloudNewTop));
        currentCloud.style.left = cloudNewLeft + 'px';
        currentCloud.style.top = cloudNewTop + 'px';
        currentCloud.style.right = 'auto';
        currentCloud.style.bottom = 'auto';
      }
    },
    { passive: false },
  );

  document.addEventListener('mouseup', () => {
    if (activeDragElement) {
      activeDragElement = null;
      if (floatingBall) floatingBall.style.cursor = 'move';
    }
  });

  document.addEventListener('touchend', (e) => {
    if (activeDragElement && e.touches.length === 0) {
      activeDragElement = null;
      if (floatingBall) floatingBall.style.cursor = '';
    }
  });

  document.addEventListener('touchcancel', () => {
    if (activeDragElement) {
      activeDragElement = null;
      if (floatingBall) floatingBall.style.cursor = '';
    }
  });

  // ========== 小球创建 ==========
  function createFloatingBall() {
    // Load rounded display font
    if (!document.getElementById('creature-font')) {
      var fontLink = document.createElement('link');
      fontLink.id = 'creature-font';
      fontLink.rel = 'stylesheet';
      fontLink.href = 'https://fonts.googleapis.com/css2?family=Fredoka:wght@500;700&display=swap';
      document.head.appendChild(fontLink);
    }

    floatingBall = document.createElement('div');
    floatingBall.id = 'floating-attention-ball';
    floatingBall.innerHTML = `
            <div id="ball-wrapper" style="
                position: relative;
                width: 82px;
                height: 82px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
            ">
                <div id="ball-light-pool" style="
                    position: absolute;
                    bottom: -1px;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 38px;
                    height: 10px;
                    background: radial-gradient(ellipse at center, rgba(255,184,128,0.45) 0%, transparent 70%);
                    border-radius: 50%;
                    animation: lightPoolPulse 2.2s ease-in-out infinite;
                    pointer-events: none;
                    transition: background 0.5s ease;
                "></div>
                <div class="creature-sparkle" style="
                    position: absolute;
                    width: 3px; height: 3px;
                    background: #FFD54F;
                    border-radius: 50%;
                    top: 50%; left: 50%;
                    animation: sparkle1 3s ease-in-out infinite;
                    pointer-events: none;
                    box-shadow: 0 0 4px #FFD54F;
                "></div>
                <div class="creature-sparkle" style="
                    position: absolute;
                    width: 2.5px; height: 2.5px;
                    background: #FFFFFF;
                    border-radius: 50%;
                    top: 50%; left: 50%;
                    animation: sparkle2 3.4s ease-in-out 0.5s infinite;
                    pointer-events: none;
                    box-shadow: 0 0 3px #FFFFFF;
                "></div>
                <div class="creature-sparkle" style="
                    position: absolute;
                    width: 3.5px; height: 3.5px;
                    background: #FFECB3;
                    border-radius: 50%;
                    top: 50%; left: 50%;
                    animation: sparkle3 2.8s ease-in-out 1.2s infinite;
                    pointer-events: none;
                    box-shadow: 0 0 5px #FFECB3;
                "></div>
                <div class="creature-sparkle" style="
                    position: absolute;
                    width: 2px; height: 2px;
                    background: #FFD54F;
                    border-radius: 50%;
                    top: 50%; left: 50%;
                    animation: sparkle4 3.6s ease-in-out 0.8s infinite;
                    pointer-events: none;
                    box-shadow: 0 0 3px #FFD54F;
                "></div>
                <div id="ball-body" style="
                    width: 68px;
                    height: 68px;
                    border-radius: 46% 50% 48% 52% / 48% 50% 52% 46%;
                    background: radial-gradient(circle at 38% 30%, #FFF5F0 0%, #FFE0D0 18%, #F0B8A0 50%, #D89078 100%);
                    box-shadow:
                        0 6px 24px rgba(200,140,110,0.30),
                        inset 0 -8px 16px rgba(180,120,100,0.15);
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                    transition: background 0.6s ease, box-shadow 0.6s ease, border-radius 0.6s ease;
                    animation: creatureFloat 3s ease-in-out infinite, creatureBreathe 4s ease-in-out infinite;
                ">
                    <div id="ball-highlight" style="
                        position: absolute;
                        top: 8px;
                        left: 12px;
                        width: 22px;
                        height: 11px;
                        background: rgba(255,255,255,0.45);
                        border-radius: 50%;
                        transform: rotate(-20deg);
                        pointer-events: none;
                    "></div>
                    <div id="ball-score-text" style="
                        font-family: 'Fredoka', system-ui, sans-serif;
                        font-size: 17px;
                        font-weight: 700;
                        color: rgba(255,255,255,0.92);
                        text-shadow: 0 1px 2px rgba(0,0,0,0.08);
                        line-height: 1;
                        margin-bottom: 0px;
                        z-index: 1;
                        letter-spacing: -0.5px;
                    ">0</div>
                    <div id="ball-face" style="display: flex; flex-direction: column; align-items: center; z-index: 1;">
                        <div id="ball-eyes" style="
                            display: flex; gap: 13px; margin-bottom: 3px;
                            animation: creatureBlink 4.5s ease-in-out infinite;
                        ">
                            <div class="creature-eye" style="
                                width: 12px; height: 13px; background: #fff;
                                border-radius: 50%; position: relative; overflow: hidden;
                                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                            ">
                                <div class="eye-iris" style="
                                    width: 8px; height: 9px; background: #4A3728;
                                    border-radius: 50%; position: absolute;
                                    bottom: 0; left: 50%; transform: translateX(-50%);
                                ">
                                    <div class="eye-shine" style="
                                        width: 3px; height: 3px; background: #fff;
                                        border-radius: 50%; position: absolute;
                                        top: 1px; right: 1px;
                                    "></div>
                                    <div style="
                                        width: 1.5px; height: 1.5px; background: #fff;
                                        border-radius: 50%; position: absolute;
                                        bottom: 1px; left: 1px;
                                    "></div>
                                </div>
                            </div>
                            <div class="creature-eye" style="
                                width: 12px; height: 13px; background: #fff;
                                border-radius: 50%; position: relative; overflow: hidden;
                                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                            ">
                                <div class="eye-iris" style="
                                    width: 8px; height: 9px; background: #4A3728;
                                    border-radius: 50%; position: absolute;
                                    bottom: 0; left: 50%; transform: translateX(-50%);
                                ">
                                    <div class="eye-shine" style="
                                        width: 3px; height: 3px; background: #fff;
                                        border-radius: 50%; position: absolute;
                                        top: 1px; right: 1px;
                                    "></div>
                                    <div style="
                                        width: 1.5px; height: 1.5px; background: #fff;
                                        border-radius: 50%; position: absolute;
                                        bottom: 1px; left: 1px;
                                    "></div>
                                </div>
                            </div>
                        </div>
                        <div id="ball-blush" style="display: flex; gap: 20px; margin-bottom: 1px;">
                            <div class="blush-dot" style="
                                width: 7px; height: 4px; background: rgba(255,160,140,0.50);
                                border-radius: 50%; filter: blur(1.5px);
                            "></div>
                            <div class="blush-dot" style="
                                width: 7px; height: 4px; background: rgba(255,160,140,0.50);
                                border-radius: 50%; filter: blur(1.5px);
                            "></div>
                        </div>
                        <div id="ball-mouth" style="
                            width: 10px; height: 5px;
                            border-radius: 0 0 5px 5px;
                            border: 1.5px solid rgba(74,55,40,0.45);
                            border-top: none;
                            transition: all 0.4s ease;
                        "></div>
                    </div>
                </div>
            </div>
        `;

    var style = document.createElement('style');
    style.id = 'creature-animations';
    style.textContent = `
            @keyframes creatureFloat {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-3px); }
            }
            @keyframes creatureBreathe {
                0%, 100% {
                    transform: scale(1);
                    border-radius: 46% 50% 48% 52% / 48% 50% 52% 46%;
                }
                50% {
                    transform: scale(1.04);
                    border-radius: 50% 46% 52% 48% / 52% 48% 46% 50%;
                }
            }
            @keyframes lightPoolPulse {
                0%, 100% { transform: translateX(-50%) scale(1); opacity: 0.65; }
                50% { transform: translateX(-50%) scale(1.35); opacity: 0.35; }
            }
            @keyframes creatureBlink {
                0%, 44%, 48%, 100% { transform: scaleY(1); }
                46% { transform: scaleY(0.06); }
            }
            @keyframes sparkle1 {
                0%, 100% { transform: translate(0, 0) scale(0); opacity: 0; }
                25% { transform: translate(22px, -28px) scale(1); opacity: 1; }
                55% { transform: translate(36px, -16px) scale(0.5); opacity: 0.5; }
                75% { transform: translate(42px, -30px) scale(0); opacity: 0; }
            }
            @keyframes sparkle2 {
                0%, 100% { transform: translate(0, 0) scale(0); opacity: 0; }
                20% { transform: translate(-20px, -24px) scale(1); opacity: 0.9; }
                50% { transform: translate(-34px, -10px) scale(0.4); opacity: 0.3; }
                70% { transform: translate(-38px, -26px) scale(0); opacity: 0; }
            }
            @keyframes sparkle3 {
                0%, 100% { transform: translate(0, 0) scale(0); opacity: 0; }
                30% { transform: translate(26px, 12px) scale(0.9); opacity: 0.8; }
                60% { transform: translate(38px, -8px) scale(0.3); opacity: 0.2; }
                80% { transform: translate(44px, 16px) scale(0); opacity: 0; }
            }
            @keyframes sparkle4 {
                0%, 100% { transform: translate(0, 0) scale(0); opacity: 0; }
                22% { transform: translate(-24px, 14px) scale(0.7); opacity: 0.7; }
                48% { transform: translate(-36px, -14px) scale(1); opacity: 0.9; }
                68% { transform: translate(-42px, 18px) scale(0); opacity: 0; }
            }
        `;
    document.head.appendChild(style);

    Object.assign(floatingBall.style, {
      position: 'fixed',
      top: '100px',
      right: '24px',
      zIndex: '9998',
      cursor: 'move',
      userSelect: 'none',
    });

    floatingBall.addEventListener('click', (e) => {
      e.stopPropagation();
      togglePanel();
    });

    makeDraggable(floatingBall, 'ball');
    document.body.appendChild(floatingBall);
  }

  // ========== 面板 ==========
  function createPanel() {
    panel = document.createElement('div');
    panel.id = 'attention-panel';
    panel.innerHTML = `
            <div style="
                background: #FFFFFF;
                border-radius: 16px;
                width: 284px;
                box-shadow: 0 8px 40px rgba(0,0,0,0.10), 0 1px 3px rgba(0,0,0,0.06);
                overflow: hidden;
                font-family: system-ui, -apple-system, sans-serif;
                border: 1px solid rgba(0,0,0,0.06);
            ">
                <div id="panel-header-bg" style="
                    padding: 14px 18px;
                    background: linear-gradient(135deg, #D89078, #C07860);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    cursor: move;
                    transition: background 0.5s ease;
                ">
                    <span style="font-size: 13px; font-weight: 600; color: #fff; letter-spacing: 0.5px;">专注力检测</span>
                    <button id="close-panel" style="
                        background: rgba(255,255,255,0.18);
                        border: none;
                        color: #fff;
                        font-size: 13px;
                        cursor: pointer;
                        width: 24px;
                        height: 24px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        line-height: 1;
                        transition: background 0.2s;
                    ">✕</button>
                </div>

                <div style="padding: 16px 18px 18px;">
                    <div style="text-align: center; margin-bottom: 14px;">
                        <div id="panel-gauge" style="
                            width: 84px;
                            height: 84px;
                            border-radius: 50%;
                            margin: 0 auto 8px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            transition: background 0.5s ease;
                            background: #D89078;
                            box-shadow: 0 0 0 4px rgba(216,144,120,0.15);
                        ">
                            <div style="text-align: center;">
                                <div id="panel-score-big" style="
                                    font-family: 'Fredoka', system-ui, sans-serif;
                                    font-size: 28px;
                                    font-weight: 700;
                                    color: #fff;
                                    line-height: 1;
                                    letter-spacing: -1px;
                                ">--</div>
                                <div style="font-size: 10px; color: rgba(255,255,255,0.75); margin-top: 2px;">专注度</div>
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; flex-direction: column; gap: 5px;">
                        <div style="
                            display: flex; justify-content: space-between; align-items: center;
                            padding: 8px 12px; background: #FAFAFA; border-radius: 8px;
                        ">
                            <span style="color: #999; font-size: 11px;">人脸</span>
                            <span id="panel-face-status" style="font-size: 11px; font-weight: 500;">--</span>
                        </div>
                        <div style="
                            display: flex; justify-content: space-between; align-items: center;
                            padding: 8px 12px; background: #FAFAFA; border-radius: 8px;
                        ">
                            <span style="color: #999; font-size: 11px;">头部转动</span>
                            <span id="panel-head-angle" style="font-size: 11px; font-weight: 500;">--</span>
                        </div>
                        <div style="
                            display: flex; justify-content: space-between; align-items: center;
                            padding: 8px 12px; background: #FAFAFA; border-radius: 8px;
                        ">
                            <span style="color: #999; font-size: 11px;">屏幕距离</span>
                            <span id="panel-distance" style="font-size: 11px; font-weight: 500;">--</span>
                        </div>
                        <div style="
                            display: flex; justify-content: space-between; align-items: center;
                            padding: 8px 12px; background: #FAFAFA; border-radius: 8px;
                        ">
                            <span style="color: #999; font-size: 11px;">眨眼频率</span>
                            <span id="panel-blink-rate" style="font-size: 11px; font-weight: 500;">--</span>
                        </div>
                        <div style="
                            display: flex; justify-content: space-between; align-items: center;
                            padding: 8px 12px; background: #FAFAFA; border-radius: 8px;
                        ">
                            <span style="color: #999; font-size: 11px;">专注时长</span>
                            <span id="panel-focus-time" style="font-size: 11px; font-weight: 500;">--</span>
                        </div>
                    </div>

                    <button id="panel-close-btn" style="
                        width: 100%;
                        margin-top: 12px;
                        background: #F5F5F5;
                        border: none;
                        color: #999;
                        padding: 8px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 12px;
                        transition: background 0.2s;
                    ">收起面板</button>
                </div>
            </div>
        `;

    Object.assign(panel.style, {
      position: 'fixed',
      bottom: '170px',
      right: '20px',
      zIndex: '9999',
      display: 'none',
      opacity: '0',
      transform: 'translateY(8px)',
      transition: 'opacity 0.2s ease-out, transform 0.2s ease-out',
      pointerEvents: 'none',
      cursor: 'move',
    });

    panel.querySelector('#close-panel').addEventListener('click', () => closePanel());
    panel.querySelector('#panel-close-btn').addEventListener('click', () => closePanel());

    makeDraggable(panel, 'panel');
    document.body.appendChild(panel);
  }

  function togglePanel() {
    if (isPanelOpen) closePanel();
    else openPanel();
  }

  function openPanel() {
    if (!panel) createPanel();

    // 清理关闭动画残留的 transitionend 监听器和超时
    if (panelCloseTimer) {
      clearTimeout(panelCloseTimer);
      panelCloseTimer = null;
    }
    // 移除所有残留的 transitionend 监听器（克隆节点方式最可靠）
    panel.style.transition = 'none';
    panel.style.opacity = '0';
    panel.style.transform = 'translateY(8px)';

    var ballRect = floatingBall.getBoundingClientRect();
    var panelLeft = ballRect.left - 296;
    var panelTop = ballRect.top;

    if (panelLeft < 10) panelLeft = ballRect.right + 10;
    if (panelTop + 430 > window.innerHeight) panelTop = window.innerHeight - 440;
    if (panelTop < 10) panelTop = 10;

    panel.style.left = panelLeft + 'px';
    panel.style.top = panelTop + 'px';
    panel.style.right = 'auto';
    panel.style.bottom = 'auto';
    panel.style.display = 'block';

    requestAnimationFrame(function () {
      panel.style.transition = 'opacity 0.2s ease-out, transform 0.2s ease-out';
      requestAnimationFrame(function () {
        panel.style.opacity = '1';
        panel.style.transform = 'translateY(0)';
        panel.style.pointerEvents = 'auto';
      });
    });

    isPanelOpen = true;
    updatePanelData();
    if (panelUpdateInterval) clearInterval(panelUpdateInterval);
    panelUpdateInterval = setInterval(updatePanelData, 500);
  }

  function closePanel() {
    if (!panel || !isPanelOpen) return;

    // 清理之前的 transitionend 监听器和超时
    if (panelCloseTimer) {
      clearTimeout(panelCloseTimer);
      panelCloseTimer = null;
    }

    panel.style.opacity = '0';
    panel.style.transform = 'translateY(8px)';
    panel.style.pointerEvents = 'none';

    var onTransitionEnd = function () {
      panel.style.display = 'none';
      panel.removeEventListener('transitionend', onTransitionEnd);
      panelCloseTimer = null;
    };
    panel.addEventListener('transitionend', onTransitionEnd);

    // 300ms 超时保底，防止 transitionend 不触发
    panelCloseTimer = setTimeout(function () {
      panel.style.display = 'none';
      panel.removeEventListener('transitionend', onTransitionEnd);
      panelCloseTimer = null;
    }, 300);

    isPanelOpen = false;
    if (panelUpdateInterval) {
      clearInterval(panelUpdateInterval);
      panelUpdateInterval = null;
    }
  }

  function updatePanelData() {
    if (!panel) return;

    var score = detectionData.attentionScore;

    // Colors by state (match creature palette)
    var headerGrad, gaugeBg, gaugeShadow;
    if (score >= 80) {
      headerGrad = 'linear-gradient(135deg, #D89078, #C07860)';
      gaugeBg = '#D89078';
      gaugeShadow = '0 0 0 4px rgba(216,144,120,0.15)';
    } else if (score >= 60) {
      headerGrad = 'linear-gradient(135deg, #B8A8D0, #A090C0)';
      gaugeBg = '#B8A8D0';
      gaugeShadow = '0 0 0 4px rgba(184,168,208,0.15)';
    } else {
      headerGrad = 'linear-gradient(135deg, #90A8B8, #7890A0)';
      gaugeBg = '#90A8B8';
      gaugeShadow = '0 0 0 4px rgba(144,168,184,0.15)';
    }

    var headerEl = panel.querySelector('#panel-header-bg');
    var gauge = panel.querySelector('#panel-gauge');
    var scoreBig = panel.querySelector('#panel-score-big');

    if (headerEl) headerEl.style.background = headerGrad;
    if (gauge) {
      gauge.style.background = gaugeBg;
      gauge.style.boxShadow = gaugeShadow;
    }
    if (scoreBig) scoreBig.textContent = score;

    // Face status
    var faceEl = panel.querySelector('#panel-face-status');
    if (faceEl) {
      faceEl.textContent = detectionData.isFaceDetected ? '已检测' : '未检测';
      faceEl.style.color = detectionData.isFaceDetected ? '#4CAF50' : '#EF5350';
    }

    // Head angle
    var headEl = panel.querySelector('#panel-head-angle');
    if (headEl) {
      if (detectionData.headYaw > 3) headEl.textContent = '右转 ' + Math.abs(detectionData.headYaw).toFixed(0) + '°';
      else if (detectionData.headYaw < -3)
        headEl.textContent = '左转 ' + Math.abs(detectionData.headYaw).toFixed(0) + '°';
      else headEl.textContent = '正对';
    }

    // Distance
    var distEl = panel.querySelector('#panel-distance');
    if (distEl && detectionData.isFaceDetected) {
      var status = getDistanceStatus(detectionData.faceArea);
      if (status === 'too_close') {
        distEl.textContent = '太近';
        distEl.style.color = '#FF9800';
      } else if (status === 'too_far') {
        distEl.textContent = '太远';
        distEl.style.color = '#2196F3';
      } else {
        distEl.textContent = '适中';
        distEl.style.color = '#4CAF50';
      }
    }

    // Blink rate
    var blinkEl = panel.querySelector('#panel-blink-rate');
    if (blinkEl) {
      if (isBaselineCollecting) {
        blinkEl.innerHTML = '收集中...';
        blinkEl.style.color = '#999';
      } else {
        var rate = Math.round(detectionData.blinkRate);
        var arrow = blinkTrend === 'up' ? '↑' : '↓';
        var color = '#4CAF50';
        if (rate < 5 || rate > 70) color = '#EF5350';
        else if (blinkChangeIntensity > 0.3) color = '#FF9800';
        blinkEl.innerHTML = '<span style="color:' + color + ';font-weight:600;">' + rate + arrow + '</span> 次/分';
      }
    }

    // Focus time
    var focusEl = panel.querySelector('#panel-focus-time');
    if (focusEl) {
      var min = Math.floor(detectionData.focusDuration / 60);
      var sec = detectionData.focusDuration % 60;
      focusEl.textContent = min.toString().padStart(2, '0') + ':' + sec.toString().padStart(2, '0');
    }
  }

  function updateBallScore() {
    var score = detectionData.attentionScore;
    var scoreEl = floatingBall?.querySelector('#ball-score-text');
    var body = floatingBall?.querySelector('#ball-body');
    var mouth = floatingBall?.querySelector('#ball-mouth');
    var lightPool = floatingBall?.querySelector('#ball-light-pool');
    var sparkles = floatingBall?.querySelectorAll('.creature-sparkle');

    if (scoreEl) scoreEl.textContent = score;

    if (body && mouth) {
      if (score >= 80) {
        // 专注 — 蜜桃色 + 金色光芒
        body.style.background =
          'radial-gradient(circle at 38% 30%, #FFF5F0 0%, #FFE0D0 18%, #F0B8A0 50%, #D89078 100%)';
        body.style.boxShadow = '0 6px 24px rgba(200,140,110,0.30), inset 0 -8px 16px rgba(180,120,100,0.15)';
        if (lightPool)
          lightPool.style.background = 'radial-gradient(ellipse at center, rgba(255,184,128,0.45) 0%, transparent 70%)';
        mouth.style.borderRadius = '0 0 5px 5px';
        mouth.style.border = '1.5px solid rgba(74,55,40,0.45)';
        mouth.style.borderTop = 'none';
        mouth.style.height = '5px';
        mouth.style.width = '10px';
        if (sparkles)
          sparkles.forEach(function (s) {
            s.style.opacity = '1';
          });
      } else if (score >= 60) {
        // 一般 — 薰衣草色
        body.style.background =
          'radial-gradient(circle at 38% 30%, #F8F6FF 0%, #E8E0F8 18%, #C8B8E0 50%, #A898C0 100%)';
        body.style.boxShadow = '0 6px 24px rgba(160,140,200,0.28), inset 0 -8px 16px rgba(140,120,180,0.12)';
        if (lightPool)
          lightPool.style.background = 'radial-gradient(ellipse at center, rgba(180,160,220,0.38) 0%, transparent 70%)';
        mouth.style.borderRadius = '0';
        mouth.style.border = 'none';
        mouth.style.borderTop = '1.5px solid rgba(74,55,40,0.40)';
        mouth.style.height = '0px';
        mouth.style.width = '8px';
        if (sparkles)
          sparkles.forEach(function (s) {
            s.style.opacity = '0.45';
          });
      } else {
        // 分心 — 鼠尾草蓝
        body.style.background =
          'radial-gradient(circle at 38% 30%, #F0F5F5 0%, #D8E8E8 18%, #B0C8D0 50%, #90A8B8 100%)';
        body.style.boxShadow = '0 6px 24px rgba(130,160,180,0.25), inset 0 -8px 16px rgba(110,140,160,0.10)';
        if (lightPool)
          lightPool.style.background = 'radial-gradient(ellipse at center, rgba(150,180,200,0.32) 0%, transparent 70%)';
        mouth.style.borderRadius = '5px 5px 0 0';
        mouth.style.border = '1.5px solid rgba(74,55,40,0.40)';
        mouth.style.borderBottom = 'none';
        mouth.style.height = '5px';
        mouth.style.width = '10px';
        if (sparkles)
          sparkles.forEach(function (s) {
            s.style.opacity = '0';
          });
      }
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
    videoElement.style.cssText =
      'position: fixed; top: 0; left: 0; width: 1px; height: 1px; opacity: 0; pointer-events: none;';
    document.body.appendChild(videoElement);

    videoElement.srcObject = stream;
    await videoElement.play();
    console.log('摄像头已启动');

    await waitForFilesetResolver();

    const vision = await FilesetResolver.forVisionTasks('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/wasm');
    faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
        delegate: 'GPU',
      },
      runningMode: 'VIDEO',
      numFaces: 1,
      minFaceDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
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
    // 初始化眨眼基线收集
    baselineStartTime = Date.now();
    isBaselineCollecting = true;
    baselineSamples = [];
    blinkTimes = [];
    totalBlinks = 0;
    console.log('📊 开始收集眨眼基线数据（30秒）...');

    function detect() {
      if (!isDetecting || !faceLandmarker || !videoElement) {
        animationId = requestAnimationFrame(detect);
        return;
      }
      if (videoElement.videoWidth && videoElement.videoHeight) {
        try {
          // 检查 faceLandmarker 是否有 detectForVideo 方法
          if (!faceLandmarker || typeof faceLandmarker.detectForVideo !== 'function') {
            animationId = requestAnimationFrame(detect);
            return;
          }

          const results = faceLandmarker.detectForVideo(videoElement, performance.now());

          if (results.faceLandmarks && results.faceLandmarks.length > 0) {
            const landmarks = results.faceLandmarks[0];
            const videoWidth = videoElement.videoWidth;
            const videoHeight = videoElement.videoHeight;

            // ===== EAR 眨眼检测 =====
            if (videoWidth > 0 && videoHeight > 0) {
              updateEARAndDetectBlink(landmarks, videoWidth, videoHeight);
            }

            // 更新眨眼频率
            updateBlinkRate();

            const leftCheek = landmarks[234];
            const rightCheek = landmarks[454];
            const nose = landmarks[1];
            const chin = landmarks[152];
            const forehead = landmarks[10];

            const faceWidth = Math.abs(leftCheek.x - rightCheek.x);
            const noseOffset = (nose.x - (leftCheek.x + rightCheek.x) / 2) / faceWidth;
            const yaw = -noseOffset * 60;

            const faceHeight = Math.abs(chin.y - forehead.y);
            const noseYOffset = (nose.y - (forehead.y + chin.y) / 2) / faceHeight;
            const pitch = noseYOffset * 45;

            const faceArea = faceWidth * faceHeight;

            let score = 100;
            score -= Math.min(40, Math.abs(yaw) * 1.2);
            score -= Math.min(30, Math.abs(pitch) * 0.8);
            if (faceArea > 0.45) score -= 15;
            if (faceArea < 0.15) score -= 10;
            score = Math.max(0, Math.min(100, Math.floor(score)));

            let currentFocusDuration = totalFocusDuration;
            const now = Date.now();
            if (score >= 80) {
              if (focusStartTime === null) {
                focusStartTime = now;
              }
              currentFocusDuration = totalFocusDuration + Math.floor((now - focusStartTime) / 1000);
            } else {
              if (focusStartTime !== null) {
                totalFocusDuration += Math.floor((now - focusStartTime) / 1000);
                focusStartTime = null;
              }
              currentFocusDuration = totalFocusDuration;
            }

            detectionData = {
              attentionScore: score,
              isFaceDetected: true,
              headYaw: yaw,
              headPitch: pitch,
              faceArea: faceArea,
              blinkRate: detectionData.blinkRate,
              focusDuration: currentFocusDuration,
            };

            let currentProblem = null;
            let currentMessage = '';

            const distanceStatus = getDistanceStatus(faceArea);
            if (distanceStatus === 'too_close') {
              currentProblem = 'too_close';
              currentMessage = '📏 离远一点~';
            } else if (distanceStatus === 'too_far') {
              currentProblem = 'too_far';
              currentMessage = '🔍 靠近一点嘛';
            } else if (Math.abs(yaw) > 25 || Math.abs(pitch) > 20) {
              currentProblem = 'distracted';
              currentMessage = '👀 看这里！';
            } else {
              currentProblem = null;
            }

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
              attentionScore: 0,
              faceArea: 0,
            };

            if (currentTipType !== 'no_face') {
              showCloudTip('😊 请正对摄像头', 'no_face', true);
            }
          }

          // Expose real-time vision data for the scoring pipeline
          window.__visionBridge__ = {
            headYaw: detectionData.headYaw,
            headPitch: detectionData.headPitch,
            faceArea: detectionData.faceArea,
            blinkRate: detectionData.blinkRate,
            blinkCount: totalBlinks,
            attentionScore: detectionData.attentionScore,
            focusDuration: detectionData.focusDuration,
            isFaceDetected: detectionData.isFaceDetected,
            timestamp: Date.now(),
          };

          updateBallScore();
          if (isPanelOpen) updatePanelData();
        } catch (error) {
          console.warn('检测过程中出错:', error);
          // 出错时仍然继续检测，避免整个网站崩溃
        }
      }
      animationId = requestAnimationFrame(detect);
    }
    detect();
  }
})();

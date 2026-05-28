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
    { name: 'short', duration: 4000 },   // 4秒快速窗口
    { name: 'medium', duration: 8000 },   // 8秒平衡窗口
    { name: 'long', duration: 30000 },    // 30秒稳定窗口
  ];
  
  let blinkRateHistory = []; // 频率历史记录
  const HISTORY_SIZE = 20;   // 历史记录长度

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

  // 面板状态
  let isPanelOpen = false;
  let floatingBall = null;
  let panel = null;
  let panelUpdateInterval = null;

  // 会话统计变量
  let sessionStartTime = null;
  let sessionEndTime = null;
  let sessionAttentionScores = [];
  let sessionDistractionCount = 0;
  let sessionBlinkRates = [];
  let sessionIsActive = false;

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
    const shortWindow = 4000;  // 4秒
    const mediumWindow = 8000; // 8秒
    const longWindow = 30000;  // 30秒

    const shortBlinks = blinkTimes.filter(t => t >= now - shortWindow);
    const mediumBlinks = blinkTimes.filter(t => t >= now - mediumWindow);
    const longBlinks = blinkTimes.filter(t => t >= now - longWindow);

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

  // 计算方差
  function calculateVariance(data) {
    if (data.length < 2) return 0;
    const mean = data.reduce((a, b) => a + b, 0) / data.length;
    return data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length;
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

  // ========== 会话统计 ==========
  function startSession() {
    sessionStartTime = Date.now();
    sessionAttentionScores = [];
    sessionDistractionCount = 0;
    sessionBlinkRates = [];
    sessionIsActive = true;
    console.log('📊 游戏会话开始');
  }

  function endSession() {
    if (!sessionIsActive) return;

    sessionEndTime = Date.now();
    sessionIsActive = false;

    const duration = (sessionEndTime - sessionStartTime) / 1000;
    const avgAttention =
      sessionAttentionScores.length > 0
        ? sessionAttentionScores.reduce((a, b) => a + b, 0) / sessionAttentionScores.length
        : 0;
    const maxAttention = sessionAttentionScores.length > 0 ? Math.max(...sessionAttentionScores) : 0;
    const minAttention = sessionAttentionScores.length > 0 ? Math.min(...sessionAttentionScores) : 0;
    const avgBlinkRate =
      sessionBlinkRates.length > 0 ? sessionBlinkRates.reduce((a, b) => a + b, 0) / sessionBlinkRates.length : 0;

    let attentionLevel = '一般';
    if (avgAttention >= 80) attentionLevel = '优秀';
    else if (avgAttention >= 60) attentionLevel = '良好';
    else if (avgAttention >= 40) attentionLevel = '一般';
    else attentionLevel = '需提升';

    const report = {
      timestamp: new Date().toISOString(),
      duration: Math.floor(duration),
      avgAttention: Math.round(avgAttention),
      maxAttention: maxAttention,
      minAttention: minAttention,
      distractionCount: sessionDistractionCount,
      avgBlinkRate: avgBlinkRate.toFixed(0),
      blinkBaseline: baselineBlinkRate ? baselineBlinkRate.toFixed(0) : '未建立',
      attentionLevel: attentionLevel,
      totalFrames: sessionAttentionScores.length,
    };

    console.log('📊 ========== 游戏会话报告 ==========');
    console.log(`游戏时长: ${report.duration} 秒`);
    console.log(`平均专注度: ${report.avgAttention} 分 (${report.attentionLevel})`);
    console.log(`最高专注度: ${report.maxAttention} 分`);
    console.log(`最低专注度: ${report.minAttention} 分`);
    console.log(`分心次数: ${report.distractionCount} 次`);
    console.log(`平均眨眼频率: ${report.avgBlinkRate} 次/分`);
    console.log(`眨眼基线: ${report.blinkBaseline} 次/分`);
    console.log(`总帧数: ${report.totalFrames} 帧`);
    console.log('====================================');

    const history = JSON.parse(localStorage.getItem('game_session_history') || '[]');
    history.push(report);
    if (history.length > 20) history.shift();
    localStorage.setItem('game_session_history', JSON.stringify(history));

    showSessionReport(report);

    return report;
  }

  function showSessionReport(report) {
    const modal = document.createElement('div');
    modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.6);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 20000;
            animation: fadeIn 0.3s ease;
        `;

    let levelColor = '#FF9800';
    if (report.attentionLevel === '优秀') levelColor = '#4CAF50';
    else if (report.attentionLevel === '良好') levelColor = '#8BC34A';
    else if (report.attentionLevel === '需提升') levelColor = '#F44336';

    modal.innerHTML = `
            <div style="
                background: linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%);
                border-radius: 20px;
                padding: 30px;
                width: 90%;
                max-width: 400px;
                text-align: center;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                border: 4px solid ${levelColor};
                animation: bounceIn 0.4s ease;
            ">
                <h2 style="color: ${levelColor}; margin-bottom: 20px;">📊 训练报告</h2>
                <div style="margin-bottom: 20px;">
                    <div style="font-size: 48px; font-weight: bold; color: ${levelColor};">
                        ${report.avgAttention}
                    </div>
                    <div style="color: #666;">平均专注度</div>
                    <div style="margin-top: 10px; padding: 5px 15px; background: ${levelColor}20; border-radius: 20px; display: inline-block;">
                        ${report.attentionLevel}
                    </div>
                </div>
                <div style="text-align: left; border-top: 1px solid #eee; padding-top: 15px;">
                    <p>⏱️ 训练时长: <strong>${report.duration}</strong> 秒</p>
                    <p>🎯 最高专注度: <strong>${report.maxAttention}</strong> 分</p>
                    <p>📉 最低专注度: <strong>${report.minAttention}</strong> 分</p>
                    <p>⚠️ 分心次数: <strong>${report.distractionCount}</strong> 次</p>
                    <p>👁️ 平均眨眼: <strong>${report.avgBlinkRate}</strong> 次/分</p>
                    <p>📊 眨眼基线: <strong>${report.blinkBaseline}</strong> 次/分</p>
                </div>
                <div style="margin-top: 20px;">
                    <button id="close-report-btn" style="
                        background: linear-gradient(90deg, #ffffffff, #ffffffff);
                        color: white;
                        border: none;
                        padding: 12px 30px;
                        border-radius: 30px;
                        font-size: 16px;
                        cursor: pointer;
                    ">关闭</button>
                </div>
            </div>
        `;

    document.body.appendChild(modal);
    document.getElementById('close-report-btn').addEventListener('click', () => {
      modal.remove();
    });
  }

  // ========== 初始化 ==========
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  async function init() {
    startSession();
    createFloatingBall();
    await startCamera();
    startDetection();
    // 自动打开面板，直观展示数据
    setTimeout(openPanel, 1000);
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
                background: white;
                border-radius: 30px;
                padding: 10px 18px;
                min-width: 130px;
                max-width: 220px;
                text-align: center;
                font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                font-size: 14px;
                font-weight: normal;
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

    const ballRect = floatingBall.getBoundingClientRect();
    let top = ballRect.top - 65;
    let left = ballRect.left + ballRect.width / 2 - 70;

    if (top < 10) top = ballRect.bottom + 10;
    if (left < 10) left = 10;
    if (left + 150 > window.innerWidth) left = window.innerWidth - 160;

    Object.assign(cloud.style, {
      position: 'fixed',
      top: top + 'px',
      left: left + 'px',
      zIndex: '10000',
      cursor: 'move',
      pointerEvents: 'auto',
    });

    if (persistent) {
      cloud.style.animation = 'cloudPulse 1.5s ease-in-out infinite';
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
        dragStartPanelLeft = parseFloat(panel.style.left) || window.innerWidth - 330;
        dragStartPanelTop = parseFloat(panel.style.top) || 100;
      }

      if (currentCloud) {
        dragStartCloudLeft = parseFloat(currentCloud.style.left) || window.innerWidth - 160;
        dragStartCloudTop = parseFloat(currentCloud.style.top) || 35;
      }

      element.style.cursor = 'grabbing';
      e.preventDefault();
    });
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

      panelNewLeft = Math.max(0, Math.min(window.innerWidth - 320, panelNewLeft));
      panelNewTop = Math.max(0, Math.min(window.innerHeight - 400, panelNewTop));

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

  document.addEventListener('mouseup', () => {
    if (activeDragElement) {
      activeDragElement = null;
      if (floatingBall) floatingBall.style.cursor = 'move';
    }
  });

  // ========== 小球创建 ==========
  function createFloatingBall() {
    floatingBall = document.createElement('div');
    floatingBall.id = 'floating-attention-ball';
    floatingBall.innerHTML = `
            <div id="ball-container" style="
                width: 100px;
                height: 100px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                cursor: move;
                transition: all 0.3s ease;
                position: relative;
                border-radius: 50%;
                background: linear-gradient(135deg, #4caf50, #81c784);
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            ">
                <div class="loader" style="
                    display: inline-flex;
                    gap: 10px;
                    z-index: 1;
                    margin-bottom: 5px;
                "></div>
                <div id="ball-face" style="
                    position: relative;
                    width: 40px;
                    height: 20px;
                    z-index: 1;
                ">
                    <div id="ball-mouth" style="
                        position: absolute;
                        bottom: 0;
                        left: 50%;
                        transform: translateX(-50%);
                        width: 20px;
                        height: 10px;
                        border-radius: 0 0 10px 10px;
                        border: 2px solid white;
                        border-top: none;
                    "></div>
                </div>
                <div id="ball-score" style="
                    position: absolute;
                    top: 10px;
                    left: 50%;
                    transform: translateX(-50%);
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.5);
                    z-index: 2;
                ">0</div>
            </div>
        `;

    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
            .loader:before,
            .loader:after {
                content: "";
                height: 20px;
                aspect-ratio: 1;
                border-radius: 50%;
                background: radial-gradient(farthest-side,#000 95%,#0000) 35% 35%/6px 6px no-repeat #fff;
                transform: scaleX(var(--s,1)) rotate(0deg);
                animation: l6 1s infinite linear;
            }
            
            .loader:after {
                --s: -1;
                animation-delay: -0.1s;
            }
            
            @keyframes l6 {
                100% {
                    transform: scaleX(var(--s,1)) rotate(360deg);
                }
            }
        `;
    document.head.appendChild(style);

    Object.assign(floatingBall.style, {
      position: 'fixed',
      top: '100px',
      right: '20px',
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
                        <span id="panel-blink-rate">--次/分</span>
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
      display: 'none',
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

    const ballRect = floatingBall.getBoundingClientRect();
    let panelLeft = ballRect.left - 330;
    let panelTop = ballRect.top;

    if (panelLeft < 10) {
      panelLeft = ballRect.right + 10;
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

    let angleText =
      detectionData.headYaw > 0
        ? `右转 ${Math.abs(detectionData.headYaw).toFixed(0)}°`
        : detectionData.headYaw < 0
          ? `左转 ${Math.abs(detectionData.headYaw).toFixed(0)}°`
          : '正对';
    panel.querySelector('#panel-head-angle').textContent = angleText;

    let distanceText = '--';
    if (detectionData.isFaceDetected) {
      const status = getDistanceStatus(detectionData.faceArea);
      if (status === 'too_close') distanceText = '⚠️ 太近';
      else if (status === 'too_far') distanceText = '⚠️ 太远';
      else distanceText = '✅ 适中';
    }
    panel.querySelector('#panel-distance').textContent = distanceText;

    // 眨眼频率正常范围阈值
    const BLINK_RATE_MIN = 5;  // 低于此值显示红色
    const BLINK_RATE_MAX = 70; // 高于此值显示红色

    // 眨眼频率显示
    const blinkStatus = getBlinkStatus();
    if (isBaselineCollecting) {
      panel.querySelector('#panel-blink-rate').innerHTML = `收集中...`;
    } else {
      // 获取趋势箭头（只有↑和↓）
      const arrow = blinkTrend === 'up' ? '↑' : '↓';

      // 整数显示
      const displayRate = Math.round(detectionData.blinkRate);

      // 根据阈值确定颜色：低于min或高于max显示红色
      let displayColor;
      if (displayRate < BLINK_RATE_MIN || displayRate > BLINK_RATE_MAX) {
        displayColor = '#FF6B6B'; // 红色 - 异常
      } else if (blinkChangeIntensity > 0.5) {
        displayColor = '#FF6B6B'; // 红色 - 剧烈变化
      } else if (blinkChangeIntensity > 0.3) {
        displayColor = '#FFC107'; // 黄色 - 中等变化
      } else {
        displayColor = blinkStatus.color; // 正常状态颜色
      }

      panel.querySelector('#panel-blink-rate').innerHTML =
        `<span style="color: ${displayColor}; font-weight: bold; font-size: 16px;">${displayRate}${arrow}</span>
         <span style="font-size: 11px; color: #888; margin-left: 3px;">次/分</span>`;
    }

    const minutes = Math.floor(detectionData.focusDuration / 60);
    const seconds = detectionData.focusDuration % 60;
    panel.querySelector('#panel-focus-time').textContent =
      `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  function updateBallScore() {
    const scoreElement = floatingBall?.querySelector('#ball-score');
    if (scoreElement) {
      scoreElement.textContent = detectionData.attentionScore;
      const ballContainer = floatingBall.querySelector('#ball-container');
      const ballMouth = floatingBall.querySelector('#ball-mouth');
      if (ballContainer && ballMouth) {
        // 确保线条粗细一致
        ballMouth.style.border = '2px solid white';

        if (detectionData.attentionScore >= 80) {
          // 绿色小球 - 微笑嘴（弧度更小）
          ballContainer.style.background = '#81c570';
          ballMouth.style.borderRadius = '0 0 5px 5px';
          ballMouth.style.borderTop = 'none';
          ballMouth.style.height = '8px';
        } else if (detectionData.attentionScore >= 60) {
          // 黄色小球 - 平嘴
          ballContainer.style.background = '#f89418';
          ballMouth.style.borderRadius = '0';
          ballMouth.style.borderTop = '2px solid white';
          ballMouth.style.borderBottom = 'none';
          ballMouth.style.height = '2px';
        } else {
          // 红色小球 - 生气嘴
          ballContainer.style.background = '#c01e25';
          ballMouth.style.borderRadius = '5px 5px 0 0';
          ballMouth.style.borderTop = '2px solid white';
          ballMouth.style.borderBottom = 'none';
          ballMouth.style.height = '8px';
        }
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
    currentBlinkRate = 0;
    smoothBlinkRate = 0;
    eyeClosedCounter = 0;
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

            if (sessionIsActive) {
              sessionAttentionScores.push(detectionData.attentionScore);
              sessionBlinkRates.push(detectionData.blinkRate);
            }

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
              if (currentTipType !== currentProblem) {
                sessionDistractionCount++;
              }
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

  // 移除 beforeunload 事件，避免点击下一关时显示会话报告
  // window.addEventListener('beforeunload', () => {
  //     if (sessionIsActive) {
  //         endSession();
  //     }
  // });
})();

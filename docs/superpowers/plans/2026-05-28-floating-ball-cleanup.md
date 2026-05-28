# 悬浮球代码精简 + 交互优化 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清理 floating-ball.js 死代码，加触摸拖拽支持，加面板过渡动画。

**Architecture:** 单文件改动，不改外部接口。触摸事件复用现有 mouse 拖拽逻辑。面板动画用 CSS transition + opacity/transform。

**Tech Stack:** Vanilla JS, CSS transitions

---

### Task 1: 删除死变量 + 死函数

**Files:**
- Modify: `frontend/floating-ball.js`

- [ ] **Step 1: 删除 8 个未用变量声明 (L67-76)**

删除以下行：
```javascript
  let wasDistracted = false;
  let wasTooClose = false;
  let wasTooFar = false;
  let lastTipTime = 0;
```
和：
```javascript
  let isDistractedTipShowing = false;
  let isTooCloseTipShowing = false;
  let isTooFarTipShowing = false;
  let isNoFaceTipShowing = false;
```

- [ ] **Step 2: 删除 `calculateVariance` 函数 (约 L203-208)**

删除整个函数体：
```javascript
  function calculateVariance(data) {
    if (data.length < 2) return 0;
    const mean = data.reduce((a, b) => a + b, 0) / data.length;
    return data.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / data.length;
  }
```

- [ ] **Step 3: 删除 `endSession` 函数 (约 L337-392)**

这个函数约 55 行，只被已注释的 beforeunload 调用。同时删除其依赖的 `showSessionReport` 函数。

- [ ] **Step 4: 删除 `showSessionReport` 函数 (约 L393-462)**

约 70 行的弹窗 HTML 生成函数。

- [ ] **Step 5: 删除 `startSession` 调用和会话数据累积代码**

在 `init()` 中删除 `startSession()` 调用行。

在 `function detect()` 中删除会话数据累积：
```javascript
// 删除这两行：
sessionAttentionScores.push(detectionData.attentionScore);
sessionBlinkRates.push(detectionData.blinkRate);
```

会话相关变量声明（`sessionStartTime` 等 7 个）也一并删除。

- [ ] **Step 6: 修复 3 个隐式全局变量**

在文件顶部变量声明区（约 L63 附近）添加：
```javascript
  let currentBlinkRate = 0;
  let smoothBlinkRate = 0;
  let eyeClosedCounter = 0;
```

同时删除 `startDetection()` 中这三行的赋值（L1297-1299），因为声明时已初始化。

- [ ] **Step 7: 验证 — 检查控制台无报错**

打开任意训练游戏页面，确认：
- 悬浮球正常显示
- 面板点击可开关
- 摄像头检测正常运行
- DevTools Console 无 JS 报错

- [ ] **Step 8: Commit**

```bash
git add frontend/floating-ball.js
git commit -m "chore: 清理floating-ball死代码 — 删除未用变量/函数，修复隐式全局变量"
```

---

### Task 2: 添加触摸拖拽支持

**Files:**
- Modify: `frontend/floating-ball.js` — `makeDraggable` 函数和 document 事件监听

- [ ] **Step 1: 在 `makeDraggable` 中添加 touchstart 监听**

在现有 `element.addEventListener('mousedown', ...)` 后面添加：
```javascript
    element.addEventListener('touchstart', (e) => {
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
    }, { passive: false });
```

- [ ] **Step 2: 添加 document 级 touchmove 监听**

在现有 `document.addEventListener('mousemove', ...)` 后面添加：
```javascript
  document.addEventListener('touchmove', (e) => {
    if (!activeDragElement) return;
    if (e.touches.length !== 1) return;

    var touch = e.touches[0];
    var deltaX = touch.clientX - dragStartX;
    var deltaY = touch.clientY - dragStartY;

    // 复用 mousemove 中已有的相同 delta 计算逻辑
    var newLeft = dragStartLeft + deltaX;
    var newTop = dragStartTop + deltaY;
    newLeft = Math.max(0, Math.min(window.innerWidth - 50, newLeft));
    newTop = Math.max(0, Math.min(window.innerHeight - 50, newTop));
    floatingBall.style.left = newLeft + 'px';
    floatingBall.style.top = newTop + 'px';
    floatingBall.style.right = 'auto';
    floatingBall.style.bottom = 'auto';

    if (panel && isPanelOpen) {
      var pnl = dragStartPanelLeft + deltaX;
      var pnt = dragStartPanelTop + deltaY;
      pnl = Math.max(0, Math.min(window.innerWidth - 284, pnl));
      pnt = Math.max(0, Math.min(window.innerHeight - 430, pnt));
      panel.style.left = pnl + 'px';
      panel.style.top = pnt + 'px';
      panel.style.right = 'auto';
      panel.style.bottom = 'auto';
    }

    if (currentCloud) {
      var cl = dragStartCloudLeft + deltaX;
      var ct = dragStartCloudTop + deltaY;
      cl = Math.max(0, Math.min(window.innerWidth - 150, cl));
      ct = Math.max(0, Math.min(window.innerHeight - 100, ct));
      currentCloud.style.left = cl + 'px';
      currentCloud.style.top = ct + 'px';
      currentCloud.style.right = 'auto';
      currentCloud.style.bottom = 'auto';
    }
  }, { passive: false });
```

- [ ] **Step 3: 添加 document 级 touchend 监听**

在现有 `document.addEventListener('mouseup', ...)` 后面添加：
```javascript
  document.addEventListener('touchend', () => {
    if (activeDragElement) {
      activeDragElement = null;
      if (floatingBall) floatingBall.style.cursor = 'move';
    }
  });
```

- [ ] **Step 4: 验证 — 移动端触摸拖拽**

在移动端或 Chrome DevTools 的设备模拟模式下：
- 触摸拖拽悬浮球，跟随手指移动
- 打开面板后，触摸拖拽面板，跟随手指移动
- 单指操作正常，页面不滚动
- 拖拽后点击，仍可正常开关面板

- [ ] **Step 5: Commit**

```bash
git add frontend/floating-ball.js
git commit -m "feat: 悬浮球添加触摸拖拽支持"
```

---

### Task 3: 面板打开/关闭过渡动画

**Files:**
- Modify: `frontend/floating-ball.js` — `openPanel()` 和 `closePanel()` 函数

- [ ] **Step 1: 在 createPanel 中给面板容器添加初始 transition 样式**

在 `Object.assign(panel.style, {...})` 中添加 transition：
```javascript
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
```

- [ ] **Step 2: 重写 `openPanel()` 动画逻辑**

```javascript
  function openPanel() {
    if (!panel) createPanel();

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
    panel.style.pointerEvents = 'auto';

    // 触发过渡：先设初始态，再切到终态
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        panel.style.opacity = '1';
        panel.style.transform = 'translateY(0)';
      });
    });

    isPanelOpen = true;
    updatePanelData();
    if (panelUpdateInterval) clearInterval(panelUpdateInterval);
    panelUpdateInterval = setInterval(updatePanelData, 500);
  }
```

- [ ] **Step 3: 重写 `closePanel()` 动画逻辑**

```javascript
  function closePanel() {
    panel.style.opacity = '0';
    panel.style.transform = 'translateY(8px)';
    panel.style.pointerEvents = 'none';

    var onTransitionEnd = function () {
      panel.style.display = 'none';
      panel.removeEventListener('transitionend', onTransitionEnd);
    };
    panel.addEventListener('transitionend', onTransitionEnd);

    isPanelOpen = false;
    if (panelUpdateInterval) {
      clearInterval(panelUpdateInterval);
      panelUpdateInterval = null;
    }
  }
```

- [ ] **Step 4: 验证 — 面板过渡动画**

- 点击悬浮球打开面板 → 面板从下方 8px 淡入滑上（200ms）
- 点击关闭按钮或收起 → 面板淡出滑下（200ms）
- 快速连续点击开关 → 动画正常，不卡状态
- 关闭后面板不阻挡点击（pointer-events:none 生效）

- [ ] **Step 5: Commit**

```bash
git add frontend/floating-ball.js
git commit -m "feat: 面板打开/关闭添加 200ms 淡入滑出过渡动画"
```

# floating-ball.js - 实时注意力检测浮球组件

## 概述

`floating-ball.js` 是一个基于 MediaPipe FaceLandmarker 的实时注意力检测组件，用于监测用户的面部状态、头部位姿、眨眼频率等数据，并计算专注度评分。

---

## 1. 视觉模型

### 1.1 MediaPipe FaceLandmarker

组件使用 **MediaPipe FaceLandmarker** 模型进行人脸关键点检测：

| 特性 | 说明 |
|------|------|
| **模型类型** | FaceLandmarker (468点面部特征点) |
| **运行模式** | VIDEO 模式，适用于视频流实时检测 |
| **最大检测人脸数** | 1 |
| **检测置信度阈值** | 0.5 |
| **追踪置信度阈值** | 0.5 |
| **推理后端** | GPU |
| **模型来源** | Google Cloud CDN |

### 1.2 关键点索引

组件使用以下关键点索引进行计算：

```javascript
// 左眼关键点索引
const LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144];
// 右眼关键点索引  
const RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380];
```

---

## 2. 核心算法说明

### 2.1 专注度评分规则

专注度评分采用百分制，计算公式如下：

```
专注度分数 = 100 - 头部转角扣分 - 头部俯仰扣分 - 距离过近扣分 - 距离过远扣分
```

**评分细则：**

| 因素 | 扣分规则 | 最大扣分 |
|------|---------|---------|
| **头部水平转角 (Yaw)** | `min(40, |yaw| × 1.2)` | 40分 |
| **头部垂直俯仰 (Pitch)** | `min(30, |pitch| × 0.8)` | 30分 |
| **距离过近** | 固定扣15分（面部面积 > 0.45） | 15分 |
| **距离过远** | 固定扣10分（面部面积 < 0.15） | 10分 |

**最终分数限制：** `max(0, min(100, 分数))`

### 2.2 人脸检测算法

人脸检测通过检查 FaceLandmarker 返回的关键点数据实现：

```javascript
if (results.faceLandmarks && results.faceLandmarks.length > 0) {
    // 人脸已检测
    detectionData.isFaceDetected = true;
} else {
    // 未检测到人脸
    detectionData.isFaceDetected = false;
}
```

**检测状态转换：**
- 检测到人脸 → 显示绿色状态指示
- 未检测到人脸 → 显示红色状态指示，并弹出提示云朵

### 2.3 头部转角算法

#### 水平转角 (Yaw)

使用脸颊和鼻子关键点计算：

```
faceWidth = |leftCheek.x - rightCheek.x|
noseOffset = (nose.x - (leftCheek.x + rightCheek.x) / 2) / faceWidth
yaw = -noseOffset × 60  // 转换为角度，范围约 ±30°
```

#### 垂直俯仰 (Pitch)

使用额头和下巴关键点计算：

```
faceHeight = |chin.y - forehead.y|
noseYOffset = (nose.y - (forehead.y + chin.y) / 2) / faceHeight
pitch = noseYOffset × 45  // 转换为角度，范围约 ±22.5°
```

### 2.4 屏幕距离算法

通过计算面部在图像中的面积来判断距离：

```javascript
function getDistanceStatus(faceArea) {
    if (faceArea > 0.45) return 'too_close';   // 太近
    if (faceArea < 0.05) return 'too_far';     // 太远
    return 'normal';                            // 适中
}
```

**面积计算：**
```
faceArea = faceWidth × faceHeight
```

### 2.5 眨眼频率算法

#### 2.5.1 EAR (Eye Aspect Ratio) 算法

使用眼睛纵横比检测眨眼：

```
EAR = (A + B) / (2 × C)
```

其中：
- A = 垂直距离 p1-p5
- B = 垂直距离 p2-p4
- C = 水平距离 p0-p3

**眨眼判定阈值：**
| 参数 | 值 | 说明 |
|------|-----|------|
| EAR_THRESHOLD | 0.2 | 闭眼判定阈值 |
| EAR_RECOVER_THRESHOLD | 0.28 | 睁眼恢复阈值 |
| MIN_BLINK_INTERVAL | 200ms | 最小眨眼间隔（去重） |

#### 2.5.2 多级窗口自适应融合算法

采用三级窗口融合计算眨眼频率：

**窗口配置：**
| 窗口 | 时长 | 作用 |
|------|------|------|
| 短窗口 | 4秒 | 快速响应，检测突变 |
| 中窗口 | 8秒 | 平衡响应 |
| 长窗口 | 30秒 | 稳定输出 |

**自适应融合权重：**
| 变化强度 | 短窗口权重 | 中窗口权重 | 长窗口权重 |
|---------|-----------|-----------|-----------|
| 剧烈变化 (>0.5) | 60% | 10% | 30% |
| 中等变化 (0.2-0.5) | 40% | 20% | 40% |
| 小变化 (<0.2) | 20% | 10% | 70% |

**计算公式：**
```javascript
fusedRate = shortRate × shortWeight
           + mediumRate × mediumWeight
           + longRate × longWeight

// 最终输出再经过平滑滤波
currentBlinkRate = currentBlinkRate × 0.8 + fusedRate × 0.2
```

**趋势检测：**
```javascript
// 基于最近3次频率变化判断趋势
avgDiff = (diff1 + diff2) / 2
if (avgDiff > 0.3) → 上升趋势 (↑)
if (avgDiff < -0.3) → 下降趋势 (↓)
```

**阈值判断：**
| 参数 | 值 | 说明 |
|------|-----|------|
| BLINK_RATE_MIN | 5 | 低于此值显示红色 |
| BLINK_RATE_MAX | 70 | 高于此值显示红色 |

### 2.6 持续专注算法

专注时长累计规则：

```javascript
if (attentionScore >= 80) {
    // 专注状态：累计专注时间
    currentFocusDuration = totalFocusDuration + (now - focusStartTime)
} else {
    // 分心状态：暂停累计，保存当前专注段
    totalFocusDuration += (now - focusStartTime)
    focusStartTime = null
}
```

**统计指标：**
- **totalFocusDuration**：总专注时长（秒）
- **sessionDistractionCount**：分心次数（头部偏离时计数）

---

## 3. 数据结构

### 3.1 检测数据对象

```javascript
detectionData = {
    attentionScore: 0,      // 专注度分数 (0-100)
    isFaceDetected: false,  // 人脸检测状态
    headYaw: 0,             // 头部水平转角 (°)
    headPitch: 0,           // 头部垂直俯仰 (°)
    faceArea: 0,            // 面部面积比例
    blinkRate: 0,           // 眨眼频率 (次/分)
    focusDuration: 0        // 持续专注时长 (秒)
}
```

### 3.2 眨眼状态

```javascript
blinkTrend = 'up' | 'down'           // 趋势方向
blinkChangeIntensity = 0-1           // 变化强度
baselineBlinkRate = 12               // 默认基线频率
```

---

## 4. 组件功能

### 4.1 浮球显示

- **颜色变化**：根据专注度分数动态改变（绿→黄→红）
- **表情变化**：微笑(≥80分)、平嘴(≥60分)、生气(<60分)
- **分数显示**：实时显示专注度分数

### 4.2 面板数据展示

| 指标 | 显示内容 | 更新频率 |
|------|---------|---------|
| 专注度 | 分数 + 进度条 | 每帧 |
| 人脸状态 | ✅已检测 / ❌未检测 | 每帧 |
| 头部转角 | 左转/右转角度 | 每帧 |
| 屏幕距离 | ✅适中 / ⚠️太近/太远 | 每帧 |
| 眨眼频率 | 数值 + 趋势箭头 + 颜色 | 每500ms |
| 持续专注 | MM:SS 格式 | 每500ms |

### 4.3 云朵提示

当检测到异常状态时显示卡通云朵提示：

| 状态 | 提示内容 |
|------|---------|
| 距离过近 | 📏 离远一点~ |
| 距离过远 | 🔍 靠近一点嘛 |
| 头部偏离 | 👀 看这里！ |
| 未检测人脸 | 😊 请正对摄像头 |

---

## 5. 会话统计

组件记录完整的训练会话数据：

```javascript
sessionReport = {
    timestamp: ISO时间戳,
    duration: 游戏时长(秒),
    avgAttention: 平均专注度,
    maxAttention: 最高专注度,
    minAttention: 最低专注度,
    distractionCount: 分心次数,
    avgBlinkRate: 平均眨眼频率,
    blinkBaseline: 眨眼基线,
    attentionLevel: 专注等级(优秀/良好/一般/需提升),
    totalFrames: 总检测帧数
}
```

**专注等级判定：**
| 平均专注度 | 等级 |
|-----------|------|
| ≥80 | 优秀 |
| ≥60 | 良好 |
| ≥40 | 一般 |
| <40 | 需提升 |

---

## 6. 文件引用

组件通过 `attention-loader.js` 动态注入，仅在游戏/测评页面加载：

```javascript
// attention-loader.js 加载逻辑
if (isGamePage || isDetectPage) {
    // 加载 MediaPipe → 注入 floating-ball.js
}
```

---

## 7. 浏览器兼容性

| 浏览器 | 支持状态 | 备注 |
|--------|---------|------|
| Chrome | ✅ 支持 | 推荐 |
| Firefox | ✅ 支持 | 需要 HTTPS |
| Safari | ✅ 支持 | 需要 HTTPS |
| Edge | ✅ 支持 | |

**注意**：需要用户授权摄像头权限，建议在 HTTPS 环境下使用。
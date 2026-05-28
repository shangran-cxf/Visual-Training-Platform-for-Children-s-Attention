# frontend/detect/ — 注意力测评

5 级测评，每级对应一个注意力维度，用于训练前的初始评估 + 训练后复测。

## 测评列表

| 等级   | 文件          | 对应维度   |
| ------ | ------------- | ---------- |
| 等级 1 | `level1.html` | 选择性注意 |
| 等级 2 | `level2.html` | 持续性注意 |
| 等级 3 | `level3.html` | 视觉追踪   |
| 等级 4 | `level4.html` | 工作记忆   |
| 等级 5 | `level5.html` | 抑制控制   |

## 测评总览

`index.html` — 测评中心页面，展示五级测评入口，提供跳转到训练中心的入口。

---

## 数据流（当前实现状态 — P0 全部完成）

### 完整链路总览

```
level1~5.html (各关卡)
    │
    ├─► finishGame / endGame
    │       │
    │       ├─ [✅] localStorage: levelX_data + detection_data
    │       │       ├─ 关卡得分存为 levelX_data（如 level1_data.selective_attention）
    │       │       └─ 合并写入 detection_data（所有维度聚合对象）
    │       │
    │       ├─ [✅] POST /api/training/session/start → /api/training/game-data → /api/training/session/end
    │       │       （将测评关卡的游戏行为作为训练数据上传，存入 training_sessions + session_summaries）
    │       │
    │       └─ [✅] 完成面板"🎯 针对性训练"按钮 → 跳转到对应维度的训练游戏
    │               level1 → schulte.html   (选择性注意)
    │               level2 → magic-maze.html(持续性注意)
    │               level3 → sun-tracking.html(视觉追踪)
    │               level4 → reverse-memory.html(工作记忆)
    │               level5 → traffic-light.html(抑制控制)
    │
    ▼
detect/index.html (测评中心)
    │
    ├─ [✅] loadDetectionFromBackend() 页面加载时从 GET /api/get/detection 恢复历史测评记录
    │       （清缓存/换设备后自动从后端恢复已完成状态）
    ├─ [✅] updateLevelStatus() 从 localStorage 更新关卡卡片得分
    ├─ [✅] 5关全部完成后 uploadDetectionToBackend() 调用 POST /api/upload/detection
    │       （聚合5维得分 + total_score 持久化到后端 detection_data 表）
    ├─ [✅] 完成后"📋 查看训练建议"按钮 → 跳转 ../training/index.html
    └─ [✅] 侧边栏"训练"按钮 → 跳转 ../child-home.html

training/index.html (训练中心)
    │
    ├─ [✅] generateRecommendedGames() 优先调用 GET /api/get/detection 从后端获取测评
    │       API 失败或无登录时 fallback 到 localStorage
    ├─ [✅] renderRecommended() 根据薄弱维度推荐训练游戏
    ├─ [✅] "📋 重新测评"按钮 → 跳转 ../detect/index.html
    ├─ [✅] checkReassessmentReminder() 每10次访问弹窗提醒复测（3天冷却期）
    └─ [✅] dismissReassessToast() 可关闭提醒，记录时间戳

child-home.html / today-training.html
    │
    └─ [✅] 通过 GET /api/get/detection 从后端获取测评数据，用于雷达图和推荐
```

### 后端持久化测评记录

| 端点                    | 方法 | 状态         | 说明                                                                         |
| ----------------------- | ---- | ------------ | ---------------------------------------------------------------------------- |
| `/api/upload/detection` | POST | ✅ 后端已实现 | 接收 selective_attention 等 5 维得分 + total_score，写入 `detection_data` 表 |
| `/api/get/detection`    | GET  | ✅ 后端已实现 | 按 child_id 查询历史测评记录，按时间倒序返回                                 |

后端 API 位于 `backend/analytics/data_collector.py`，路由注册在 `data_collector_bp` Blueprint。

### 测评-训练双向导航

| 导航方向      | 状态     | 实现位置                     | 说明                                                  |
| ------------- | -------- | ---------------------------- | ----------------------------------------------------- |
| 测评→训练     | ✅ 已完成 | detect/index.html L1130      | "📋 查看训练建议" 按钮 → training/index.html           |
| 测评→训练     | ✅ 已完成 | detect/index.html L1018      | 侧边栏"训练" → child-home.html                        |
| 完成页→训练   | ✅ 已完成 | level1~5.html endGame()      | "🎯 针对性训练" 按钮，跳对应维度训练游戏               |
| 训练→测评     | ✅ 已完成 | training/index.html L256     | "📋 重新测评" 按钮 → detect/index.html                 |
| 训练→复测提醒 | ✅ 已完成 | training/index.html L488-520 | 每10次访问右下角弹出 Toast，含"去复测"按钮，3天冷却期 |

---

## 测评-训练 关系流程

### 当前实际流程 (AS-IS / P0 修复后)

```
┌─────────────────────────────────────────────────────────────┐
│                      测评阶段 (detect/)                      │
│                                                             │
│  index.html → level1 → level2 → level3 → level4 → level5   │
│                              │                              │
│         每个 level 完成后：                                  │
│           ✅ localStorage: levelX_data + detection_data      │
│           ✅ "🎯 针对性训练" → 对应维度游戏                   │
│           ✅ POST training session 数据到后端                │
│                              │                              │
│  全部5关完成后 detect/index.html:                            │
│           ✅ POST /api/upload/detection (持久化到DB)          │
│           ✅ "📋 查看训练建议" → training/index.html          │
│           ✅ 页面加载时 GET /api/get/detection (恢复历史)    │
└──────────────────────┬──────────────────────────────────────┘
                       │ 后端 API (可靠桥梁)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      训练阶段 (training/)                    │
│                                                             │
│  training/index.html 从 GET /api/get/detection 获取测评      │
│       ↓                                                     │
│  按薄弱维度推荐训练游戏                                      │
│       ↓                                                     │
│  ✅ "📋 重新测评" → detect/index.html (随时可回测评)        │
│  ✅ 每10次访问 → 右下角 Toast "建议复测" → 3天冷却期         │
│  ✅ 训练游戏间自由切换                                       │
└─────────────────────────────────────────────────────────────┘
```

### 关键数据流设计

```
localStorage (本地缓存)
    ├─ levelX_data        ← 各关卡得分 (localStorage + API 恢复)
    ├─ detection_data     ← 聚合数据   (localStorage + API 恢复)
    ├─ training_visit_count     ← 训练访问计数
    └─ reassess_dismissed_at    ← 复测提醒关闭时间

后端 detection_data 表
    ├─ child_id
    ├─ selective_attention / sustained_attention / visual_tracking
    ├─ working_memory / inhibitory_control / total_score
    └─ timestamp (自动)

读写策略：localStorage 为读写缓存，后端为持久化权威源。
  - 写入：localStorage 实时写 → 5关完成时 POST /api/upload/detection 同步后端
  - 读取：优先 localStorage，无数据时 GET /api/get/detection 从后端恢复
```

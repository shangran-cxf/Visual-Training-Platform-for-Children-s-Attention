# API 接口文档

本文档定义了训练数据分析系统的所有 API 接口。

## 基础信息

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`

---

## 1. 训练会话接口

### 1.1 开始训练会话

**请求**
```
POST /api/training/session/start
```

**请求体**
```json
{
  "child_id": 1,
  "game_type": "level1",
  "device_id": "web-browser"
}
```

**参数说明**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| child_id | int | 是 | 孩子ID |
| game_type | string | 是 | 游戏类型标识（见游戏类型对照表） |
| device_id | string | 否 | 设备标识 |

**响应**
```json
{
  "message": "训练会话已创建",
  "session_id": 123,
  "session_token": "abc123...",
  "game_type": "level1",
  "game_name": "线索筛选站"
}
```

---

### 1.2 结束训练会话

**请求**
```
POST /api/training/session/end
```

**请求体**
```json
{
  "session_id": 123
}
```

**响应**
```json
{
  "message": "训练会话已结束",
  "session_id": 123,
  "summary": {
    "final_score": 85,
    "performance_level": "良好",
    "accuracy_score": 0.89,
    "precision_score": 0.80,
    "speed_score": 0.25,
    "head_stable_score": 0.92,
    "face_stable_score": 0.88,
    "blink_stable_score": 0.85
  },
  "earned_badges": [],
  "recommendations": ["表现良好，继续保持！"]
}
```

---

### 1.3 心跳保活

**请求**
```
POST /api/training/session/heartbeat
```

**请求体**
```json
{
  "session_id": 123
}
```

**响应**
```json
{
  "message": "心跳更新成功",
  "session_id": 123,
  "status": "active"
}
```

---

### 1.4 中断训练会话

**请求**
```
POST /api/training/session/interrupt
```

**请求体**
```json
{
  "session_id": 123,
  "current_state": {
    "progress": 50,
    "current_level": 2
  }
}
```

**响应**
```json
{
  "message": "会话已中断",
  "session_id": 123,
  "status": "interrupted"
}
```

---

## 2. 数据上传接口

### 2.1 上传视觉数据

**请求**
```
POST /api/training/vision-data
```

**请求体**
```json
{
  "session_id": 123,
  "request_id": "uuid-1234",
  "timestamp": "2026-04-04T10:30:00.000Z",
  "head_yaw": 5.2,
  "head_pitch": -3.1,
  "face_distance": 150.5,
  "blink_count": 0
}
```

**参数说明**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | int | 是 | 训练会话ID |
| request_id | string | 否 | 请求唯一标识（防重复） |
| timestamp | string | 否 | 数据采集时间（ISO 8601格式），不填则使用服务器时间 |
| head_yaw | float | 是 | 头部左右偏转角（度） |
| head_pitch | float | 是 | 头部上下偏转角（度） |
| face_distance | float | 是 | 人脸距离（相对值） |
| blink_count | int | 是 | 眨眼次数 |

**响应**
```json
{
  "message": "视觉数据上传成功"
}
```

---

### 2.2 上传游戏数据

**请求**
```
POST /api/training/game-data
```

**请求体**
```json
{
  "session_id": 123,
  "request_id": "uuid-5678",
  "timestamp": "2026-04-04T10:30:00.000Z",
  "event_type": "game_result",
  "time": 45,
  "correct": 8,
  "error": 2,
  "miss": 1,
  "total_target": 10
}
```

**参数说明**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| session_id | int | 是 | 训练会话ID |
| request_id | string | 否 | 请求唯一标识（防重复） |
| timestamp | string | 否 | 数据采集时间（ISO 8601格式），不填则使用服务器时间 |
| event_type | string | 是 | 事件类型 |
| time | int | 否 | 完成时间（秒），默认0 |
| correct | int | 否 | 正确次数，默认0 |
| error | int | 否 | 错误次数，默认0 |
| miss | int | 否 | 遗漏次数，默认0 |
| leave | int | 否 | 离开次数，默认0 |
| obstacle | int | 否 | 撞障碍次数，默认0 |
| total_target | int | 否 | 总目标数，默认1 |
| total_step | int | 否 | 总操作步数，默认1 |
| total_click | int | 否 | 总点击次数，默认1 |
| total_trial | int | 否 | 总试验次数，默认1 |
| memory_load | int | 否 | 记忆项目数，默认1 |
| order_error | int | 否 | 顺序错误次数，默认0 |
| late_error_ratio | float | 否 | 后30%错误比例，默认0 |
| mean_rt | int | 否 | 平均反应时间（毫秒），默认1000 |
| reaction_times | [int] | 否 | 各次反应时间列表 |

**响应**
```json
{
  "message": "游戏数据上传成功"
}
```

---

## 3. 数据查询接口

### 3.1 查询训练历史

**请求**
```
GET /api/training/history/{child_id}
```

**查询参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |
| game_type | string | 否 | 游戏类型筛选 |
| attention_type | string | 否 | 注意力类型筛选 |
| limit | int | 否 | 返回条数限制，默认20 |
| offset | int | 否 | 偏移量，用于分页 |

**响应**
```json
{
  "total": 50,
  "limit": 20,
  "offset": 0,
  "records": [
    {
      "session_id": 123,
      "game_type": "level1",
      "game_name": "线索筛选站",
      "attention_type": "selective",
      "final_score": 85,
      "performance_level": "良好",
      "duration": 45,
      "created_at": "2026-04-04 10:30:00"
    }
  ]
}
```

---

### 3.2 查询训练详情

**请求**
```
GET /api/training/detail/{session_id}
```

**响应**
```json
{
  "session_id": 123,
  "child_id": 1,
  "game_type": "level1",
  "game_name": "线索筛选站",
  "attention_type": "selective",
  "final_score": 85,
  "performance_level": "良好",
  "duration": 45,
  "created_at": "2026-04-04 10:30:00",
  "details": {
    "accuracy_score": 89,
    "precision_score": 80,
    "speed_score": 25,
    "head_stable_score": 92,
    "face_stable_score": 88,
    "blink_stable_score": 85
  },
  "game_data": {
    "time": 45,
    "correct": 8,
    "error": 2,
    "miss": 1,
    "total_target": 10
  },
  "vision_summary": {
    "avg_head_deviation": 5.2,
    "avg_blink_rate": 12,
    "attention_stability": 85
  }
}
```

---

### 3.3 查询训练趋势

**请求**
```
GET /api/training/trend/{child_id}
```

**查询参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| attention_type | string | 否 | 注意力类型筛选 |
| days | int | 否 | 查询最近N天的数据，默认30 |

**响应**
```json
{
  "child_id": 1,
  "period": {
    "start_date": "2026-03-05",
    "end_date": "2026-04-04",
    "days": 30
  },
  "trend": {
    "selective": {
      "avg_score": 82,
      "trend": "up",
      "records": [
        {"date": "2026-04-01", "score": 80},
        {"date": "2026-04-02", "score": 85},
        {"date": "2026-04-03", "score": 82}
      ]
    },
    "sustained": {
      "avg_score": 78,
      "trend": "stable",
      "records": []
    },
    "tracking": {
      "avg_score": 75,
      "trend": "up",
      "records": []
    },
    "memory": {
      "avg_score": 70,
      "trend": "down",
      "records": []
    },
    "inhibitory": {
      "avg_score": 72,
      "trend": "stable",
      "records": []
    }
  },
  "overall": {
    "avg_score": 75,
    "total_sessions": 25,
    "improvement": 5
  }
}
```

---

## 4. 错误响应

所有接口在出错时返回统一格式：

```json
{
  "error": "错误信息描述"
}
```

**常见错误码**
| HTTP状态码 | 说明 |
|-----------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如已有活跃会话） |
| 500 | 服务器内部错误 |

---

## 5. 评分算法说明

### 5.1 视觉指标计算

```
head_stable = 1 - (头部偏转角标准差 / 30)
face_stable = 1 - (人脸距离变化率 / 50)
blink_stable = 1 - (眨眼频率 / 25)
```

### 5.2 各维度评分公式

**选择性注意**
```
accuracy = correct / (correct + miss)
precision = correct / (correct + error)
speed = 1 - time / 60
score = accuracy * 0.35 + precision * 0.25 + speed * 0.20 + head_stable * 0.10 + blink_stable * 0.10
```

**持续性注意**
```
speed = 1 - time / 120
stable_act = 1 - (error + leave) / total_step
no_fatigue = 1 - late_error_ratio
score = stable_act * 0.30 + no_fatigue * 0.25 + speed * 0.20 + head_stable * 0.15 + blink_stable * 0.10
```

**视觉追踪**
```
acc = correct / total_click
speed = 1 - time / 60
rt_score = 1 - mean_rt / 1000
score = acc * 0.35 + rt_score * 0.25 + speed * 0.20 + head_stable * 0.12 + face_stable * 0.08
```

**工作记忆**
```
acc = correct / (correct + error)
speed = 1 - time / 60
order = 1 - order_error / memory_load
score = acc * 0.40 + order * 0.20 + speed * 0.20 + head_stable * 0.12 + blink_stable * 0.08
```

**抑制控制**
```
acc = correct / total_trial
impulse = 1 - (error + obstacle) / total_trial
score = impulse * 0.40 + acc * 0.30 + head_stable * 0.15 + face_stable * 0.08 + blink_stable * 0.07
```

### 5.3 等级评定

| 分数范围 | 等级 |
|---------|------|
| 90-100 | 优秀 |
| 75-89 | 良好 |
| 50-74 | 一般 |
| 0-49 | 较弱 |

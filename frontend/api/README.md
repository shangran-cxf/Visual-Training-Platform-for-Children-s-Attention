# frontend/api/ — 前端 API 客户端

封装后端 API 调用，ES module 方式组织。

## 文件说明

| 文件 | 职责 |
|---|---|
| `config.js` | API 配置：base URL 自动检测（localhost vs 生产）、超时时间、Token 存储 key、游戏类型映射、注意力类型名称、错误码常量 |
| `request.js` | 通用 `apiGet(url, params)` / `apiPost(url, data)` 函数：自动注入 `Authorization: Bearer <token>` 头、超时控制（AbortController）、统一错误处理 |
| `errors.js` | API 错误处理工具类 |
| `training.js` | 训练会话专用 API：`startSession`、`endSession`、`uploadGameData`、`uploadVisionData`、`heartbeat`、`interruptSession`、训练历史/详情/趋势/每日汇总查询 |

## 使用方式

```javascript
import { apiGet, apiPost } from './api/request.js';
import { startSession, uploadGameData } from './api/training.js';

// 通用请求
const res = await apiGet('/api/user/query');
const res = await apiPost('/api/login', { username, password });

// 训练专用
const session = await startSession(childId, gameType);
await uploadGameData(session.session_id, gameData);
```

## 配置

- 本地开发：`http://localhost:5000`
- 生产环境：自动检测当前域名
- Token 存储在 `localStorage`，key 为 `auth_token`

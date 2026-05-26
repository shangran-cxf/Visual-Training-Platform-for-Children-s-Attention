# backend/ai/ — AI 训练评估

调用 DeepSeek API（OpenAI 兼容接口）生成训练评估报告。

## 文件说明

| 文件 | 职责 |
|---|---|
| `config.py` | AI 配置加载（从 `.env` 读取）、Prompt 模板（当前训练评估 + 历史训练评估，含结构化 JSON 输出 Schema） |
| `analysis.py` | `ai_bp` Blueprint：当前训练评估、历史趋势分析、自定义生成、综合训练分析报告、AI 状态检查 |
| `validator.py` | 数据指纹（MD5）缓存 + LRU 内存缓存（24h TTL）+ 空报告模板 |

## 配置

在 `backend/ai/` 下创建 `.env` 文件（已 gitignore）：

```
AI_API_KEY=your_api_key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-flash
```

## API 路由

| 路由 | 方法 | 用途 |
|---|---|---|
| `/api/ai/current-training-evaluation` | POST | 当前训练评估 |
| `/api/ai/history-training-evaluation` | POST | 历史趋势分析 |
| `/api/ai/generate` | POST | 自定义 Prompt 生成 |
| `/api/ai/training-analysis` | POST | 综合训练分析报告 |
| `/api/ai/status` | GET | AI 配置状态检查 |

## 缓存策略

- 对输入数据计算 MD5 指纹
- 相同指纹在 24h 内直接返回缓存结果
- LRU 淘汰策略，避免重复调用 API

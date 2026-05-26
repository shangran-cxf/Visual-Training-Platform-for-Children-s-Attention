# backend/ — Flask API 服务层

Flask REST API，通过 Blueprint 模块化组织。入口文件 `app.py`。

## 文件说明

| 文件 | 职责 |
|---|---|
| `app.py` | Flask 应用创建、CORS、`before_request` 认证检查、Blueprint 注册、静态文件服务、错误处理 |
| `config.py` | 集中配置：16 种游戏类型、5 个注意力维度、评分权重、绩效等级、8 种徽章、论坛分类 |
| `requirements.txt` | Python 依赖：Flask, Flask-CORS, bcrypt, openai>=1.0 |
| `gunicorn_conf.py` | 生产环境 Gunicorn 配置（4 workers, 2 threads, 0.0.0.0:5000） |
| `uwsgi.ini` | 生产环境 uWSGI 配置 |

## 业务逻辑层

| 目录 | 职责 | 详见 |
|---|---|---|
| `modules/` | 7 个 API Blueprint 模块 | [modules/README.md](modules/README.md) |
| `analytics/` | 数据采集、评分引擎、注意力分析、报告生成 | [analytics/README.md](analytics/README.md) |
| `ai/` | AI 训练评估（DeepSeek API） | [ai/README.md](ai/README.md) |
| `middleware/` | Token 认证中间件 | [middleware/README.md](middleware/README.md) |
| `utils/` | 公共工具函数 | [utils/README.md](utils/README.md) |

## 启动

```bash
python backend/app.py          # 开发
gunicorn -c backend/gunicorn_conf.py app:app   # 生产
```

## API 响应格式

成功：`{success: true, message: "...", data: {...}}`
失败：`{success: false, error: {code: "...", message: "..."}}`

## 认证机制

Token 通过 `itsdangerous.URLSafeTimedSerializer` 生成，7 天有效期。`before_request` 选择性豁免公开路径（`/api/login`、`/api/register` 等）。

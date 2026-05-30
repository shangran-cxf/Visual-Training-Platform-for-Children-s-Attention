# 童眸智训 (Visual Training Platform for Children's Attention)

基于 Flask + 原生 HTML/CSS/JS 的儿童注意力训练平台。通过游戏化训练、实时面部检测和 AI 分析，帮助 6-12 岁儿童提升注意力水平。

## 项目架构

```
├── frontend/              # 前端层 - 静态 HTML/CSS/JS 页面
│   ├── api/               #   ES6 模块化 API 请求层
│   ├── training/          #   11 个训练游戏
│   ├── detect/            #   5 级注意力测评 + 综合测评
│   ├── assessment/        #   测评报告（儿童版/家长版）
│   ├── knowledge/         #   知识库文章 + 后台管理
│   └── images/ sounds/    #   素材资源
├── backend/               # 后端层 - Flask REST API 服务
│   ├── modules/           #   路由蓝图（auth, children, forum, knowledge, badges, admin, user_stats）
│   ├── analytics/         #   评分引擎、注意力分析、数据采集、报告生成
│   ├── ai/                #   AI 训练评估模块（DeepSeek API）
│   ├── middleware/        #   Token 认证中间件
│   └── utils/             #   工具函数
├── database/              # 数据库层 - SQLite
├── tests/                 # pytest 测试（135 个）
└── scripts/               # 数据分析与迁移脚本
```

三层分离，各层有自己的 README.md 说明内部结构。

## 快速开始

### 1. 安装依赖

```bash
pip install -r backend/requirements.txt
npm install              # Prettier（代码格式化）
pre-commit install       # Git 提交前自动检查
```

### 2. 启动服务

```bash
# 开发模式（Flask 内置服务器，自动热重载）
python run.py

# 或指定端口和调试模式
python run.py --port 8080 --debug

# 生产模式（需先安装 gunicorn）
python run.py --prod gunicorn

# 生产模式（需先安装 uwsgi）
python run.py --prod uwsgi
```

启动后访问 `http://localhost:5000`。

### 3. 环境变量

生产环境可通过环境变量覆盖默认配置：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `FLASK_DEBUG` | `true` | 调试模式开关 |
| `FLASK_HOST` | `0.0.0.0` | 监听地址 |
| `FLASK_PORT` | `5000` | 监听端口 |
| `SECRET_KEY` | 内置默认值 | Flask 密钥（生产务必修改） |
| `DATABASE_PATH` | `database/attention.db` | 数据库路径 |
| `GUNICORN_BIND` | `0.0.0.0:5000` | Gunicorn 绑定地址 |

### 4. 运行测试

```bash
pytest                    # 135 个测试
```

### 5. 数据库

首次启动自动创建表结构并初始化默认数据。数据库文件位于 `database/attention.db`。

### 6. AI 分析（可选）

在 `backend/ai/` 下创建 `.env` 文件（模板见 `backend/ai/.env.example`）：

```
AI_API_KEY=your_api_key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-flash
```

## 核心功能

- **五大注意力维度训练** — 选择性注意、持续性注意、视觉追踪、工作记忆、抑制控制，共 11 个训练游戏
- **五级注意力测评** — 逐维度测评 + 综合测评，生成儿童/家长双版评估报告
- **实时面部检测** — 基于 MediaPipe FaceLandmarker 的 EAR 眨眼检测、头部姿态估计、专注时长追踪，浮动小球可视化
- **AI 训练评估** — 调用 DeepSeek API 生成结构化训练评析报告，支持缓存去重
- **评分引擎** — 五维度加权评分，结合游戏表现与视觉指标，支持跨游戏 Z-score 归一化（T 分数）
- **数据采集** — 会话生命周期管理（开始/心跳/中断/结束），请求去重，视觉数据 2Hz 上报
- **家长仪表盘** — Chart.js 可视化训练历史、五维雷达图、维度趋势
- **论坛社区** — 帖子/评论/投票/收藏，搜索与分类，用户等级系统
- **勋章系统** — 8 枚成就勋章，训练完成自动颁发
- **知识库** — 儿童注意力科普文章，标签筛选，后台管理
- **后台管理** — 用户管理、系统统计、训练记录查看

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python Flask, SQLite, itsdangerous (Token 认证), bcrypt, Pillow, OpenAI SDK |
| 前端 | 原生 HTML/CSS/JS, Chart.js, MediaPipe FaceLandmarker (CDN) |
| AI | DeepSeek API (OpenAI 兼容接口) |
| 部署 | Gunicorn / uWSGI |

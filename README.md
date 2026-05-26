# 童眸智训 (Visual Training Platform for Children's Attention)

基于 Flask + 原生 HTML/CSS/JS 的儿童注意力训练平台。通过游戏化训练、实时面部检测和 AI 分析，帮助 6-12 岁儿童提升注意力水平。

## 项目架构

```
├── frontend/          # 前端层 - 静态 HTML/CSS/JS 页面
├── backend/           # 后端层 - Flask REST API 服务
└── database/          # 数据库层 - SQLite 数据库
```

三层分离，各层有自己的 README.md 说明内部结构。

## 快速开始

### 1. 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 2. 启动服务

```bash
python backend/app.py
```

默认运行在 `http://localhost:5000`。

### 3. 数据库

首次启动自动创建表结构并初始化默认数据。数据库文件位于 `database/attention.db`，可通过环境变量 `DATABASE_PATH` 自定义路径。

### 4. AI 分析（可选）

如需 AI 训练评估功能，在 `backend/ai/` 下创建 `.env` 文件：

```
AI_API_KEY=your_api_key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-v4-flash
```

## 核心功能

- **五大注意力维度训练** — 选择性注意、持续性注意、视觉追踪、工作记忆、抑制控制，共 11 个训练游戏
- **实时面部检测** — 基于 MediaPipe FaceLandmarker 的 EAR 眨眼检测、头部姿态估计、专注时长追踪
- **AI 训练评估** — 调用 DeepSeek API 生成训练报告
- **评分引擎** — 五维度加权评分，综合游戏表现与视觉指标
- **家长仪表盘** — Chart.js 可视化训练历史与维度趋势
- **论坛社区** — 帖子/评论/投票/收藏
- **徽章系统** — 游戏成就 + 签到连续天数
- **注意力评估** — 五级测评体系

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python Flask, SQLite, itsdangerous (Token), bcrypt, OpenAI SDK |
| 前端 | 原生 HTML/CSS/JS, Chart.js, MediaPipe FaceLandmarker (CDN) |
| AI | DeepSeek API (OpenAI 兼容接口) |
| 部署 | Gunicorn / uWSGI |

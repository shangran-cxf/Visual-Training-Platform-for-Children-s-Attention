# frontend/ — 前端静态资源层

原生 HTML/CSS/JS，无框架、无构建工具。CSS 内联于各 HTML 文件的 `<style>` 标签中。

## 页面结构

| 文件/目录 | 用途 |
|---|---|
| `index.html` | 首页：登录/注册，灯塔海洋 CSS 动画，卡通云朵眼球交互 |
| `child-home.html` | 儿童训练中心：侧边栏导航，五大维度分类标签，游戏卡片 |
| `child-document.html` | 家长仪表盘：Chart.js 图表，儿童信息、训练统计、成长轨迹 |
| `today-training.html` | 今日训练汇总 |
| `medal-wall.html` | 徽章墙展示 |
| `forum.html` | 论坛帖子列表 |
| `forum-detail.html` | 论坛帖子详情 + 评论区 |
| `about_us.html` | 关于平台 |
| `knowledge.html` | 知识库文章列表 |

## 核心 JS 文件

| 文件 | 职责 |
|---|---|
| `utils.js` | `StorageUtil`（localStorage 封装）、`UserStateUtil`（登录态管理、儿童切换）、`MedalUtil`（游戏勋章、签到勋章、解锁动画） |
| `components-parent.js` | 家长端公共组件：侧边栏、个人信息弹窗、头像上传、密码修改、登出 |
| `attention-loader.js` | IIFE 自动检测游戏/测评页面 → CDN 加载 MediaPipe FaceLandmarker → 注入 floating-ball.js |
| `floating-ball.js` | 实时注意力检测浮球：MediaPipe 468 点面部特征 + EAR 眨眼算法，采集头部位姿、眨眼率、专注时长并上传 |

## 业务逻辑层

| 目录 | 职责 | 详见 |
|---|---|---|
| `api/` | 前端 API 客户端（请求封装、错误处理、训练 API） | [api/README.md](api/README.md) |
| `training/` | 11 个注意力训练游戏 | [training/README.md](training/README.md) |
| `detect/` | 5 级注意力测评 | [detect/README.md](detect/README.md) |
| `assessment/` | 注意力评估表单（儿童自评 + 家长评估） | [assessment/README.md](assessment/README.md) |
| `knowledge/` | 知识库内容（文章 JSON + 管理页面） | [knowledge/README.md](knowledge/README.md) |

## 设计风格

粘土风格（Claymorphism）：圆角、柔和阴影、粉彩渐变、趣味形状。双模式界面：儿童模式（游戏化、活泼色彩）和家长模式（仪表盘、数据面板）。

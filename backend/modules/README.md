# backend/modules/ — API 业务模块

7 个 Flask Blueprint，各自负责一块业务领域。

## 模块列表

| 模块 | Blueprint | 前缀 | 职责 |
|---|---|---|---|
| `auth.py` | `auth_bp` | `/api` | 注册、登录、密码修改、头像上传、个人信息 |
| `children.py` | `children_bp` | `/api` | 儿童的 CRUD、训练统计、最近训练记录 |
| `forum.py` | `forum_bp` | `/api/forum` | 帖子 CRUD、评论、投票、收藏、搜索、置顶/精华、图片上传 |
| `knowledge.py` | `knowledge_bp` | `/api/knowledge` | 知识库文章 CRUD、搜索、标签管理（数据存 JSON 文件） |
| `badges.py` | `badges_bp` | `/api` | 徽章列表、儿童已获徽章、颁发徽章 |
| `admin.py` | `admin_bp` | `/api` | 用户管理（列表、封禁、重置密码、删除）、全量训练数据、统计 |
| `user_stats.py` | `user_stats_bp` | `/api` | 用户等级（论坛经验值）、发帖数、聚合统计 |

## 通用模式

- 所有路由使用 `get_db_connection()` 获取数据库连接
- 响应通过 `response_utils.success_response()` / `error_response()` 统一返回
- 敏感操作（修改/删除）通过 `require_auth` 或 `require_admin` 装饰器保护
- 用户身份通过 `request.user_id` 获取（由中间件注入）

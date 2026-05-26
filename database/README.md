# database/ — 数据库层

SQLite 数据库，通过 `execute_db()` 统一管理连接生命周期。

## 文件说明

| 文件 | 职责 |
|---|---|
| `db.py` | 连接管理，`execute_db(sql, params, fetch)` 执行 SQL 并自动处理 commit/rollback |
| `models.py` | `init_db()` — CREATE TABLE IF NOT EXISTS + ALTER TABLE 增量迁移，首次启动自动调用 |
| `config.py` | 数据库路径配置，默认 `database/attention.db`，可通过 `DATABASE_PATH` 环境变量覆盖 |
| `init.sql` | 完整 SQL 建表脚本（文档用途，不实际执行） |
| `migrate.py` | 旧路径到新路径的数据库迁移工具 |

## 数据表 (12 张)

| 表 | 用途 |
|---|---|
| `parents` | 家长账户（uid, username, password/bcrypt, email, role, level, is_banned） |
| `children` | 儿童档案（parent_id FK, name, age） |
| `forum_posts` | 论坛帖子（title, content, category_id, is_pinned, is_essential, view_count） |
| `forum_comments` | 论坛评论（post_id FK, parent_id FK, content） |
| `forum_votes` | 投票记录（post_id/comment_id, vote_type: 1/-1） |
| `favorites` | 帖子收藏（parent_id, post_id, UNIQUE 约束） |
| `detection_data` | 注意力评估结果（child_id FK, 五维度分数, total_score） |
| `training_sessions` | 训练会话（session_token UUID, status: active/completed/interrupted, duration） |
| `game_raw_data` | 游戏原始数据（session_id FK, event_type, event_data JSON, 各项指标） |
| `vision_raw_data` | 视觉原始数据（session_id FK, head_yaw/pitch, blink_rate, focus_duration） |
| `session_summaries` | 会话汇总（final_score, 12项子分数, performance_level） |
| `child_reports` | 儿童报告（report_type, 五维度分数, percentile, strengths/weaknesses JSON） |
| `processed_requests` | 幂等性追踪（request_id UNIQUE） |

## 初始化流程

1. `app.py` 启动 → 调用 `init_db()`
2. `init_db()` 执行 CREATE TABLE IF NOT EXISTS（所有表）
3. 执行增量 ALTER TABLE（向后兼容旧库）
4. 插入默认管理员 `admin / 123456` 和示例儿童 "小A"

# backend/utils/ — 公共工具

跨模块共享的纯函数和工具类。

## 文件说明

| 文件 | 职责 |
|---|---|
| `db_utils.py` | `build_update_sql(table, data, condition)` — 从 dict 动态构建 UPDATE 语句；`check_user_exists` — 按 id 或 username 查用户；`is_admin` — 检查管理员角色 |
| `error_codes.py` | 17 个符号错误码（`INVALID_PARAMS`、`UNAUTHORIZED`、`NOT_FOUND` 等），每个带中文消息和 HTTP 状态码映射 |
| `password_utils.py` | `hash_password` / `verify_password` — bcrypt 哈希；`is_bcrypt_hash` — 检测 `$2b$`/`$2a$` 前缀，支持旧明文密码自动升级 |
| `response_utils.py` | `success_response(data, message)` → `{success, message, data}`；`error_response(message, code, status)` → `{success, error: {code, message}}` |

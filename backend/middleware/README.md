# backend/middleware/ — 认证中间件

Token 认证机制，保护 API 路由。

## 文件说明

| 文件 | 职责 |
|---|---|
| `auth_middleware.py` | Token 生成、验证、`require_auth` 装饰器、`require_admin` 装饰器 |

## 认证流程

1. **登录** → `generate_token(user_id, role)` 生成 `itsdangerous.URLSafeTimedSerializer` 签名 Token，7 天过期
2. **请求** → `before_request`（app.py）检查 `Authorization: Bearer <token>` 头，验证后注入 `request.user_id` 和 `request.user_role`
3. **公开路径豁免**：`/api/login`、`/api/register`、部分 GET 端点无需 Token
4. **权限校验**：`require_auth` 装饰器要求有效 Token，`require_admin` 装饰器额外检查 `role == 'admin'`

## 使用方式

```python
from middleware.auth_middleware import require_auth, require_admin

@auth_bp.route('/api/protected')
@require_auth
def protected_route():
    user_id = request.user_id  # 中间件注入
    ...

@admin_bp.route('/api/admin/action')
@require_admin
def admin_route():
    ...
```

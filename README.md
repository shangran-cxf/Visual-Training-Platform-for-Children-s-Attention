# Visual-Training-Platform-for-Children-s-Attention

## 项目架构

本项目采用三层分离架构：

```
Visual-Training-Platform-for-Children-s-Attention/
├── frontend/          # 前端层 - 静态资源和页面
├── backend/           # 后端层 - Flask API 服务
└── database/          # 数据库层 - SQLite 数据库
    ├── attention.db   # 数据库文件
    ├── init.sql       # 初始化脚本
    ├── migrate.py     # 迁移工具
    └── config.py      # 数据库配置
```

### 数据库配置

数据库路径可通过环境变量 `DATABASE_PATH` 自定义配置：

```bash
# Windows
set DATABASE_PATH=D:\path\to\your\database.db

# Linux/Mac
export DATABASE_PATH=/path/to/your/database.db
```

默认路径：`项目根目录/database/attention.db`


# frontend/knowledge/ — 知识库

注意力发展相关文章，数据以 JSON 文件存储（非数据库）。

## 文件说明

| 文件 | 用途 |
|---|---|
| `knowledge-data.json` | 文章数据（标题、内容、标签、分类） |
| `admin.html` | 知识库管理后台页面 |
| `templates/article-template.json` | 文章模板 |

## 数据管理

知识库文章通过 `/api/knowledge/articles` API 操作，后端直接读写 `knowledge-data.json` 文件，不经过 SQLite。

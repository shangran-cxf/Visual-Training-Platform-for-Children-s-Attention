# frontend/detect/ — 注意力测评

5 级测评，每级对应一个注意力维度，用于训练前的初始评估。

## 测评列表

| 等级 | 文件 | 对应维度 |
|---|---|---|
| 等级 1 | `level1.html` | 选择性注意 |
| 等级 2 | `level2.html` | 持续性注意 |
| 等级 3 | `level3.html` | 视觉追踪 |
| 等级 4 | `level4.html` | 工作记忆 |
| 等级 5 | `level5.html` | 抑制控制 |

## 测评总览

`index.html` — 测评中心页面，展示五级测评入口。

## 数据流

- 测评结果通过 `/api/upload/detection` 提交
- 可通过 `/api/get/detection` 查询历史测评数据
- 数据存入 `detection_data` 表

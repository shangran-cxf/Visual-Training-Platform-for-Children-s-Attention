# AI 模块评估报告合并与深度优化

## 目标

1. 合并「当前训练评估」和「历史趋势分析」为一个综合报告（前端实际只用了前者）
2. 提升分析深度：从罗列数据变为解读关联、归因趋势、给出可执行建议
3. 适配 DeepSeek JSON Output 模式，提升 JSON 输出稳定性

## 改动范围

### backend/ai/config.py

- 删除 `PROMPT_TEMPLATES["history_training_evaluation"]`
- 重写 `PROMPT_TEMPLATES["current_training_evaluation"]`：
  - system_prompt 增加角色定义和分析原则（关联分析、趋势归因、可执行建议）
  - user_prompt_template 增加 `{trend_data}` 占位符
  - JSON 样例中增加 `trend_analysis` 字段
  - 明确要求 JSON 格式（适配 DeepSeek JSON Output 模式）

### backend/ai/analysis.py

- `call_ai_service()`：
  - `extra_body={"thinking":{"type":"disabled"}}` → `response_format={'type': 'json_object'}`
  - `max_tokens` 从 1000 → 1500
- `generate_current_training_evaluation()`：
  - 数据源增加 `get_training_trend()` 查询
  - Prompt 参数增加 `trend_data=format_trend_data_for_prompt(child_id)`
- 删除 `generate_history_training_evaluation()` 路由函数和 `get_history_evaluation_data()` 辅助函数（仅被该路由使用）
- 删除因上述移除产生的孤立 import

### 不变

- `validator.py`：完整保留
- `/api/ai/status`、`/api/ai/generate`、`/api/ai/training-analysis`：不动
- 前端 localStorage 缓存策略：不动

### frontend/child-document.html

- HTML：在 `ai-home-guidance` 下方增加趋势分析展示区（`ai-trend-analysis`）
- JS `displayEvaluation()`：追加 `trend_analysis` 数组渲染（维度名 + 趋势方向 + 简短分析）
- `generateDataVersion()`：hash 计算包含 trend 数据，保证趋势变化时缓存失效

## 输出 JSON 结构

```json
{
  "summary": "综合总结（40-60字，含趋势变化）",
  "strengths": ["优势（15-50字）", "优势（15-50字）"],
  "weaknesses": ["待提升点（15-50字）", "待提升点（15-50字）"],
  "suggestions": ["具体建议（15-50字）", "具体建议（15-50字）"],
  "home_guidance": "家庭指导（60-150字）",
  "trend_analysis": [
    {"name": "选择性注意", "trend": "上升", "detail": "简短分析（15-40字）"}
  ]
}
```

## 风险

- DeepSeek JSON Output 已知可能返回空 content，`validate_json_response()` 保留作 fallback
- `max_tokens=1500` 需验证截断情况，趋势数据量多时可能不够

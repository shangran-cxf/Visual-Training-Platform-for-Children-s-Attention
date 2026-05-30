# AI 模块评估报告合并与深度优化 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 合并「当前训练评估」和「历史趋势分析」为一个综合报告，提升 Prompt 分析深度，适配 DeepSeek JSON Output 模式。

**Architecture:** 修改 `config.py`（Prompt 模板重写）、`analysis.py`（合并数据源 + JSON Output 模式 + 删除历史路由）、`child-document.html`（前端趋势分析展示）。缓存层不动。

**Tech Stack:** Python Flask, OpenAI SDK (DeepSeek 兼容), JavaScript (原生)

---

### Task 1: 重写 Prompt 模板 + 提高 max_tokens 默认值

**Files:**
- Modify: `backend/ai/config.py`
- Modify: `backend/ai/.env.example`

- [ ] **Step 1: 重写 Prompt 模板，删除 history 模板**

在 `backend/ai/config.py` 中，将 `PROMPT_TEMPLATES` 的 `current_training_evaluation` 替换为以下内容，删除 `history_training_evaluation` 条目：

```python
PROMPT_TEMPLATES = {
    "current_training_evaluation": {
        "name": "训练综合评估报告",
        "system_prompt": (
            "你是一位专业又亲切的儿童注意力训练专家。"
            "请用温暖、专业的语言，为家长提供直观易懂的训练反馈。\n"
            "## 分析原则\n"
            "1. 不罗列数据——解读数据背后的含义，关注维度间的关联"
            "（如工作记忆弱可能影响其他能力的发挥）\n"
            "2. 趋势变化要分析可能原因，不只描述方向\n"
            "3. 每条建议要针对具体数据表现，家长能直接执行\n"
            "你的回答必须是严格的 JSON 格式。"
        ),
        "user_prompt_template": (
            "请根据以下儿童训练数据，为家长生成一份专业、易懂、实用的综合评估报告。\n\n"
            "## 儿童信息\n"
            "姓名：{child_name}，年龄：{child_age}岁\n\n"
            "## 训练数据\n"
            "{training_data}\n\n"
            "## 能力评估\n"
            "{detection_data}\n\n"
            "## 历史趋势（近30天）\n"
            "{trend_data}\n\n"
            "## 输出 JSON 格式\n"
            "{{\n"
            '  "summary": "综合总结（40-60字，含核心发现和趋势变化）",\n'
            '  "strengths": ["优势（15-50字）", "优势（15-50字）"],\n'
            '  "weaknesses": ["待提升点（15-50字）", "待提升点（15-50字）"],\n'
            '  "suggestions": ["具体建议（15-50字）", "具体建议（15-50字）"],\n'
            '  "home_guidance": "家庭指导（60-150字，分点、可执行）",\n'
            '  "trend_analysis": [\n'
            '    {{"name": "维度名", "trend": "上升/下降/稳定", "detail": "简短分析（15-40字）"}}\n'
            "  ]\n"
            "}}\n\n"
            "写作要求：\n"
            "1. 语言亲切自然，像和朋友交流一样\n"
            "2. 每条内容精炼有力，避免冗长重复\n"
            "3. 分析数据间关系而非罗列数字\n"
            "4. 建议具体可操作，家长容易执行"
        ),
    },
}
```

- [ ] **Step 2: 提高 max_tokens 默认值**

在 `backend/ai/config.py` 中，将 `AI_CONFIG` 的 `max_tokens` 默认值从 1000 改为 1500：

```python
# 修改此行:
"max_tokens": int(os.environ.get("AI_MAX_TOKENS", "1500")),
```

在 `backend/ai/.env.example` 中同步：

```
AI_MAX_TOKENS=1500
```

- [ ] **Step 3: Commit**

```bash
git add backend/ai/config.py backend/ai/.env.example
git commit -m "feat: 重写 AI Prompt 模板，合并趋势分析，提升分析深度"
```

---

### Task 2: 后端路由合并 + JSON Output 模式

**Files:**
- Modify: `backend/ai/analysis.py`

- [ ] **Step 1: call_ai_service 切换为 JSON Output 模式**

将 `call_ai_service` 函数中的 `extra_body` 替换为 `response_format`，条件化添加（仅 `expect_json=True` 时）：

```python
def call_ai_service(system_prompt, user_prompt, expect_json=True):
    if not is_ai_configured():
        return None, "AI 服务未配置，请在 backend/ai/.env 中填写 base_url、api_key 和 model"

    try:
        client = OpenAI(
            api_key=AI_CONFIG["api_key"],
            base_url=AI_CONFIG["base_url"],
            timeout=AI_CONFIG["timeout"],
        )

        kwargs = dict(
            model=AI_CONFIG["model"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=AI_CONFIG["max_tokens"],
            temperature=AI_CONFIG["temperature"],
        )

        if expect_json:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)

        content = response.choices[0].message.content

        if expect_json:
            parsed_json, error = validate_json_response(content)
            if error:
                return None, error
            return parsed_json, None
        else:
            return content, None

    except Exception as e:
        return None, f"AI API 调用失败: {str(e)}"
```

- [ ] **Step 2: 删除 history 路由和辅助函数**

删除整个 `generate_history_training_evaluation()` 函数（约 428-504 行）。

删除 `get_history_evaluation_data()` 函数（约 141-150 行）：

```python
# 删除此函数:
def get_history_evaluation_data(child_id, days=30):
    stats = get_child_training_stats(child_id)
    trend = get_child_training_trend(child_id, days)
    ...
```

- [ ] **Step 3: 当前评估路由增加趋势数据**

在 `generate_current_training_evaluation()` 中，数据查询增加趋势数据，传给 Prompt 时增加 `trend_data` 参数：

修改 `get_evaluation_data` 调用为直接构造，增加趋势数据获取。找到 `generate_current_training_evaluation()` 函数体，将其中的：

```python
evaluation_data = get_evaluation_data(child_id)
```

替换为：

```python
trend = get_child_training_trend(child_id)
trend_data_str = format_trend_data_for_prompt(child_id)

evaluation_data = get_evaluation_data(child_id)
evaluation_data["trend"] = trend
```

在 `build_prompt_from_template` 调用中增加 `trend_data` 参数：

```python
prompts, error = build_prompt_from_template(
    "current_training_evaluation",
    child_name=child_info.get("name", "未知"),
    child_age=child_info.get("age", "未知"),
    training_data=format_training_data_for_prompt(child_id),
    detection_data=format_detection_data_for_prompt(child_id),
    trend_data=trend_data_str,
)
```

- [ ] **Step 4: Commit**

```bash
git add backend/ai/analysis.py
git commit -m "feat: 合并评估路由 + 切换 JSON Output 模式"
```

---

### Task 3: 前端趋势分析展示

**Files:**
- Modify: `frontend/child-document.html`

- [ ] **Step 1: HTML 增加趋势分析展示区**

在 `ai-home-guidance` 区域后面添加趋势分析展示区。找到 `<!-- 右下卡片 - 成长轨迹 -->` 上方的 `</div>`（`ai-evaluation-error` 所在 div 的结束标签前一行的 `</div>`），在 `ai-evaluation-content` div 内部、`ai-evaluation-error` 之前插入：

```html
              <div id="ai-trend-section" style="margin-top: 15px">
                <h4 style="color: #343559; margin-bottom: 10px; font-size: 16px">趋势分析</h4>
                <div id="ai-trend-analysis" style="color: #555; line-height: 1.6"></div>
              </div>
```

具体位置：在 `<p id="ai-home-guidance"...></p>` 之后、`</div>`（ai-evaluation-right 结束）之后、`<div id="ai-evaluation-error"` 之前插入。

- [ ] **Step 2: displayEvaluation 增加趋势分析渲染**

在 `displayEvaluation()` 函数的 `ai-home-guidance` 设置之后（约第 819 行），追加趋势分析渲染：

```javascript
        // 展示趋势分析
        const trendSection = document.getElementById('ai-trend-section');
        const trendContainer = document.getElementById('ai-trend-analysis');
        if (evaluation.trend_analysis && evaluation.trend_analysis.length > 0) {
          trendSection.style.display = 'block';
          trendContainer.innerHTML = '';
          evaluation.trend_analysis.forEach((item) => {
            const div = document.createElement('div');
            div.style.marginBottom = '10px';
            const trendIcon = item.trend === '上升' ? '↑' : item.trend === '下降' ? '↓' : '→';
            const trendColor = item.trend === '上升' ? '#4caf50' : item.trend === '下降' ? '#f44336' : '#ff9800';
            div.innerHTML =
              '<span style="font-weight: 600">' +
              item.name +
              '</span> ' +
              '<span style="color: ' +
              trendColor +
              '">' +
              trendIcon +
              ' ' +
              item.trend +
              '</span>' +
              '<br><span style="color: #888; font-size: 13px">' +
              item.detail +
              '</span>';
            trendContainer.appendChild(div);
          });
        } else {
          trendSection.style.display = 'none';
        }
```

- [ ] **Step 3: generateDataVersion 包含趋势数据**

修改 `generateDataVersion()` 函数，在 `versionData` 中增加 `trend` 字段。

先修改 `fetchChildData()` 的返回值，在 `result` 对象中增加 `trend` 字段。找到 `const result = { ... }` 处（约第 677 行），增加：

```javascript
          const result = {
            info: { ... },
            radarData: radarData,
            trend: trend,  // 新增
          };
```

然后修改 `generateDataVersion()` 函数：

```javascript
      function generateDataVersion(childData) {
        if (!childData) return null;

        const info = childData.info || {};
        const radarData = childData.radarData || [];
        const trend = childData.trend || {};

        const versionData = {
          name: info.name,
          time: info.time,
          courses: info.courses,
          level: info.level,
          radarData: radarData.join(','),
          trendKeys: Object.keys(trend.trend || {}).join(','),
        };

        return JSON.stringify(versionData);
      }
```

- [ ] **Step 4: Commit**

```bash
git add frontend/child-document.html
git commit -m "feat: 前端增加 AI 趋势分析展示"
```

---

### Self-Review

1. **Spec coverage:**
   - ✅ Prompt 重写（Task 1）— 增加分析原则 + trend_data + JSON 样例
   - ✅ 删除 history 模板（Task 1）
   - ✅ JSON Output 模式（Task 2）
   - ✅ max_tokens 1000→1500（Task 1）
   - ✅ 合并数据源（Task 2）
   - ✅ 删除 history 路由 + 辅助函数（Task 2）
   - ✅ 前端 HTML + JS（Task 3）
   - ✅ generateDataVersion 含趋势（Task 3）

2. **Placeholder scan:** No TBD, TODO, or vague instructions.

3. **Type consistency:**
   - `evaluation.trend_analysis` — matches JSON output spec field name
   - `childData.trend` — matches existing `fetchChildData` variable name
   - `evaluation_data["trend"]` — used by `generate_data_fingerprint` which already handles `trend` key

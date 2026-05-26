# backend/analytics/ — 数据分析与评分引擎

训练数据的采集、处理、评分和报告生成。

## 文件说明

| 文件 | 职责 |
|---|---|
| `data_collector.py` | 训练会话生命周期管理（start/end/heartbeat/interrupt）、游戏数据和视觉数据上传、训练历史查询、趋势分析、每日汇总。包含 `processed_requests` 幂等性检查 |
| `scoring.py` | 五维度评分函数（`calculate_selective_score` 等）+ `ScoringEngine` 类。综合游戏指标（accuracy, speed, errors）和视觉指标（head_stable, blink_stable, face_stable）通过配置权重计算 0-100 分 |
| `attention_analyzer.py` | `AttentionAnalyzer` 类：综合注意力分数、五维度评估、趋势分析、异常检测（2-sigma 离群值、>30% 骤降）、强弱项识别、游戏推荐 |
| `data_processor.py` | `DataProcessor` 类：数据清洗、会话合并、分数归一化、统计计算、Z-score 离群值检测 |
| `report_generator.py` | `ReportGenerator` 类：注意力报告、进度报告、推荐生成、百分位计算、改善率计算。生成报告存入 `child_reports` 表 |

## 训练会话生命周期

```
POST /api/training/session/start  →  创建会话 (status=active)
POST /api/training/session/heartbeat  →  更新 last_activity
POST /api/training/game-data  →  写入 game_raw_data
POST /api/training/vision-data  →  写入 vision_raw_data
POST /api/training/session/end  →  计算汇总 → 写入 session_summaries → 颁发徽章
POST /api/training/session/interrupt  →  标记中断 (status=interrupted)
```

## 评分体系

5 个注意力类型各有独立的评分函数和权重配置（见 `backend/config.py` 的 `SCORING_WEIGHTS`）：

- **选择性注意** — accuracy, precision, speed, head_stable, blink_stable
- **持续性注意** — accuracy, no_fatigue, head_stable, face_stable, blink_stable
- **视觉追踪** — accuracy, head_stable, face_stable, stable_act, impulse
- **工作记忆** — accuracy, speed, memory, head_stable, blink_stable
- **抑制控制** — accuracy, rt_score, order_score, impulse, blink_stable

绩效等级：excellent (90+), good (75-89), average (50-74), weak (<50)

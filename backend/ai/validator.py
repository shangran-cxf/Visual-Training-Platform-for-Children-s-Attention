import hashlib
import json
from datetime import UTC, timedelta
from typing import Any

from utils.time_utils import now_utc

_report_cache: dict[str, dict[str, Any]] = {}


def is_empty_data(data: dict[str, Any]) -> bool:
    if not data:
        return True

    # 有训练记录即视为有数据，不再要求 detection 必须非零
    if data.get("training_count", 0) > 0:
        return False

    detection = data.get("detection")
    if not detection:
        return True

    scores = [
        detection.get("selective_attention", 0),
        detection.get("sustained_attention", 0),
        detection.get("visual_tracking", 0),
        detection.get("working_memory", 0),
        detection.get("inhibitory_control", 0),
    ]
    return all(score == 0 for score in scores)


def generate_data_fingerprint(data: dict[str, Any]) -> str:
    fingerprint_data = {
        "training_count": data.get("training_count", 0),
        "total_time": data.get("total_time", 0),
        "avg_score": round(data.get("avg_score", 0), 2),
    }

    detection = data.get("detection")
    if detection:
        fingerprint_data["detection"] = {
            "selective_attention": round(detection.get("selective_attention", 0), 4),
            "sustained_attention": round(detection.get("sustained_attention", 0), 4),
            "visual_tracking": round(detection.get("visual_tracking", 0), 4),
            "working_memory": round(detection.get("working_memory", 0), 4),
            "inhibitory_control": round(detection.get("inhibitory_control", 0), 4),
            "total_score": round(detection.get("total_score", 0), 4),
        }

    trend = data.get("trend")
    if trend:
        trend_summary = {}
        for key, records in trend.items():
            if records:
                scores = [r.get("score", 0) for r in records]
                trend_summary[key] = {
                    "count": len(records),
                    "avg": round(sum(scores) / len(scores), 2) if scores else 0,
                }
        fingerprint_data["trend_summary"] = trend_summary

    data_str = json.dumps(fingerprint_data, sort_keys=True)
    return hashlib.md5(data_str.encode()).hexdigest()


def get_cached_report_if_unchanged(
    child_id: int, data: dict[str, Any], cache_config: dict[str, Any], report_type: str = "evaluation"
) -> dict[str, Any] | None:
    if not cache_config.get("enabled", True):
        return None

    cache_key = f"report_{child_id}_{report_type}"
    cached = _report_cache.get(cache_key)

    if not cached:
        return None

    expire_hours = cache_config.get("expire_hours", 24)
    cached_time = cached.get("cached_at")
    if cached_time:
        # 兼容旧缓存中的 naive datetime
        if cached_time.tzinfo is None:
            cached_time = cached_time.replace(tzinfo=UTC)
        expire_time = cached_time + timedelta(hours=expire_hours)
        if now_utc() > expire_time:
            del _report_cache[cache_key]
            return None

    current_fingerprint = generate_data_fingerprint(data)
    cached_fingerprint = cached.get("fingerprint")

    if current_fingerprint == cached_fingerprint:
        return cached.get("report")

    return None


def cache_report(child_id: int, data: dict[str, Any], report: dict[str, Any], report_type: str = "evaluation") -> None:
    cache_key = f"report_{child_id}_{report_type}"

    _report_cache[cache_key] = {
        "fingerprint": generate_data_fingerprint(data),
        "report": report,
        "cached_at": now_utc(),
    }


def get_empty_report(report_type: str = "current_training") -> dict[str, Any]:
    empty_reports = {
        "current_training": {
            "summary": "暂无训练数据，建议先完成至少一次训练后再生成评价报告。",
            "strengths": ["暂无数据"],
            "weaknesses": ["暂无数据"],
            "suggestions": ["请先完成注意力训练测试", "训练后系统将自动生成个性化评价报告"],
            "home_guidance": "建议家长引导孩子每天进行15-20分钟的注意力训练，循序渐进地提升注意力水平。",
            "is_empty_report": True,
        },
        "history_training": {
            "overall_progress": "暂无历史训练数据，无法分析进步趋势。",
            "trend_analysis": [],
            "milestones": ["暂无数据"],
            "recommendations": ["建议定期进行训练以积累数据", "持续训练将帮助系统生成更准确的趋势分析"],
            "encouragement": "开始训练之旅，每一步都是进步！",
            "is_empty_report": True,
        },
        "training_analysis": {
            "analysis": """## 暂无训练数据

目前还没有足够的训练数据来生成详细的评析报告。

### 建议
1. **完成训练测试**：请先完成注意力能力评估测试
2. **定期训练**：建议每周进行2-3次训练
3. **持续记录**：系统将自动记录训练数据并生成报告

完成训练后，系统将为您提供：
- 五大注意力维度的详细分析
- 个性化的训练建议
- 针对性的家庭指导方案""",
            "is_empty_report": True,
        },
    }

    return empty_reports.get(report_type, empty_reports["current_training"])


def clear_cache(child_id: int | None = None) -> None:
    global _report_cache

    if child_id is not None:
        keys_to_delete = [k for k in _report_cache if k.startswith(f"report_{child_id}")]
        for key in keys_to_delete:
            del _report_cache[key]
    else:
        _report_cache.clear()


def get_cache_stats() -> dict[str, Any]:
    return {
        "total_cached": len(_report_cache),
        "cache_keys": list(_report_cache.keys()),
    }

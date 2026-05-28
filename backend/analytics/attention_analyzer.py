import json
import math
import statistics
from datetime import UTC, datetime

from config import (
    ENABLE_CROSS_GAME_NORMALIZATION,
    GAME_SCORE_CALIBRATION,
    TIME_DECAY_HALF_LIFE_DAYS,
)


class AttentionAnalyzer:
    """注意力分析模块 - 专注度算法、趋势分析"""

    GAME_DIMENSION_MAP = {
        "schulte": ["selective_attention", "sustained_attention"],
        "find-numbers": ["selective_attention", "visual_tracking"],
        "card-matching": ["working_memory", "sustained_attention"],
        "reverse-memory": ["working_memory"],
        "traffic-light": ["inhibitory_control", "sustained_attention"],
        "command-adventure": ["inhibitory_control"],
        "magic-maze": ["visual_tracking", "sustained_attention"],
        "sun-tracking": ["visual_tracking"],
        "animal-searching": ["selective_attention", "visual_tracking"],
        "water-plants": ["sustained_attention", "inhibitory_control"],
    }

    DIMENSION_NAMES = {
        "selective_attention": "选择性注意力",
        "sustained_attention": "持续性注意力",
        "visual_tracking": "视觉追踪",
        "working_memory": "工作记忆",
        "inhibitory_control": "抑制控制",
    }

    PERFORMANCE_LEVELS = {(90, 100): "优秀", (75, 89.99): "良好", (50, 74.99): "一般", (0, 49.99): "较弱"}

    @staticmethod
    def _compute_decay_weight(session_date_str, reference_date=None, half_life_days=None):
        """Exponential time decay. A session half_life_days old gets 50% weight."""
        if half_life_days is None:
            half_life_days = TIME_DECAY_HALF_LIFE_DAYS
        if not session_date_str:
            return 1.0
        if reference_date is None:
            reference_date = datetime.now(UTC)
        try:
            if isinstance(session_date_str, str):
                session_date_str = session_date_str.replace("Z", "+00:00")
                session_date = datetime.fromisoformat(session_date_str)
                if session_date.tzinfo is None:
                    session_date = session_date.replace(tzinfo=UTC)
            else:
                session_date = session_date_str
            days_ago = (reference_date - session_date).total_seconds() / 86400
            if days_ago < 0:
                days_ago = 0
            return math.pow(0.5, days_ago / half_life_days)
        except Exception:
            return 1.0

    @staticmethod
    def _weighted_mean(values, weights):
        """Weighted mean. Falls back to simple mean when weights sum to 0."""
        if not values or not weights:
            return 0.0
        total_weight = sum(weights)
        if total_weight == 0:
            return sum(values) / len(values)
        return sum(v * w for v, w in zip(values, weights, strict=False)) / total_weight

    @staticmethod
    def _normalize_score(raw_score, game_type):
        """Convert raw score to T-score (mean=50, std=10) using per-game calibration."""
        if not ENABLE_CROSS_GAME_NORMALIZATION:
            return raw_score
        calib = GAME_SCORE_CALIBRATION.get(game_type)
        if not calib or calib.get("std", 0) == 0:
            return raw_score
        z_score = (raw_score - calib["mean"]) / calib["std"]
        t_score = 50 + z_score * 10
        return max(0.0, min(100.0, t_score))

    @staticmethod
    def calculate_attention_score(vision_data: dict, game_data: dict) -> float:
        """计算专注度综合评分（0-100）

        Args:
            vision_data: 视觉指标数据
                - head_stability: 头部稳定性 (0-100)
                - focus_duration: 注视持续时间 (秒)
                - blink_rate: 眨眼频率 (次/分钟)
                - screen_distance: 屏幕距离 (厘米)
            game_data: 游戏表现数据
                - accuracy: 正确率 (0-100)
                - reaction_speed: 反应速度评分 (0-100)
                - completion_rate: 完成度 (0-100)

        Returns:
            综合评分 (0-100)
        """
        visual_score = 0.0
        game_score = 0.0

        head_stability = vision_data.get("head_stability", 70)
        if head_stability is not None:
            visual_score += head_stability * 0.2

        focus_duration = vision_data.get("focus_duration", 0)
        focus_quality = min(100, (focus_duration / 30) * 100) if focus_duration else 50
        visual_score += focus_quality * 0.2

        blink_rate = vision_data.get("blink_rate", 15)
        if blink_rate is not None:
            normal_blink_range = (10, 20)
            if normal_blink_range[0] <= blink_rate <= normal_blink_range[1]:
                blink_score = 100
            elif blink_rate < normal_blink_range[0]:
                blink_score = max(0, 100 - (normal_blink_range[0] - blink_rate) * 5)
            else:
                blink_score = max(0, 100 - (blink_rate - normal_blink_range[1]) * 5)
            visual_score += blink_score * 0.1

        screen_distance = vision_data.get("screen_distance", 50)
        if screen_distance is not None:
            ideal_distance = 50
            distance_deviation = abs(screen_distance - ideal_distance)
            distance_score = max(0, 100 - distance_deviation * 2)
            visual_score += distance_score * 0.1

        accuracy = game_data.get("accuracy", 0)
        if accuracy is not None:
            game_score += accuracy * 0.2

        reaction_speed = game_data.get("reaction_speed", 50)
        if reaction_speed is not None:
            game_score += reaction_speed * 0.1

        completion_rate = game_data.get("completion_rate", 0)
        if completion_rate is not None:
            game_score += completion_rate * 0.1

        total_score = visual_score + game_score
        return round(min(100, max(0, total_score)), 2)

    @staticmethod
    def assess_five_dimensions(sessions_data: list) -> dict:
        """评估五维注意力能力（带时间衰减、跨游戏归一化、多维度拆分）

        Args:
            sessions_data: 训练会话数据列表，每个元素包含:
                - game_type: 游戏类型
                - overall_score: 综合评分
                - accuracy: 正确率
                - attention_stability: 注意力稳定性
                - dimension_contributions: JSON字符串或dict (新会话)
                - normalized_score: 跨游戏归一化分 (新会话)
                - date / created_at: 会话日期 (用于时间衰减)

        Returns:
            五维注意力评分字典
        """
        dimension_scores = {
            "selective_attention": [],
            "sustained_attention": [],
            "visual_tracking": [],
            "working_memory": [],
            "inhibitory_control": [],
        }
        dimension_weights = {
            "selective_attention": [],
            "sustained_attention": [],
            "visual_tracking": [],
            "working_memory": [],
            "inhibitory_control": [],
        }

        for session in sessions_data:
            game_type = session.get("game_type")
            if not game_type:
                continue

            score = session.get("overall_score", 0)

            # Prefer normalized_score, fall back to raw overall_score
            normalized = session.get("normalized_score")
            base_score = normalized if normalized is not None else AttentionAnalyzer._normalize_score(score, game_type)

            # Time decay weight
            session_date = session.get("created_at") or session.get("date")
            decay_weight = AttentionAnalyzer._compute_decay_weight(session_date)

            # Resolve dimension contributions
            contributions_raw = session.get("dimension_contributions")
            if contributions_raw:
                if isinstance(contributions_raw, str):
                    try:
                        contributions = json.loads(contributions_raw)
                    except (json.JSONDecodeError, TypeError):
                        contributions = None
                else:
                    contributions = contributions_raw

            if contributions:
                for dim, fraction in contributions.items():
                    if dim in dimension_scores:
                        dimension_scores[dim].append(base_score * fraction)
                        dimension_weights[dim].append(decay_weight * fraction)
            else:
                # Legacy: binary GAME_DIMENSION_MAP with full score per dimension
                dimensions = AttentionAnalyzer.GAME_DIMENSION_MAP.get(game_type, [])
                for dim in dimensions:
                    if dim in dimension_scores:
                        dimension_scores[dim].append(base_score)
                        dimension_weights[dim].append(decay_weight)

        result = {}
        for dimension in dimension_scores:
            scores = dimension_scores[dimension]
            weights = dimension_weights[dimension]
            if scores:
                result[dimension] = round(AttentionAnalyzer._weighted_mean(scores, weights), 2)
            else:
                result[dimension] = 0.0

        return result

    @staticmethod
    def analyze_trend(historical_data: list) -> dict:
        """分析注意力趋势（带时间衰减）

        Args:
            historical_data: 历史训练数据列表，按时间排序，每个元素包含:
                - date: 日期
                - overall_score: 综合评分
                - accuracy: 正确率

        Returns:
            趋势分析结果
        """
        if not historical_data or len(historical_data) < 2:
            return {"trend": "stable", "change_rate": 0.0, "description": "数据不足，无法分析趋势"}

        scores = [d.get("overall_score", 0) for d in historical_data]
        dates = [d.get("date") or d.get("created_at") for d in historical_data]
        weights = [AttentionAnalyzer._compute_decay_weight(d) for d in dates]

        if len(scores) >= 3:
            recent_scores = scores[-3:]
            recent_weights = weights[-3:]
            earlier_scores = scores[:-3] if len(scores) > 3 else scores[:1]
            earlier_weights = weights[:-3] if len(weights) > 3 else weights[:1]

            recent_avg = AttentionAnalyzer._weighted_mean(recent_scores, recent_weights)
            earlier_avg = AttentionAnalyzer._weighted_mean(earlier_scores, earlier_weights)

            change_rate = 0.0 if earlier_avg == 0 else (recent_avg - earlier_avg) / earlier_avg * 100

            if change_rate > 5:
                trend = "improving"
                description = "注意力表现呈上升趋势，继续保持！"
            elif change_rate < -5:
                trend = "declining"
                description = "注意力表现有所下降，建议加强训练"
            else:
                trend = "stable"
                description = "注意力表现稳定"
        else:
            first_score = scores[0]
            last_score = scores[-1]

            change_rate = 0.0 if first_score == 0 else (last_score - first_score) / first_score * 100

            if change_rate > 5:
                trend = "improving"
                description = "注意力表现呈上升趋势"
            elif change_rate < -5:
                trend = "declining"
                description = "注意力表现有所下降"
            else:
                trend = "stable"
                description = "注意力表现稳定"

        overall_avg = AttentionAnalyzer._weighted_mean(scores, weights)

        return {
            "trend": trend,
            "change_rate": round(change_rate, 2),
            "description": description,
            "recent_average": round(AttentionAnalyzer._weighted_mean(scores[-3:], weights[-3:]), 2)
            if len(scores) >= 3
            else round(overall_avg, 2),
            "overall_average": round(overall_avg, 2),
        }

    @staticmethod
    def detect_anomalies(session_data: list) -> list:
        """检测异常模式

        Args:
            session_data: 训练会话数据列表，每个元素包含:
                - session_id: 会话ID
                - overall_score: 综合评分
                - accuracy: 正确率
                - attention_stability: 注意力稳定性
                - date: 日期
                - game_type: 游戏类型

        Returns:
            异常事件列表
        """
        anomalies = []

        if not session_data:
            return anomalies

        scores = [s.get("overall_score", 0) for s in session_data]

        if len(scores) >= 3:
            mean_score = statistics.mean(scores)
            std_score = statistics.stdev(scores) if len(scores) > 1 else 0

            for _i, session in enumerate(session_data):
                score = session.get("overall_score", 0)

                if std_score > 0 and abs(score - mean_score) > 2 * std_score:
                    anomaly = {
                        "type": "score_outlier",
                        "session_id": session.get("session_id"),
                        "score": score,
                        "expected_range": f"{round(mean_score - std_score, 2)} - {round(mean_score + std_score, 2)}",
                        "severity": "high" if abs(score - mean_score) > 3 * std_score else "medium",
                        "description": f"评分{'异常偏高' if score > mean_score else '异常偏低'}，偏离正常范围",
                    }
                    anomalies.append(anomaly)

        for i in range(1, len(session_data)):
            prev_score = session_data[i - 1].get("overall_score", 0)
            curr_score = session_data[i].get("overall_score", 0)

            if prev_score > 0:
                drop_rate = ((prev_score - curr_score) / prev_score) * 100

                if drop_rate > 30:
                    anomaly = {
                        "type": "sudden_drop",
                        "session_id": session_data[i].get("session_id"),
                        "previous_score": prev_score,
                        "current_score": curr_score,
                        "drop_rate": round(drop_rate, 2),
                        "severity": "high" if drop_rate > 50 else "medium",
                        "description": f"注意力评分突然下降{round(drop_rate, 1)}%，可能存在干扰因素",
                    }
                    anomalies.append(anomaly)

        for session in session_data:
            stability = session.get("attention_stability", 100)

            if stability < 50:
                anomaly = {
                    "type": "low_stability",
                    "session_id": session.get("session_id"),
                    "stability": stability,
                    "severity": "high" if stability < 30 else "medium",
                    "description": f"注意力稳定性较低({stability}%)，训练过程中注意力波动较大",
                }
                anomalies.append(anomaly)

        for session in session_data:
            accuracy = session.get("accuracy", 100)
            score = session.get("overall_score", 0)

            if accuracy < 50 and score > 70:
                anomaly = {
                    "type": "accuracy_score_mismatch",
                    "session_id": session.get("session_id"),
                    "accuracy": accuracy,
                    "score": score,
                    "severity": "low",
                    "description": "正确率较低但评分较高，可能存在数据异常",
                }
                anomalies.append(anomaly)

        return anomalies

    @staticmethod
    def get_performance_level(score: float) -> str:
        """根据分数获取表现等级

        Args:
            score: 评分 (0-100)

        Returns:
            表现等级描述
        """
        if score >= 90:
            return "优秀"
        elif score >= 75:
            return "良好"
        elif score >= 50:
            return "一般"
        else:
            return "较弱"

    @staticmethod
    def get_dimension_strengths_weaknesses(dimension_scores: dict) -> dict:
        """分析维度优势和劣势

        Args:
            dimension_scores: 五维注意力评分字典

        Returns:
            包含优势和劣势的分析结果
        """
        if not dimension_scores:
            return {"strengths": [], "weaknesses": []}

        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)

        strengths = []
        weaknesses = []

        for dimension, score in sorted_dimensions[:2]:
            if score >= 70:
                strengths.append(
                    {
                        "dimension": dimension,
                        "name": AttentionAnalyzer.DIMENSION_NAMES.get(dimension, dimension),
                        "score": score,
                        "level": AttentionAnalyzer.get_performance_level(score),
                    }
                )

        for dimension, score in sorted_dimensions[-2:]:
            if score < 60:
                weaknesses.append(
                    {
                        "dimension": dimension,
                        "name": AttentionAnalyzer.DIMENSION_NAMES.get(dimension, dimension),
                        "score": score,
                        "level": AttentionAnalyzer.get_performance_level(score),
                    }
                )

        return {"strengths": strengths, "weaknesses": weaknesses}

    @staticmethod
    def recommend_games(dimension_scores: dict, played_games: list = None) -> list:
        """根据维度评分推荐游戏

        Args:
            dimension_scores: 五维注意力评分字典
            played_games: 已玩过的游戏列表

        Returns:
            推荐游戏列表
        """
        if not dimension_scores:
            return []

        sorted_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])

        weakest_dimensions = [d[0] for d in sorted_dimensions[:2]]

        game_recommendations = []
        played_games = played_games or []

        for game_type, dimensions in AttentionAnalyzer.GAME_DIMENSION_MAP.items():
            match_count = sum(1 for d in weakest_dimensions if d in dimensions)

            if match_count > 0:
                avg_dimension_score = statistics.mean([dimension_scores.get(d, 0) for d in dimensions])

                game_recommendations.append(
                    {
                        "game_type": game_type,
                        "dimensions": dimensions,
                        "dimension_names": [AttentionAnalyzer.DIMENSION_NAMES.get(d, d) for d in dimensions],
                        "match_score": match_count,
                        "avg_dimension_score": round(avg_dimension_score, 2),
                        "priority": "high" if avg_dimension_score < 60 else "medium",
                        "played": game_type in played_games,
                    }
                )

        game_recommendations.sort(key=lambda x: (-x["match_score"], x["avg_dimension_score"]))

        return game_recommendations[:5]

    @staticmethod
    def calculate_improvement_rate(recent_scores: list, previous_scores: list) -> dict:
        """计算改进率

        Args:
            recent_scores: 近期评分列表
            previous_scores: 之前评分列表

        Returns:
            改进率分析结果
        """
        if not recent_scores or not previous_scores:
            return {"improvement_rate": 0.0, "trend": "stable", "description": "数据不足"}

        recent_avg = statistics.mean(recent_scores)
        previous_avg = statistics.mean(previous_scores)

        improvement_rate = 0.0 if previous_avg == 0 else (recent_avg - previous_avg) / previous_avg * 100

        if improvement_rate > 10:
            trend = "significant_improvement"
            description = "进步显著，继续保持！"
        elif improvement_rate > 0:
            trend = "improvement"
            description = "有所进步，继续努力！"
        elif improvement_rate > -10:
            trend = "stable"
            description = "表现稳定"
        else:
            trend = "decline"
            description = "需要加强训练"

        return {
            "improvement_rate": round(improvement_rate, 2),
            "recent_average": round(recent_avg, 2),
            "previous_average": round(previous_avg, 2),
            "trend": trend,
            "description": description,
        }

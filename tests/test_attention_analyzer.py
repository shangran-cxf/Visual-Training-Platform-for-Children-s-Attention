from analytics.attention_analyzer import AttentionAnalyzer


class TestCalculateAttentionScore:
    def test_perfect_scores(self, sample_vision_data, sample_game_data):
        vision = {"head_stability": 100, "focus_duration": 30, "blink_rate": 15, "screen_distance": 50}
        game = {"accuracy": 100, "reaction_speed": 100, "completion_rate": 100}
        score = AttentionAnalyzer.calculate_attention_score(vision, game)
        assert score == 100.0

    def test_minimum_scores(self):
        vision = {"head_stability": 0, "focus_duration": 0, "blink_rate": 0, "screen_distance": 0}
        game = {"accuracy": 0, "reaction_speed": 0, "completion_rate": 0}
        score = AttentionAnalyzer.calculate_attention_score(vision, game)
        assert score >= 0

    def test_typical_scores(self, sample_vision_data, sample_game_data):
        score = AttentionAnalyzer.calculate_attention_score(sample_vision_data, sample_game_data)
        assert 0 <= score <= 100

    def test_missing_keys_defaults(self):
        score = AttentionAnalyzer.calculate_attention_score({}, {})
        assert 0 <= score <= 100

    def test_blink_rate_too_low_penalizes(self):
        normal = AttentionAnalyzer.calculate_attention_score({"blink_rate": 15}, {"accuracy": 80})
        low = AttentionAnalyzer.calculate_attention_score({"blink_rate": 2}, {"accuracy": 80})
        assert low < normal

    def test_blink_rate_too_high_penalizes(self):
        normal = AttentionAnalyzer.calculate_attention_score({"blink_rate": 15}, {"accuracy": 80})
        high = AttentionAnalyzer.calculate_attention_score({"blink_rate": 40}, {"accuracy": 80})
        assert high < normal

    def test_screen_distance_deviation_penalizes(self):
        ideal = AttentionAnalyzer.calculate_attention_score({"screen_distance": 50}, {"accuracy": 80})
        far = AttentionAnalyzer.calculate_attention_score({"screen_distance": 80}, {"accuracy": 80})
        assert far < ideal

    def test_score_clamped_to_100(self):
        vision = {"head_stability": 200, "focus_duration": 100, "blink_rate": 15, "screen_distance": 50}
        game = {"accuracy": 200, "reaction_speed": 200, "completion_rate": 200}
        score = AttentionAnalyzer.calculate_attention_score(vision, game)
        assert score <= 100


class TestAssessFiveDimensions:
    def test_all_dimensions_covered(self, sample_sessions):
        result = AttentionAnalyzer.assess_five_dimensions(sample_sessions)
        assert "selective_attention" in result
        assert "sustained_attention" in result

    def test_empty_sessions_returns_zeros(self):
        result = AttentionAnalyzer.assess_five_dimensions([])
        for v in result.values():
            assert v == 0.0

    def test_unknown_game_type_ignored(self):
        sessions = [{"game_type": "unknown-game", "overall_score": 100, "accuracy": 100, "attention_stability": 100}]
        result = AttentionAnalyzer.assess_five_dimensions(sessions)
        assert all(v == 0.0 for v in result.values())

    def test_scores_are_weighted(self, sample_sessions):
        result = AttentionAnalyzer.assess_five_dimensions(sample_sessions)
        for v in result.values():
            assert 0 <= v <= 100


class TestAnalyzeTrend:
    def test_improving_trend(self):
        data = [
            {"overall_score": 50},
            {"overall_score": 55},
            {"overall_score": 60},
            {"overall_score": 70},
            {"overall_score": 80},
        ]
        result = AttentionAnalyzer.analyze_trend(data)
        assert result["trend"] == "improving"
        assert result["change_rate"] > 0

    def test_declining_trend(self):
        data = [
            {"overall_score": 80},
            {"overall_score": 75},
            {"overall_score": 70},
            {"overall_score": 60},
            {"overall_score": 50},
        ]
        result = AttentionAnalyzer.analyze_trend(data)
        assert result["trend"] == "declining"
        assert result["change_rate"] < 0

    def test_stable_trend(self):
        data = [
            {"overall_score": 70},
            {"overall_score": 72},
            {"overall_score": 71},
            {"overall_score": 70},
            {"overall_score": 73},
        ]
        result = AttentionAnalyzer.analyze_trend(data)
        assert result["trend"] == "stable"

    def test_insufficient_data(self):
        result = AttentionAnalyzer.analyze_trend([])
        assert result["trend"] == "stable"
        assert "数据不足" in result["description"]

        result2 = AttentionAnalyzer.analyze_trend([{"overall_score": 50}])
        assert result2["trend"] == "stable"
        assert "数据不足" in result2["description"]

    def test_two_data_points(self):
        data = [{"overall_score": 50}, {"overall_score": 80}]
        result = AttentionAnalyzer.analyze_trend(data)
        assert result["trend"] in ("improving", "declining", "stable")
        assert "change_rate" in result


class TestDetectAnomalies:
    def test_empty_data_no_anomalies(self):
        anomalies = AttentionAnalyzer.detect_anomalies([])
        assert anomalies == []

    def test_score_outlier_detected(self):
        sessions = [
            {"session_id": 1, "overall_score": 70, "accuracy": 80, "attention_stability": 70},
            {"session_id": 2, "overall_score": 72, "accuracy": 85, "attention_stability": 75},
            {"session_id": 3, "overall_score": 71, "accuracy": 75, "attention_stability": 70},
            {"session_id": 4, "overall_score": 68, "accuracy": 70, "attention_stability": 65},
            {"session_id": 5, "overall_score": 69, "accuracy": 72, "attention_stability": 72},
            {"session_id": 6, "overall_score": 73, "accuracy": 78, "attention_stability": 68},
            {"session_id": 7, "overall_score": -50, "accuracy": 80, "attention_stability": 80},
        ]
        anomalies = AttentionAnalyzer.detect_anomalies(sessions)
        types = {a["type"] for a in anomalies}
        assert "score_outlier" in types
        anomalies = AttentionAnalyzer.detect_anomalies(sessions)
        types = {a["type"] for a in anomalies}
        assert "score_outlier" in types

    def test_sudden_drop_detected(self):
        sessions = [
            {"session_id": 1, "overall_score": 80, "accuracy": 80, "attention_stability": 80},
            {"session_id": 2, "overall_score": 40, "accuracy": 40, "attention_stability": 40},
        ]
        anomalies = AttentionAnalyzer.detect_anomalies(sessions)
        types = {a["type"] for a in anomalies}
        assert "sudden_drop" in types

    def test_low_stability_detected(self):
        sessions = [
            {"session_id": 1, "overall_score": 60, "accuracy": 60, "attention_stability": 30},
        ]
        anomalies = AttentionAnalyzer.detect_anomalies(sessions)
        types = {a["type"] for a in anomalies}
        assert "low_stability" in types

    def test_accuracy_score_mismatch_detected(self):
        sessions = [
            {"session_id": 1, "overall_score": 85, "accuracy": 30, "attention_stability": 70},
        ]
        anomalies = AttentionAnalyzer.detect_anomalies(sessions)
        types = {a["type"] for a in anomalies}
        assert "accuracy_score_mismatch" in types


class TestGetPerformanceLevel:
    def test_excellent(self):
        assert AttentionAnalyzer.get_performance_level(95) == "优秀"

    def test_good(self):
        assert AttentionAnalyzer.get_performance_level(80) == "良好"

    def test_average(self):
        assert AttentionAnalyzer.get_performance_level(65) == "一般"

    def test_needs_improvement(self):
        assert AttentionAnalyzer.get_performance_level(40) == "需改进"

    def test_boundary_good(self):
        assert AttentionAnalyzer.get_performance_level(90) == "优秀"

    def test_boundary_average(self):
        assert AttentionAnalyzer.get_performance_level(75) == "良好"


class TestDimensionStrengthsWeaknesses:
    def test_strengths_and_weaknesses(self):
        scores = {
            "selective_attention": 85,
            "sustained_attention": 45,
            "visual_tracking": 72,
            "working_memory": 40,
            "inhibitory_control": 68,
        }
        result = AttentionAnalyzer.get_dimension_strengths_weaknesses(scores)
        assert len(result["strengths"]) >= 1
        assert len(result["weaknesses"]) >= 1
        assert result["strengths"][0]["score"] >= 70
        assert result["weaknesses"][0]["score"] < 60

    def test_all_strong(self):
        scores = {d: 85 for d in AttentionAnalyzer.DIMENSION_NAMES}
        result = AttentionAnalyzer.get_dimension_strengths_weaknesses(scores)
        assert len(result["weaknesses"]) == 0

    def test_all_weak(self):
        scores = {d: 35 for d in AttentionAnalyzer.DIMENSION_NAMES}
        result = AttentionAnalyzer.get_dimension_strengths_weaknesses(scores)
        assert len(result["strengths"]) == 0

    def test_empty_scores(self):
        result = AttentionAnalyzer.get_dimension_strengths_weaknesses({})
        assert result["strengths"] == []
        assert result["weaknesses"] == []


class TestRecommendGames:
    def test_recommends_for_weak_dimensions(self):
        scores = {
            "selective_attention": 40,
            "sustained_attention": 80,
            "visual_tracking": 75,
            "working_memory": 35,
            "inhibitory_control": 70,
        }
        recs = AttentionAnalyzer.recommend_games(scores)
        assert len(recs) >= 1
        assert len(recs) <= 5

    def test_empty_scores(self):
        recs = AttentionAnalyzer.recommend_games({})
        assert recs == []

    def test_played_games_marked(self):
        scores = {
            "selective_attention": 40,
            "sustained_attention": 80,
            "visual_tracking": 75,
            "working_memory": 85,
            "inhibitory_control": 70,
        }
        recs = AttentionAnalyzer.recommend_games(scores, played_games=["schulte"])
        for r in recs:
            if r["game_type"] == "schulte":
                assert r["played"] is True


class TestCalculateImprovementRate:
    def test_significant_improvement(self):
        result = AttentionAnalyzer.calculate_improvement_rate([80, 85, 90], [50, 55, 60])
        assert result["trend"] == "significant_improvement"
        assert result["improvement_rate"] > 10

    def test_decline(self):
        result = AttentionAnalyzer.calculate_improvement_rate([50, 55, 60], [80, 85, 90])
        assert result["trend"] == "decline"
        assert result["improvement_rate"] < -10

    def test_stable(self):
        result = AttentionAnalyzer.calculate_improvement_rate([70, 70, 70], [70, 70, 70])
        assert result["trend"] == "stable"

    def test_empty_data(self):
        result = AttentionAnalyzer.calculate_improvement_rate([], [70, 80])
        assert result["trend"] == "stable"
        assert "数据不足" in result["description"]

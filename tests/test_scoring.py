from analytics.scoring import (
    calculate_blink_stable,
    calculate_face_stable,
    calculate_head_stable,
    calculate_inhibitory_score,
    calculate_memory_score,
    calculate_score,
    calculate_selective_score,
    calculate_std,
    calculate_sustained_score,
    calculate_tracking_score,
    calculate_vision_scores,
    clamp,
    get_performance_level,
)


class TestClamp:
    def test_within_range(self):
        assert clamp(0.5) == 0.5

    def test_below_min(self):
        assert clamp(-0.5) == 0

    def test_above_max(self):
        assert clamp(1.5) == 1

    def test_none_value(self):
        assert clamp(None) == 0

    def test_custom_range(self):
        assert clamp(150, 0, 100) == 100
        assert clamp(-10, 0, 100) == 0


class TestCalculateStd:
    def test_normal_case(self):
        result = calculate_std([2, 4, 4, 4, 5, 5, 7, 9])
        assert result == 2.0

    def test_single_value(self):
        assert calculate_std([5]) == 0.0

    def test_empty_list(self):
        assert calculate_std([]) == 0.0


class TestCalculateHeadStable:
    def test_perfect_stability(self):
        result = calculate_head_stable([0, 0, 0], [0, 0, 0])
        assert result == 1.0

    def test_moderate_movement(self):
        result = calculate_head_stable([5, 10, 5, 10], [5, 10, 5, 10])
        assert 0 < result < 1

    def test_empty_lists(self):
        assert calculate_head_stable([], []) == 0.0


class TestCalculateFaceStable:
    def test_constant_distance(self):
        result = calculate_face_stable([50, 50, 50])
        assert result == 1.0

    def test_single_value(self):
        result = calculate_face_stable([50])
        assert result == 1.0

    def test_empty_list(self):
        assert calculate_face_stable([]) == 1.0


class TestCalculateBlinkStable:
    def test_no_blinks(self):
        result = calculate_blink_stable([0, 0, 0])
        assert result == 0.5

    def test_high_blink_rate(self):
        result = calculate_blink_stable([20, 25, 30])
        assert result < 0.5

    def test_empty_list(self):
        assert calculate_blink_stable([]) == 1.0

    def test_moderate_blink_rate(self):
        result = calculate_blink_stable([1, 2, 1, 2])
        assert 0 <= result <= 1


class TestCalculateSelectiveScore:
    def test_perfect_score(self):
        game = {"correct": 10, "error": 0, "miss": 0, "time": 0, "total_target": 10}
        vision = {"head_stable": 1.0, "blink_stable": 1.0}
        result = calculate_selective_score(game, vision)
        assert result["final_score"] == 100

    def test_poor_score(self):
        game = {"correct": 0, "error": 10, "miss": 10, "time": 120, "total_target": 10}
        vision = {"head_stable": 0.0, "blink_stable": 0.0}
        result = calculate_selective_score(game, vision)
        assert result["final_score"] == 0

    def test_zero_total_target(self):
        game = {"correct": 0, "error": 0, "miss": 0, "time": 30, "total_target": 0}
        vision = {"head_stable": 0.5, "blink_stable": 0.5}
        result = calculate_selective_score(game, vision)
        assert 0 <= result["final_score"] <= 100


class TestCalculateSustainedScore:
    def test_perfect_score(self):
        game = {"correct": 10, "error": 0, "leave": 0, "time": 0, "total_step": 10, "late_error_ratio": 0}
        vision = {"head_stable": 1.0, "blink_stable": 1.0}
        result = calculate_sustained_score(game, vision)
        assert result["final_score"] == 100

    def test_zero_total_step(self):
        game = {"correct": 0, "error": 0, "leave": 0, "time": 0, "total_step": 0, "late_error_ratio": 0}
        vision = {"head_stable": 0.5, "blink_stable": 0.5}
        result = calculate_sustained_score(game, vision)
        assert 0 <= result["final_score"] <= 100


class TestCalculateTrackingScore:
    def test_perfect_score(self):
        game = {"correct": 10, "error": 0, "time": 0, "total_click": 10, "mean_rt": 0}
        vision = {"head_stable": 1.0, "blink_stable": 1.0, "face_stable": 1.0}
        result = calculate_tracking_score(game, vision)
        assert result["final_score"] == 100

    def test_zero_total_click(self):
        game = {"correct": 0, "error": 0, "time": 30, "total_click": 0, "mean_rt": 500}
        vision = {"head_stable": 0.5, "face_stable": 0.5}
        result = calculate_tracking_score(game, vision)
        assert 0 <= result["final_score"] <= 100


class TestCalculateMemoryScore:
    def test_perfect_score(self):
        game = {"correct": 10, "error": 0, "time": 0, "memory_load": 10, "order_error": 0}
        vision = {"head_stable": 1.0, "blink_stable": 1.0}
        result = calculate_memory_score(game, vision)
        assert result["final_score"] == 100

    def test_zero_memory_load(self):
        game = {"correct": 0, "error": 0, "time": 30, "memory_load": 0, "order_error": 0}
        vision = {"head_stable": 0.5, "blink_stable": 0.5}
        result = calculate_memory_score(game, vision)
        assert 0 <= result["final_score"] <= 100


class TestCalculateInhibitoryScore:
    def test_perfect_score(self):
        game = {"correct": 10, "error": 0, "obstacle": 0, "total_trial": 10}
        vision = {"head_stable": 1.0, "face_stable": 1.0, "blink_stable": 1.0}
        result = calculate_inhibitory_score(game, vision)
        assert result["final_score"] == 100

    def test_zero_total_trial(self):
        game = {"correct": 0, "error": 0, "obstacle": 0, "total_trial": 0}
        vision = {"head_stable": 0.5, "face_stable": 0.5, "blink_stable": 0.5}
        result = calculate_inhibitory_score(game, vision)
        assert 0 <= result["final_score"] <= 100


class TestGetPerformanceLevel:
    def test_excellent(self):
        assert get_performance_level(95) == "优秀"

    def test_good(self):
        assert get_performance_level(80) == "良好"

    def test_average(self):
        assert get_performance_level(60) == "一般"

    def test_weak(self):
        assert get_performance_level(30) == "较弱"


class TestCalculateScore:
    def test_known_type(self):
        game = {"correct": 10, "error": 0, "miss": 0, "time": 0, "total_target": 10}
        vision = {"head_stable": 1.0, "blink_stable": 1.0}
        result = calculate_score("selective", game, vision)
        assert "final_score" in result
        assert "performance_level" in result

    def test_unknown_type(self):
        result = calculate_score("nonexistent", {}, {})
        assert result["final_score"] == 0
        assert "未知" in result["error"]

    def test_uses_default_game_data(self):
        result = calculate_score("selective", {}, {"head_stable": 0.5, "blink_stable": 0.5})
        assert "final_score" in result
        assert "performance_level" in result


class TestCalculateVisionScores:
    def test_typical_data(self):
        data = [
            {"head_yaw": 2, "head_pitch": 1, "face_distance": 50, "blink_count": 3},
            {"head_yaw": 2.5, "head_pitch": 1.5, "face_distance": 51, "blink_count": 4},
            {"head_yaw": 1.5, "head_pitch": 0.5, "face_distance": 49, "blink_count": 3},
        ]
        result = calculate_vision_scores(data)
        assert "head_stable" in result
        assert "face_stable" in result
        assert "blink_stable" in result
        assert all(0 <= v <= 1 for v in result.values())

    def test_empty_data(self):
        result = calculate_vision_scores([])
        assert result == {"head_stable": 0.5, "face_stable": 0.5, "blink_stable": 0.5}

    def test_missing_fields(self):
        data = [{"head_yaw": 2}]
        result = calculate_vision_scores(data)
        assert 0 <= result["head_stable"] <= 1
        assert result["face_stable"] == 1.0
        assert result["blink_stable"] == 1.0

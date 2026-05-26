from analytics.data_processor import DataProcessor


class TestCleanGameData:
    def test_empty_list(self):
        assert DataProcessor.clean_game_data([]) == []

    def test_valid_data_passes_through(self):
        data = [{"score": 50, "accuracy": 0.5}, {"score": 80, "accuracy": 0.8}]
        result = DataProcessor.clean_game_data(data)
        assert len(result) == 2

    def test_filters_negative_score(self):
        data = [{"score": -10, "accuracy": 0.5}, {"score": 50, "accuracy": 0.5}]
        result = DataProcessor.clean_game_data(data)
        assert len(result) == 1

    def test_filters_score_over_1000(self):
        data = [{"score": 1500, "accuracy": 0.5}, {"score": 50, "accuracy": 0.5}]
        result = DataProcessor.clean_game_data(data)
        assert len(result) == 1

    def test_filters_negative_accuracy(self):
        data = [{"score": 50, "accuracy": -0.5}, {"score": 50, "accuracy": 0.5}]
        result = DataProcessor.clean_game_data(data)
        assert len(result) == 1

    def test_filters_accuracy_over_1(self):
        data = [{"score": 50, "accuracy": 1.5}, {"score": 50, "accuracy": 0.5}]
        result = DataProcessor.clean_game_data(data)
        assert len(result) == 1

    def test_none_values_allowed(self):
        data = [{"score": None, "accuracy": None}]
        result = DataProcessor.clean_game_data(data)
        assert len(result) == 1


class TestCleanVisionData:
    def test_empty_list(self):
        assert DataProcessor.clean_vision_data([]) == []

    def test_valid_data_passes_through(self):
        data = [{"attention_score": 50}, {"attention_score": 80}]
        result = DataProcessor.clean_vision_data(data)
        assert len(result) == 2

    def test_filters_score_over_100(self):
        data = [{"attention_score": 150}, {"attention_score": 50}]
        result = DataProcessor.clean_vision_data(data)
        assert len(result) == 1

    def test_filters_negative_score(self):
        data = [{"attention_score": -5}, {"attention_score": 50}]
        result = DataProcessor.clean_vision_data(data)
        assert len(result) == 1

    def test_face_not_detected_nulls_values(self):
        data = [{"attention_score": 50, "face_detected": 0, "head_yaw": 10, "head_pitch": 5}]
        result = DataProcessor.clean_vision_data(data)
        assert result[0]["attention_score"] is None
        assert result[0]["head_yaw"] is None
        assert result[0]["head_pitch"] is None

    def test_face_detected_preserves_values(self):
        data = [{"attention_score": 50, "face_detected": 1, "head_yaw": 10}]
        result = DataProcessor.clean_vision_data(data)
        assert result[0]["attention_score"] == 50
        assert result[0]["head_yaw"] == 10


class TestMergeSessionData:
    def test_both_empty(self):
        assert DataProcessor.merge_session_data([], []) == []

    def test_merges_by_timestamp(self):
        game = [{"timestamp": "2024-01-01T10:00:00", "score": 80}]
        vision = [{"timestamp": "2024-01-01T10:00:00", "attention_score": 70}]
        result = DataProcessor.merge_session_data(game, vision)
        assert len(result) == 1
        assert "game_score" in result[0]
        assert "vision_attention_score" in result[0]

    def test_prefers_timestamp_over_created_at(self):
        game = [{"created_at": "2024-01-01T10:00:00", "score": 80}]
        vision = [{"created_at": "2024-01-01T10:00:00", "attention_score": 70}]
        result = DataProcessor.merge_session_data(game, vision)
        assert len(result) == 1

    def test_different_timestamps_kept_separate(self):
        game = [{"timestamp": "2024-01-01T10:00:00", "score": 80}]
        vision = [{"timestamp": "2024-01-01T11:00:00", "attention_score": 70}]
        result = DataProcessor.merge_session_data(game, vision)
        assert len(result) == 2


class TestNormalizeScores:
    def test_empty_list(self):
        assert DataProcessor.normalize_scores([]) == []

    def test_normalizes_to_range(self):
        result = DataProcessor.normalize_scores([0, 50, 100])
        assert result[0] == 0
        assert result[2] == 100
        assert 0 < result[1] < 100

    def test_identical_values(self):
        result = DataProcessor.normalize_scores([50, 50, 50])
        assert all(v == 50 for v in result)

    def test_none_values_preserved(self):
        result = DataProcessor.normalize_scores([50, None, 100])
        assert result[1] is None
        assert result[0] == 0
        assert result[2] == 100

    def test_all_none(self):
        result = DataProcessor.normalize_scores([None, None])
        assert result == [None, None]


class TestCalculateStatistics:
    def test_empty_data(self):
        result = DataProcessor.calculate_statistics([], "score")
        assert result == {"mean": 0, "std": 0, "min": 0, "max": 0, "median": 0}

    def test_computes_all_metrics(self):
        data = [{"score": 10}, {"score": 20}, {"score": 30}, {"score": 40}, {"score": 50}]
        result = DataProcessor.calculate_statistics(data, "score")
        assert result["mean"] == 30
        assert result["min"] == 10
        assert result["max"] == 50
        assert result["median"] == 30
        assert result["std"] > 0

    def test_single_value(self):
        data = [{"score": 42}]
        result = DataProcessor.calculate_statistics(data, "score")
        assert result["mean"] == 42
        assert result["std"] == 0


class TestDetectOutliers:
    def test_empty_data(self):
        assert DataProcessor.detect_outliers([], "score") == []

    def test_single_item(self):
        assert DataProcessor.detect_outliers([{"score": 50}], "score") == []

    def test_detects_extreme_outlier(self):
        data = [
            {"score": 50},
            {"score": 52},
            {"score": 48},
            {"score": 51},
            {"score": 49},
            {"score": 200},
        ]
        result = DataProcessor.detect_outliers(data, "score")
        assert len(result) == 1
        assert result[0] == 5

    def test_none_values_ignored(self):
        data = [
            {"score": 50},
            {"score": None},
            {"score": 52},
            {"score": 51},
            {"score": 49},
            {"score": 48},
            {"score": 500},
        ]
        result = DataProcessor.detect_outliers(data, "score")
        assert len(result) >= 1

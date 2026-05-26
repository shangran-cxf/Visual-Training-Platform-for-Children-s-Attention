import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")


@pytest.fixture
def sample_vision_data():
    return {
        "head_stability": 85,
        "focus_duration": 25,
        "blink_rate": 15,
        "screen_distance": 50,
    }


@pytest.fixture
def sample_game_data():
    return {
        "accuracy": 80,
        "reaction_speed": 70,
        "completion_rate": 90,
    }


@pytest.fixture
def sample_sessions():
    return [
        {"game_type": "schulte", "overall_score": 75, "accuracy": 80, "attention_stability": 70},
        {"game_type": "card-matching", "overall_score": 85, "accuracy": 90, "attention_stability": 80},
        {"game_type": "traffic-light", "overall_score": 65, "accuracy": 70, "attention_stability": 60},
        {"game_type": "magic-maze", "overall_score": 70, "accuracy": 75, "attention_stability": 65},
        {"game_type": "reverse-memory", "overall_score": 90, "accuracy": 95, "attention_stability": 85},
    ]

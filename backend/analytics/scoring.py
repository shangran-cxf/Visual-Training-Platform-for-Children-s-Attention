class ScoringEngine:
    """评分算法模块 - 综合评分算法"""
    
    WEIGHTS = {
        'visual': 0.6,
        'game': 0.4,
        'head_stability': 0.2,
        'focus_quality': 0.2,
        'blink_score': 0.1,
        'distance_score': 0.1,
        'accuracy': 0.2,
        'speed': 0.1,
        'completion': 0.1
    }
    
    @staticmethod
    def calculate_head_stability(head_yaw: float, head_pitch: float) -> float:
        """计算头部稳定性评分"""
        if head_yaw is None or head_pitch is None:
            return 0.0
        
        deviation = (head_yaw ** 2 + head_pitch ** 2) ** 0.5
        
        if deviation <= 5:
            score = 100.0
        elif deviation <= 10:
            score = 95.0 - (deviation - 5) * 2
        elif deviation <= 20:
            score = 85.0 - (deviation - 10) * 3
        elif deviation <= 30:
            score = 55.0 - (deviation - 20) * 2.5
        else:
            score = max(0.0, 30.0 - (deviation - 30) * 1.5)
        
        return round(score, 2)
    
    @staticmethod
    def calculate_focus_quality(focus_duration: int, total_duration: int) -> float:
        """计算专注质量评分"""
        if focus_duration is None or total_duration is None or total_duration <= 0:
            return 0.0
        
        focus_ratio = focus_duration / total_duration
        
        if focus_ratio >= 0.95:
            score = 100.0
        elif focus_ratio >= 0.90:
            score = 95.0 + (focus_ratio - 0.90) * 100
        elif focus_ratio >= 0.80:
            score = 85.0 + (focus_ratio - 0.80) * 100
        elif focus_ratio >= 0.70:
            score = 70.0 + (focus_ratio - 0.70) * 150
        elif focus_ratio >= 0.60:
            score = 55.0 + (focus_ratio - 0.60) * 150
        elif focus_ratio >= 0.50:
            score = 40.0 + (focus_ratio - 0.50) * 150
        else:
            score = focus_ratio * 80
        
        return round(min(100.0, max(0.0, score)), 2)
    
    @staticmethod
    def calculate_blink_score(blink_rate: float) -> float:
        """计算眨眼频率评分"""
        if blink_rate is None:
            return 0.0
        
        normal_min = 15.0
        normal_max = 20.0
        
        if normal_min <= blink_rate <= normal_max:
            return 100.0
        
        if blink_rate < normal_min:
            deviation = normal_min - blink_rate
            score = 100.0 - deviation * 5
        else:
            deviation = blink_rate - normal_max
            score = 100.0 - deviation * 3
        
        return round(max(0.0, min(100.0, score)), 2)
    
    @staticmethod
    def calculate_distance_score(face_area: float) -> float:
        """计算屏幕距离评分"""
        if face_area is None or face_area <= 0:
            return 0.0
        
        optimal_min = 8000.0
        optimal_max = 15000.0
        acceptable_min = 5000.0
        acceptable_max = 20000.0
        
        if optimal_min <= face_area <= optimal_max:
            return 100.0
        
        if face_area < optimal_min:
            if face_area >= acceptable_min:
                ratio = (face_area - acceptable_min) / (optimal_min - acceptable_min)
                score = 70.0 + ratio * 30.0
            else:
                ratio = face_area / acceptable_min
                score = ratio * 70.0
        else:
            if face_area <= acceptable_max:
                ratio = (acceptable_max - face_area) / (acceptable_max - optimal_max)
                score = 70.0 + ratio * 30.0
            else:
                excess_ratio = (face_area - acceptable_max) / acceptable_max
                score = max(0.0, 70.0 - excess_ratio * 50.0)
        
        return round(max(0.0, min(100.0, score)), 2)
    
    @staticmethod
    def calculate_speed_score(completion_time: int, expected_time: int) -> float:
        """计算反应速度评分"""
        if completion_time is None or expected_time is None or expected_time <= 0:
            return 0.0
        
        if completion_time <= 0:
            return 0.0
        
        time_ratio = completion_time / expected_time
        
        if time_ratio <= 0.5:
            score = 100.0
        elif time_ratio <= 0.75:
            score = 95.0 - (time_ratio - 0.5) * 20
        elif time_ratio <= 1.0:
            score = 90.0 - (time_ratio - 0.75) * 40
        elif time_ratio <= 1.5:
            score = 80.0 - (time_ratio - 1.0) * 60
        elif time_ratio <= 2.0:
            score = 50.0 - (time_ratio - 1.5) * 40
        else:
            score = max(0.0, 30.0 - (time_ratio - 2.0) * 10)
        
        return round(max(0.0, min(100.0, score)), 2)
    
    @staticmethod
    def calculate_completion_score(levels_completed: int, total_levels: int) -> float:
        """计算完成度评分"""
        if levels_completed is None or total_levels is None or total_levels <= 0:
            return 0.0
        
        if levels_completed < 0:
            return 0.0
        
        completion_ratio = levels_completed / total_levels
        score = completion_ratio * 100.0
        
        return round(max(0.0, min(100.0, score)), 2)
    
    @staticmethod
    def safe_score(score: float, max_score: float = 100.0) -> float:
        """确保评分在有效范围内"""
        if score is None:
            return 0.0
        
        if not isinstance(score, (int, float)):
            return 0.0
        
        if score < 0:
            return 0.0
        
        if score > max_score:
            return max_score
        
        return round(float(score), 2)
    
    @staticmethod
    def calculate_overall_score(vision_data: dict, game_data: dict) -> float:
        """计算综合评分"""
        if vision_data is None:
            vision_data = {}
        if game_data is None:
            game_data = {}
        
        head_stability = ScoringEngine.calculate_head_stability(
            vision_data.get('head_yaw'),
            vision_data.get('head_pitch')
        )
        
        focus_quality = ScoringEngine.calculate_focus_quality(
            vision_data.get('focus_duration', 0),
            vision_data.get('total_duration', 1)
        )
        
        blink_score = ScoringEngine.calculate_blink_score(
            vision_data.get('blink_rate')
        )
        
        distance_score = ScoringEngine.calculate_distance_score(
            vision_data.get('face_area')
        )
        
        accuracy_score = ScoringEngine.safe_score(game_data.get('accuracy', 0))
        
        speed_score = ScoringEngine.calculate_speed_score(
            game_data.get('completion_time', 0),
            game_data.get('expected_time', 1)
        )
        
        completion_score = ScoringEngine.calculate_completion_score(
            game_data.get('levels_completed', 0),
            game_data.get('total_levels', 1)
        )
        
        visual_components = [
            head_stability * ScoringEngine.WEIGHTS['head_stability'],
            focus_quality * ScoringEngine.WEIGHTS['focus_quality'],
            blink_score * ScoringEngine.WEIGHTS['blink_score'],
            distance_score * ScoringEngine.WEIGHTS['distance_score']
        ]
        visual_weight_sum = (
            ScoringEngine.WEIGHTS['head_stability'] +
            ScoringEngine.WEIGHTS['focus_quality'] +
            ScoringEngine.WEIGHTS['blink_score'] +
            ScoringEngine.WEIGHTS['distance_score']
        )
        visual_score = sum(visual_components) / visual_weight_sum if visual_weight_sum > 0 else 0
        
        game_components = [
            accuracy_score * ScoringEngine.WEIGHTS['accuracy'],
            speed_score * ScoringEngine.WEIGHTS['speed'],
            completion_score * ScoringEngine.WEIGHTS['completion']
        ]
        game_weight_sum = (
            ScoringEngine.WEIGHTS['accuracy'] +
            ScoringEngine.WEIGHTS['speed'] +
            ScoringEngine.WEIGHTS['completion']
        )
        game_score = sum(game_components) / game_weight_sum if game_weight_sum > 0 else 0
        
        overall_score = (
            visual_score * ScoringEngine.WEIGHTS['visual'] +
            game_score * ScoringEngine.WEIGHTS['game']
        )
        
        return round(max(0.0, min(100.0, overall_score)), 2)

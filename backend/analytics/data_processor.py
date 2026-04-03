import statistics
from typing import List, Dict, Any, Optional


class DataProcessor:
    """数据处理模块 - 数据清洗、合并、标准化"""
    
    @staticmethod
    def clean_game_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗游戏数据 - 过滤异常值"""
        if not data:
            return []
        
        cleaned_data = []
        for item in data:
            score = item.get('score')
            accuracy = item.get('accuracy')
            
            if score is not None and (score < 0 or score > 1000):
                continue
            
            if accuracy is not None and (accuracy < 0 or accuracy > 1):
                continue
            
            cleaned_data.append(item)
        
        return cleaned_data
    
    @staticmethod
    def clean_vision_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """清洗视觉数据 - 处理缺失值和异常值"""
        if not data:
            return []
        
        cleaned_data = []
        for item in data:
            attention_score = item.get('attention_score')
            
            if attention_score is not None and (attention_score < 0 or attention_score > 100):
                continue
            
            cleaned_item = item.copy()
            if item.get('face_detected') == 0:
                cleaned_item['attention_score'] = None
                cleaned_item['head_yaw'] = None
                cleaned_item['head_pitch'] = None
            
            cleaned_data.append(cleaned_item)
        
        return cleaned_data
    
    @staticmethod
    def merge_session_data(game_data: List[Dict[str, Any]], vision_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并游戏数据和视觉数据"""
        if not game_data and not vision_data:
            return []
        
        def get_timestamp(item):
            ts = item.get('timestamp') or item.get('created_at')
            if ts is None:
                return None
            if isinstance(ts, str):
                return ts
            return str(ts)
        
        game_by_time = {}
        for item in game_data:
            ts = get_timestamp(item)
            if ts:
                if ts not in game_by_time:
                    game_by_time[ts] = []
                game_by_time[ts].append(item)
        
        vision_by_time = {}
        for item in vision_data:
            ts = get_timestamp(item)
            if ts:
                if ts not in vision_by_time:
                    vision_by_time[ts] = []
                vision_by_time[ts].append(item)
        
        all_timestamps = sorted(set(game_by_time.keys()) | set(vision_by_time.keys()))
        
        merged_data = []
        for ts in all_timestamps:
            merged_item = {'timestamp': ts}
            
            if ts in game_by_time:
                for key, value in game_by_time[ts][0].items():
                    if key not in ['timestamp', 'created_at']:
                        merged_item[f'game_{key}'] = value
            
            if ts in vision_by_time:
                for key, value in vision_by_time[ts][0].items():
                    if key not in ['timestamp', 'created_at']:
                        merged_item[f'vision_{key}'] = value
            
            merged_data.append(merged_item)
        
        return merged_data
    
    @staticmethod
    def normalize_scores(scores: List[float], max_score: float = 100.0) -> List[float]:
        """标准化分数到0-100范围"""
        if not scores:
            return []
        
        valid_scores = [s for s in scores if s is not None]
        if not valid_scores:
            return [None] * len(scores)
        
        min_val = min(valid_scores)
        max_val = max(valid_scores)
        
        if max_val == min_val:
            return [max_score / 2 if s is not None else None for s in scores]
        
        normalized = []
        for score in scores:
            if score is None:
                normalized.append(None)
            else:
                norm_score = ((score - min_val) / (max_val - min_val)) * max_score
                normalized.append(round(norm_score, 2))
        
        return normalized
    
    @staticmethod
    def calculate_statistics(data: List[Dict[str, Any]], field: str) -> Dict[str, float]:
        """计算统计指标"""
        if not data:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
        
        values = []
        for item in data:
            value = item.get(field)
            if value is not None:
                values.append(float(value))
        
        if not values:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
        
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0
        min_val = min(values)
        max_val = max(values)
        median_val = statistics.median(values)
        
        return {
            'mean': round(mean_val, 2),
            'std': round(std_val, 2),
            'min': round(min_val, 2),
            'max': round(max_val, 2),
            'median': round(median_val, 2)
        }
    
    @staticmethod
    def detect_outliers(data: List[Dict[str, Any]], field: str, threshold: float = 2.0) -> List[int]:
        """检测异常值（使用Z-score方法）"""
        if not data or len(data) < 2:
            return []
        
        values = []
        indices = []
        for idx, item in enumerate(data):
            value = item.get(field)
            if value is not None:
                values.append(float(value))
                indices.append(idx)
        
        if len(values) < 2:
            return []
        
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)
        
        if std_val == 0:
            return []
        
        outlier_indices = []
        for i, value in enumerate(values):
            z_score = abs(value - mean_val) / std_val
            if z_score > threshold:
                outlier_indices.append(indices[i])
        
        return sorted(outlier_indices)

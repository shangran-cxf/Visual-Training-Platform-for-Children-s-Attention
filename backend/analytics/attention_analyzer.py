from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import statistics


class AttentionAnalyzer:
    """注意力分析模块 - 专注度算法、趋势分析"""
    
    GAME_DIMENSION_MAP = {
        'schulte': ['selective_attention', 'sustained_attention'],
        'find-numbers': ['selective_attention', 'visual_tracking'],
        'card-matching': ['working_memory', 'sustained_attention'],
        'reverse-memory': ['working_memory'],
        'traffic-light': ['inhibitory_control', 'sustained_attention'],
        'command-adventure': ['inhibitory_control'],
        'magic-maze': ['visual_tracking', 'sustained_attention'],
        'sun-tracking': ['visual_tracking'],
        'animal-searching': ['selective_attention', 'visual_tracking'],
        'water-plants': ['sustained_attention', 'inhibitory_control']
    }
    
    DIMENSION_NAMES = {
        'selective_attention': '选择性注意力',
        'sustained_attention': '持续性注意力',
        'visual_tracking': '视觉追踪',
        'working_memory': '工作记忆',
        'inhibitory_control': '抑制控制'
    }
    
    PERFORMANCE_LEVELS = {
        (90, 100): '优秀',
        (75, 89.99): '良好',
        (60, 74.99): '一般',
        (0, 59.99): '需改进'
    }
    
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
        
        head_stability = vision_data.get('head_stability', 70)
        if head_stability is not None:
            visual_score += head_stability * 0.2
        
        focus_duration = vision_data.get('focus_duration', 0)
        focus_quality = min(100, (focus_duration / 30) * 100) if focus_duration else 50
        visual_score += focus_quality * 0.2
        
        blink_rate = vision_data.get('blink_rate', 15)
        if blink_rate is not None:
            normal_blink_range = (10, 20)
            if normal_blink_range[0] <= blink_rate <= normal_blink_range[1]:
                blink_score = 100
            elif blink_rate < normal_blink_range[0]:
                blink_score = max(0, 100 - (normal_blink_range[0] - blink_rate) * 5)
            else:
                blink_score = max(0, 100 - (blink_rate - normal_blink_range[1]) * 5)
            visual_score += blink_score * 0.1
        
        screen_distance = vision_data.get('screen_distance', 50)
        if screen_distance is not None:
            ideal_distance = 50
            distance_deviation = abs(screen_distance - ideal_distance)
            distance_score = max(0, 100 - distance_deviation * 2)
            visual_score += distance_score * 0.1
        
        accuracy = game_data.get('accuracy', 0)
        if accuracy is not None:
            game_score += accuracy * 0.2
        
        reaction_speed = game_data.get('reaction_speed', 50)
        if reaction_speed is not None:
            game_score += reaction_speed * 0.1
        
        completion_rate = game_data.get('completion_rate', 0)
        if completion_rate is not None:
            game_score += completion_rate * 0.1
        
        total_score = visual_score + game_score
        return round(min(100, max(0, total_score)), 2)
    
    @staticmethod
    def assess_five_dimensions(sessions_data: list) -> dict:
        """评估五维注意力能力
        
        Args:
            sessions_data: 训练会话数据列表，每个元素包含:
                - game_type: 游戏类型
                - overall_score: 综合评分
                - accuracy: 正确率
                - attention_stability: 注意力稳定性
        
        Returns:
            五维注意力评分字典
        """
        dimension_scores = {
            'selective_attention': [],
            'sustained_attention': [],
            'visual_tracking': [],
            'working_memory': [],
            'inhibitory_control': []
        }
        
        for session in sessions_data:
            game_type = session.get('game_type')
            if game_type not in AttentionAnalyzer.GAME_DIMENSION_MAP:
                continue
            
            dimensions = AttentionAnalyzer.GAME_DIMENSION_MAP[game_type]
            score = session.get('overall_score', 0)
            accuracy = session.get('accuracy', 0)
            stability = session.get('attention_stability', 0)
            
            weighted_score = score * 0.5 + accuracy * 0.3 + stability * 0.2
            
            for dimension in dimensions:
                dimension_scores[dimension].append(weighted_score)
        
        result = {}
        for dimension, scores in dimension_scores.items():
            if scores:
                result[dimension] = round(statistics.mean(scores), 2)
            else:
                result[dimension] = 0.0
        
        return result
    
    @staticmethod
    def analyze_trend(historical_data: list) -> dict:
        """分析注意力趋势
        
        Args:
            historical_data: 历史训练数据列表，按时间排序，每个元素包含:
                - date: 日期
                - overall_score: 综合评分
                - accuracy: 正确率
        
        Returns:
            趋势分析结果
        """
        if not historical_data or len(historical_data) < 2:
            return {
                'trend': 'stable',
                'change_rate': 0.0,
                'description': '数据不足，无法分析趋势'
            }
        
        scores = [d.get('overall_score', 0) for d in historical_data]
        
        if len(scores) >= 3:
            recent_scores = scores[-3:]
            earlier_scores = scores[:-3] if len(scores) > 3 else scores[:1]
            
            recent_avg = statistics.mean(recent_scores)
            earlier_avg = statistics.mean(earlier_scores)
            
            if earlier_avg == 0:
                change_rate = 0.0
            else:
                change_rate = ((recent_avg - earlier_avg) / earlier_avg) * 100
            
            if change_rate > 5:
                trend = 'improving'
                description = '注意力表现呈上升趋势，继续保持！'
            elif change_rate < -5:
                trend = 'declining'
                description = '注意力表现有所下降，建议加强训练'
            else:
                trend = 'stable'
                description = '注意力表现稳定'
        else:
            first_score = scores[0]
            last_score = scores[-1]
            
            if first_score == 0:
                change_rate = 0.0
            else:
                change_rate = ((last_score - first_score) / first_score) * 100
            
            if change_rate > 5:
                trend = 'improving'
                description = '注意力表现呈上升趋势'
            elif change_rate < -5:
                trend = 'declining'
                description = '注意力表现有所下降'
            else:
                trend = 'stable'
                description = '注意力表现稳定'
        
        return {
            'trend': trend,
            'change_rate': round(change_rate, 2),
            'description': description,
            'recent_average': round(statistics.mean(scores[-3:]), 2) if len(scores) >= 3 else round(statistics.mean(scores), 2),
            'overall_average': round(statistics.mean(scores), 2)
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
        
        scores = [s.get('overall_score', 0) for s in session_data]
        
        if len(scores) >= 3:
            mean_score = statistics.mean(scores)
            std_score = statistics.stdev(scores) if len(scores) > 1 else 0
            
            for i, session in enumerate(session_data):
                score = session.get('overall_score', 0)
                
                if std_score > 0 and abs(score - mean_score) > 2 * std_score:
                    anomaly = {
                        'type': 'score_outlier',
                        'session_id': session.get('session_id'),
                        'score': score,
                        'expected_range': f'{round(mean_score - std_score, 2)} - {round(mean_score + std_score, 2)}',
                        'severity': 'high' if abs(score - mean_score) > 3 * std_score else 'medium',
                        'description': f"评分{'异常偏高' if score > mean_score else '异常偏低'}，偏离正常范围"
                    }
                    anomalies.append(anomaly)
        
        for i in range(1, len(session_data)):
            prev_score = session_data[i-1].get('overall_score', 0)
            curr_score = session_data[i].get('overall_score', 0)
            
            if prev_score > 0:
                drop_rate = ((prev_score - curr_score) / prev_score) * 100
                
                if drop_rate > 30:
                    anomaly = {
                        'type': 'sudden_drop',
                        'session_id': session_data[i].get('session_id'),
                        'previous_score': prev_score,
                        'current_score': curr_score,
                        'drop_rate': round(drop_rate, 2),
                        'severity': 'high' if drop_rate > 50 else 'medium',
                        'description': f'注意力评分突然下降{round(drop_rate, 1)}%，可能存在干扰因素'
                    }
                    anomalies.append(anomaly)
        
        for session in session_data:
            stability = session.get('attention_stability', 100)
            
            if stability < 50:
                anomaly = {
                    'type': 'low_stability',
                    'session_id': session.get('session_id'),
                    'stability': stability,
                    'severity': 'high' if stability < 30 else 'medium',
                    'description': f'注意力稳定性较低({stability}%)，训练过程中注意力波动较大'
                }
                anomalies.append(anomaly)
        
        for session in session_data:
            accuracy = session.get('accuracy', 100)
            score = session.get('overall_score', 0)
            
            if accuracy < 50 and score > 70:
                anomaly = {
                    'type': 'accuracy_score_mismatch',
                    'session_id': session.get('session_id'),
                    'accuracy': accuracy,
                    'score': score,
                    'severity': 'low',
                    'description': '正确率较低但评分较高，可能存在数据异常'
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
            return '优秀'
        elif score >= 75:
            return '良好'
        elif score >= 60:
            return '一般'
        else:
            return '需改进'
    
    @staticmethod
    def get_dimension_strengths_weaknesses(dimension_scores: dict) -> dict:
        """分析维度优势和劣势
        
        Args:
            dimension_scores: 五维注意力评分字典
        
        Returns:
            包含优势和劣势的分析结果
        """
        if not dimension_scores:
            return {'strengths': [], 'weaknesses': []}
        
        sorted_dimensions = sorted(
            dimension_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        strengths = []
        weaknesses = []
        
        for dimension, score in sorted_dimensions[:2]:
            if score >= 70:
                strengths.append({
                    'dimension': dimension,
                    'name': AttentionAnalyzer.DIMENSION_NAMES.get(dimension, dimension),
                    'score': score,
                    'level': AttentionAnalyzer.get_performance_level(score)
                })
        
        for dimension, score in sorted_dimensions[-2:]:
            if score < 60:
                weaknesses.append({
                    'dimension': dimension,
                    'name': AttentionAnalyzer.DIMENSION_NAMES.get(dimension, dimension),
                    'score': score,
                    'level': AttentionAnalyzer.get_performance_level(score)
                })
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses
        }
    
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
        
        sorted_dimensions = sorted(
            dimension_scores.items(),
            key=lambda x: x[1]
        )
        
        weakest_dimensions = [d[0] for d in sorted_dimensions[:2]]
        
        game_recommendations = []
        played_games = played_games or []
        
        for game_type, dimensions in AttentionAnalyzer.GAME_DIMENSION_MAP.items():
            match_count = sum(1 for d in weakest_dimensions if d in dimensions)
            
            if match_count > 0:
                avg_dimension_score = statistics.mean(
                    [dimension_scores.get(d, 0) for d in dimensions]
                )
                
                game_recommendations.append({
                    'game_type': game_type,
                    'dimensions': dimensions,
                    'dimension_names': [AttentionAnalyzer.DIMENSION_NAMES.get(d, d) for d in dimensions],
                    'match_score': match_count,
                    'avg_dimension_score': round(avg_dimension_score, 2),
                    'priority': 'high' if avg_dimension_score < 60 else 'medium',
                    'played': game_type in played_games
                })
        
        game_recommendations.sort(key=lambda x: (-x['match_score'], x['avg_dimension_score']))
        
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
            return {
                'improvement_rate': 0.0,
                'trend': 'stable',
                'description': '数据不足'
            }
        
        recent_avg = statistics.mean(recent_scores)
        previous_avg = statistics.mean(previous_scores)
        
        if previous_avg == 0:
            improvement_rate = 0.0
        else:
            improvement_rate = ((recent_avg - previous_avg) / previous_avg) * 100
        
        if improvement_rate > 10:
            trend = 'significant_improvement'
            description = '进步显著，继续保持！'
        elif improvement_rate > 0:
            trend = 'improvement'
            description = '有所进步，继续努力！'
        elif improvement_rate > -10:
            trend = 'stable'
            description = '表现稳定'
        else:
            trend = 'decline'
            description = '需要加强训练'
        
        return {
            'improvement_rate': round(improvement_rate, 2),
            'recent_average': round(recent_avg, 2),
            'previous_average': round(previous_avg, 2),
            'trend': trend,
            'description': description
        }

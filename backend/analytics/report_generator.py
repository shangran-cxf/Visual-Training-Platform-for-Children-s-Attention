from datetime import datetime, timedelta
from typing import Dict, List
import json
from database import execute_db
from .attention_analyzer import AttentionAnalyzer
from config import ATTENTION_DIMENSIONS, GAME_TYPES, BADGES


class ReportGenerator:
    """报告生成模块 - 评估报告、进度报告生成"""
    
    @staticmethod
    def generate_attention_report(child_id: int, period_start: str, period_end: str) -> dict:
        """生成注意力评估报告"""
        child = execute_db('SELECT id, name, age FROM children WHERE id = ?', (child_id,))
        if not child:
            return {'error': '孩子不存在'}
        
        child_info = {
            'id': child[0][0],
            'name': child[0][1],
            'age': child[0][2]
        }
        
        dimension_scores = AttentionAnalyzer.calculate_dimension_scores(
            child_id, period_start, period_end
        )
        
        strengths, weaknesses = AttentionAnalyzer.identify_strengths_weaknesses(dimension_scores)
        
        total_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0
        
        percentile = ReportGenerator.calculate_percentile(child_id, total_score)
        
        improvement_rate = ReportGenerator.calculate_improvement_rate(child_id, total_score)
        
        recommendations = ReportGenerator.generate_recommendations(dimension_scores, weaknesses)
        
        trends = {}
        for dim in ATTENTION_DIMENSIONS.keys():
            trends[dim] = AttentionAnalyzer.analyze_trends(child_id, dim, days=30)
        
        training_history = AttentionAnalyzer.get_training_history(child_id, limit=5)
        
        dimension_stats = AttentionAnalyzer.get_dimension_statistics(child_id)
        
        report = {
            'report_type': 'attention_assessment',
            'child_info': child_info,
            'period': {
                'start': period_start,
                'end': period_end
            },
            'dimension_scores': dimension_scores,
            'total_score': round(total_score, 2),
            'percentile': percentile,
            'improvement_rate': improvement_rate,
            'strengths': [ATTENTION_DIMENSIONS.get(s, s) for s in strengths],
            'weaknesses': [ATTENTION_DIMENSIONS.get(w, w) for w in weaknesses],
            'recommendations': recommendations,
            'trends': trends,
            'training_history': training_history,
            'dimension_statistics': dimension_stats,
            'generated_at': datetime.now().isoformat()
        }
        
        strengths_json = json.dumps([ATTENTION_DIMENSIONS.get(s, s) for s in strengths], ensure_ascii=False)
        weaknesses_json = json.dumps([ATTENTION_DIMENSIONS.get(w, w) for w in weaknesses], ensure_ascii=False)
        recommendations_json = json.dumps(recommendations, ensure_ascii=False)
        
        execute_db('''
            INSERT INTO child_reports 
            (child_id, report_type, period_start, period_end, 
             selective_attention_score, sustained_attention_score, visual_tracking_score,
             working_memory_score, inhibitory_control_score, total_score, percentile,
             improvement_rate, strengths, weaknesses, recommendations)
            VALUES (?, 'attention', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            child_id, period_start, period_end,
            dimension_scores.get('selective_attention', 0),
            dimension_scores.get('sustained_attention', 0),
            dimension_scores.get('visual_tracking', 0),
            dimension_scores.get('working_memory', 0),
            dimension_scores.get('inhibitory_control', 0),
            total_score, percentile, improvement_rate,
            strengths_json, weaknesses_json, recommendations_json
        ))
        
        return report
    
    @staticmethod
    def generate_progress_report(child_id: int, period: str = 'month') -> dict:
        """生成训练进度报告"""
        child = execute_db('SELECT id, name, age FROM children WHERE id = ?', (child_id,))
        if not child:
            return {'error': '孩子不存在'}
        
        child_info = {
            'id': child[0][0],
            'name': child[0][1],
            'age': child[0][2]
        }
        
        if period == 'week':
            days = 7
        elif period == 'month':
            days = 30
        elif period == 'quarter':
            days = 90
        else:
            days = 30
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        sessions = execute_db('''
            SELECT id, game_type, overall_score, total_accuracy, 
                   avg_attention_score, total_time, created_at
            FROM session_summaries
            WHERE child_id = ? AND created_at BETWEEN ? AND ?
            ORDER BY created_at
        ''', (child_id, start_date.isoformat(), end_date.isoformat()))
        
        if not sessions:
            return {
                'report_type': 'progress',
                'child_info': child_info,
                'period': period,
                'message': '该时间段内没有训练记录',
                'generated_at': datetime.now().isoformat()
            }
        
        total_sessions = len(sessions)
        total_duration = sum(s[5] or 0 for s in sessions)
        games_played = len(set(s[1] for s in sessions))
        
        scores = [s[2] or 0 for s in sessions]
        accuracies = [s[3] or 0 for s in sessions]
        attention_scores = [s[4] or 0 for s in sessions]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        avg_attention = sum(attention_scores) / len(attention_scores) if attention_scores else 0
        
        if len(scores) >= 2:
            first_half_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
            second_half_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            score_change = second_half_avg - first_half_avg
            
            first_half_acc = sum(accuracies[:len(accuracies)//2]) / (len(accuracies)//2)
            second_half_acc = sum(accuracies[len(accuracies)//2:]) / (len(accuracies) - len(accuracies)//2)
            accuracy_improvement = second_half_acc - first_half_acc
            
            first_half_att = sum(attention_scores[:len(attention_scores)//2]) / (len(attention_scores)//2)
            second_half_att = sum(attention_scores[len(attention_scores)//2:]) / (len(attention_scores) - len(attention_scores)//2)
            attention_improvement = second_half_att - first_half_att
        else:
            score_change = 0
            accuracy_improvement = 0
            attention_improvement = 0
        
        badge_dict = {b['id']: b for b in BADGES}
        
        user_badges = execute_db('''
            SELECT badge_id, earned_at
            FROM user_badges
            WHERE child_id = ? AND earned_at BETWEEN ? AND ?
            ORDER BY earned_at DESC
        ''', (child_id, start_date.isoformat(), end_date.isoformat()))
        
        badges_earned = len(user_badges)
        milestones = []
        for ub in user_badges:
            badge_id = ub[0]
            if badge_id in badge_dict:
                badge = badge_dict[badge_id]
                milestones.append({
                    'name': badge['name'],
                    'icon': badge['icon'],
                    'earned_at': ub[1][:10] if ub[1] else None
                })
        
        if total_sessions >= 50:
            milestones.append({'name': '完成50次训练', 'icon': '🎯', 'achieved_at': end_date.isoformat()})
        elif total_sessions >= 10:
            milestones.append({'name': '完成10次训练', 'icon': '⭐', 'achieved_at': end_date.isoformat()})
        
        if avg_score >= 90:
            milestones.append({'name': '平均分达到90分', 'icon': '🏆', 'achieved_at': end_date.isoformat()})
        
        dimension_scores = AttentionAnalyzer.calculate_dimension_scores(
            child_id, start_date.isoformat(), end_date.isoformat()
        )
        _, weaknesses = AttentionAnalyzer.identify_strengths_weaknesses(dimension_scores)
        
        recommended_games = []
        focus_areas = []
        
        for weakness in weaknesses:
            focus_areas.append(ATTENTION_DIMENSIONS.get(weakness, weakness))
            
            for game_type, game_info in GAME_TYPES.items():
                if weakness in game_info.get('dimensions', []):
                    recommended_games.append({
                        'game_type': game_type,
                        'game_name': game_info.get('name', game_type),
                        'target_dimension': ATTENTION_DIMENSIONS.get(weakness, weakness)
                    })
        
        recommended_games = recommended_games[:3]
        
        report = {
            'report_type': 'progress',
            'child_info': child_info,
            'period': period,
            'period_dates': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'statistics': {
                'total_sessions': total_sessions,
                'total_duration': total_duration,
                'total_duration_formatted': f"{total_duration // 3600}小时{(total_duration % 3600) // 60}分钟",
                'games_played': games_played,
                'avg_score': round(avg_score, 2),
                'avg_accuracy': round(avg_accuracy, 2),
                'avg_attention': round(avg_attention, 2)
            },
            'progress': {
                'score_change': round(score_change, 2),
                'accuracy_improvement': round(accuracy_improvement, 2),
                'attention_improvement': round(attention_improvement, 2)
            },
            'milestones': milestones,
            'badges_earned': badges_earned,
            'recommended_games': recommended_games,
            'focus_areas': focus_areas,
            'generated_at': datetime.now().isoformat()
        }
        
        milestones_json = json.dumps(milestones, ensure_ascii=False)
        recommended_games_json = json.dumps(recommended_games, ensure_ascii=False)
        focus_areas_json = json.dumps(focus_areas, ensure_ascii=False)
        
        execute_db('''
            INSERT INTO child_reports
            (child_id, report_type, total_sessions, total_duration, games_played,
             avg_score_change, accuracy_improvement, attention_improvement,
             badges_earned, milestones_achieved, recommended_games, focus_areas)
            VALUES (?, 'progress', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            child_id, total_sessions, total_duration, games_played,
            score_change, accuracy_improvement, attention_improvement,
            milestones_json, badges_earned, recommended_games_json, focus_areas_json
        ))
        
        return report
    
    @staticmethod
    def generate_recommendations(dimension_scores: dict, weak_areas: list) -> list:
        """生成个性化建议"""
        recommendations = []
        
        dimension_recommendations = {
            'selective_attention': {
                'suggestion': '建议进行选择性注意力训练，如舒尔特方格、找数字等游戏',
                'games': ['schulte', 'find-numbers', 'animal-searching']
            },
            'sustained_attention': {
                'suggestion': '建议增加持续性注意力训练，可以尝试长时间专注的游戏',
                'games': ['schulte', 'card-matching', 'water-plants']
            },
            'visual_tracking': {
                'suggestion': '建议进行视觉追踪训练，如追踪太阳、魔法迷宫等游戏',
                'games': ['sun-tracking', 'magic-maze', 'find-numbers']
            },
            'working_memory': {
                'suggestion': '建议进行工作记忆训练，如记忆翻牌、倒序记忆等游戏',
                'games': ['card-matching', 'reverse-memory']
            },
            'inhibitory_control': {
                'suggestion': '建议进行抑制控制训练，如红绿灯、指令冒险等游戏',
                'games': ['traffic-light', 'command-adventure', 'water-plants']
            }
        }
        
        for area in weak_areas:
            if area in dimension_recommendations:
                rec = dimension_recommendations[area]
                recommendations.append(rec['suggestion'])
                
                game_names = []
                for game_type in rec['games']:
                    if game_type in GAME_TYPES:
                        game_names.append(GAME_TYPES[game_type]['name'])
                
                if game_names:
                    recommendations.append(f"推荐游戏：{', '.join(game_names)}")
        
        avg_score = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0
        
        if avg_score < 60:
            recommendations.append('建议降低训练难度，循序渐进提升能力')
            recommendations.append('建议每天训练1-2次，每次15-20分钟')
        elif avg_score < 80:
            recommendations.append('建议保持当前训练频率，逐步提升难度')
            recommendations.append('建议每天训练1次，每次20-30分钟')
        else:
            recommendations.append('表现优秀！建议尝试更高难度的训练')
            recommendations.append('建议每周训练3-4次，保持训练状态')
        
        if not recommendations:
            recommendations.append('表现良好，继续保持！')
        
        return recommendations
    
    @staticmethod
    def calculate_percentile(child_id: int, score: float) -> int:
        """计算百分位排名"""
        child = execute_db('SELECT age FROM children WHERE id = ?', (child_id,))
        if not child:
            return 0
        
        child_age = child[0][0]
        
        if not child_age:
            all_scores = execute_db('''
                SELECT AVG(overall_score)
                FROM session_summaries
                WHERE overall_score IS NOT NULL
                GROUP BY child_id
            ''')
        else:
            age_range = 2
            all_scores = execute_db('''
                SELECT AVG(ss.overall_score)
                FROM session_summaries ss
                JOIN children c ON ss.child_id = c.id
                WHERE ss.overall_score IS NOT NULL 
                AND c.age BETWEEN ? AND ?
                GROUP BY ss.child_id
            ''', (child_age - age_range, child_age + age_range))
        
        if not all_scores:
            return 50
        
        scores_list = [s[0] for s in all_scores if s[0] is not None]
        
        if not scores_list:
            return 50
        
        scores_list.sort()
        
        count_below = sum(1 for s in scores_list if s < score)
        percentile = int((count_below / len(scores_list)) * 100)
        
        return min(100, max(0, percentile))
    
    @staticmethod
    def calculate_improvement_rate(child_id: int, current_score: float) -> float:
        """计算提升率"""
        last_report = execute_db('''
            SELECT total_score, created_at
            FROM child_reports
            WHERE child_id = ? AND report_type = 'attention'
            ORDER BY created_at DESC
            LIMIT 1
        ''', (child_id,))
        
        if not last_report:
            return 0.0
        
        previous_score = last_report[0][0]
        
        if previous_score is None or previous_score == 0:
            return 0.0
        
        improvement_rate = ((current_score - previous_score) / previous_score) * 100
        
        return round(improvement_rate, 2)

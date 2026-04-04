import math
from config import SCORING_WEIGHTS, PERFORMANCE_LEVELS, DEFAULT_GAME_DATA


def clamp(value, min_val=0, max_val=1):
    if value is None:
        return 0
    return max(min_val, min(max_val, value))


def calculate_head_stable(head_yaw_list, head_pitch_list):
    if not head_yaw_list or not head_pitch_list:
        return 0.0
    
    yaw_std = calculate_std(head_yaw_list)
    pitch_std = calculate_std(head_pitch_list)
    combined_std = math.sqrt(yaw_std ** 2 + pitch_std ** 2)
    
    head_stable = 1 - (combined_std / 30)
    return clamp(head_stable)


def calculate_face_stable(face_distance_list):
    if not face_distance_list or len(face_distance_list) < 2:
        return 1.0
    
    changes = []
    for i in range(1, len(face_distance_list)):
        if face_distance_list[i-1] > 0:
            change_rate = abs(face_distance_list[i] - face_distance_list[i-1]) / face_distance_list[i-1]
            changes.append(change_rate)
    
    if not changes:
        return 1.0
    
    avg_change_rate = sum(changes) / len(changes)
    face_stable = 1 - (avg_change_rate / 50)
    return clamp(face_stable)


def calculate_blink_stable(blink_count_list, sample_interval_ms=500):
    if not blink_count_list:
        return 1.0
    
    total_blinks = sum(blink_count_list)
    total_time_min = (len(blink_count_list) * sample_interval_ms) / 60000
    
    if total_time_min == 0:
        return 1.0
    
    blink_rate = total_blinks / total_time_min
    blink_stable = 1 - (blink_rate / 25)
    return clamp(blink_stable)


def calculate_std(values):
    if not values or len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def calculate_selective_score(game_data, vision_scores):
    weights = SCORING_WEIGHTS['selective']
    
    correct = game_data.get('correct', 0)
    error = game_data.get('error', 0)
    miss = game_data.get('miss', 0)
    time = game_data.get('time', 0)
    
    total_target = game_data.get('total_target', 1)
    if total_target == 0:
        total_target = 1
    
    accuracy = correct / (correct + miss) if (correct + miss) > 0 else 0
    precision = correct / (correct + error) if (correct + error) > 0 else 0
    speed = 1 - (time / 60)
    speed = clamp(speed)
    
    head_stable = vision_scores.get('head_stable', 0)
    blink_stable = vision_scores.get('blink_stable', 0)
    
    score = (
        accuracy * weights['accuracy'] +
        precision * weights['precision'] +
        speed * weights['speed'] +
        head_stable * weights['head_stable'] +
        blink_stable * weights['blink_stable']
    )
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'speed': speed,
        'head_stable': head_stable,
        'blink_stable': blink_stable,
        'final_score': clamp(score * 100, 0, 100)
    }


def calculate_sustained_score(game_data, vision_scores):
    weights = SCORING_WEIGHTS['sustained']
    
    correct = game_data.get('correct', 0)
    error = game_data.get('error', 0)
    leave = game_data.get('leave', 0)
    time = game_data.get('time', 0)
    total_step = game_data.get('total_step', 1)
    late_error_ratio = game_data.get('late_error_ratio', 0)
    
    if total_step == 0:
        total_step = 1
    
    speed = 1 - (time / 120)
    speed = clamp(speed)
    
    stable_act = 1 - (error + leave) / total_step
    stable_act = clamp(stable_act)
    
    no_fatigue = 1 - late_error_ratio
    no_fatigue = clamp(no_fatigue)
    
    head_stable = vision_scores.get('head_stable', 0)
    blink_stable = vision_scores.get('blink_stable', 0)
    
    score = (
        stable_act * weights['stable_act'] +
        no_fatigue * weights['no_fatigue'] +
        speed * weights['speed'] +
        head_stable * weights['head_stable'] +
        blink_stable * weights['blink_stable']
    )
    
    return {
        'stable_act': stable_act,
        'no_fatigue': no_fatigue,
        'speed': speed,
        'head_stable': head_stable,
        'blink_stable': blink_stable,
        'final_score': clamp(score * 100, 0, 100)
    }


def calculate_tracking_score(game_data, vision_scores):
    weights = SCORING_WEIGHTS['tracking']
    
    correct = game_data.get('correct', 0)
    error = game_data.get('error', 0)
    time = game_data.get('time', 0)
    total_click = game_data.get('total_click', 1)
    mean_rt = game_data.get('mean_rt', 1000)
    
    if total_click == 0:
        total_click = 1
    
    acc = correct / total_click
    acc = clamp(acc)
    
    speed = 1 - (time / 60)
    speed = clamp(speed)
    
    rt_score = 1 - (mean_rt / 1000)
    rt_score = clamp(rt_score)
    
    head_stable = vision_scores.get('head_stable', 0)
    face_stable = vision_scores.get('face_stable', 0)
    
    score = (
        acc * weights['accuracy'] +
        rt_score * weights['rt_score'] +
        speed * weights['speed'] +
        head_stable * weights['head_stable'] +
        face_stable * weights['face_stable']
    )
    
    return {
        'accuracy': acc,
        'rt_score': rt_score,
        'speed': speed,
        'head_stable': head_stable,
        'face_stable': face_stable,
        'final_score': clamp(score * 100, 0, 100)
    }


def calculate_memory_score(game_data, vision_scores):
    weights = SCORING_WEIGHTS['memory']
    
    correct = game_data.get('correct', 0)
    error = game_data.get('error', 0)
    time = game_data.get('time', 0)
    memory_load = game_data.get('memory_load', 1)
    order_error = game_data.get('order_error', 0)
    
    if memory_load == 0:
        memory_load = 1
    
    acc = correct / (correct + error) if (correct + error) > 0 else 0
    acc = clamp(acc)
    
    speed = 1 - (time / 60)
    speed = clamp(speed)
    
    order = 1 - (order_error / memory_load)
    order = clamp(order)
    
    head_stable = vision_scores.get('head_stable', 0)
    blink_stable = vision_scores.get('blink_stable', 0)
    
    score = (
        acc * weights['accuracy'] +
        order * weights['order'] +
        speed * weights['speed'] +
        head_stable * weights['head_stable'] +
        blink_stable * weights['blink_stable']
    )
    
    return {
        'accuracy': acc,
        'order': order,
        'speed': speed,
        'head_stable': head_stable,
        'blink_stable': blink_stable,
        'final_score': clamp(score * 100, 0, 100)
    }


def calculate_inhibitory_score(game_data, vision_scores):
    weights = SCORING_WEIGHTS['inhibitory']
    
    correct = game_data.get('correct', 0)
    error = game_data.get('error', 0)
    obstacle = game_data.get('obstacle', 0)
    total_trial = game_data.get('total_trial', 1)
    
    if total_trial == 0:
        total_trial = 1
    
    acc = correct / total_trial
    acc = clamp(acc)
    
    impulse = 1 - (error + obstacle) / total_trial
    impulse = clamp(impulse)
    
    head_stable = vision_scores.get('head_stable', 0)
    face_stable = vision_scores.get('face_stable', 0)
    blink_stable = vision_scores.get('blink_stable', 0)
    
    score = (
        impulse * weights['impulse'] +
        acc * weights['accuracy'] +
        head_stable * weights['head_stable'] +
        face_stable * weights['face_stable'] +
        blink_stable * weights['blink_stable']
    )
    
    return {
        'impulse': impulse,
        'accuracy': acc,
        'head_stable': head_stable,
        'face_stable': face_stable,
        'blink_stable': blink_stable,
        'final_score': clamp(score * 100, 0, 100)
    }


def get_performance_level(score):
    if score >= PERFORMANCE_LEVELS['excellent']['min']:
        return PERFORMANCE_LEVELS['excellent']['name']
    elif score >= PERFORMANCE_LEVELS['good']['min']:
        return PERFORMANCE_LEVELS['good']['name']
    elif score >= PERFORMANCE_LEVELS['average']['min']:
        return PERFORMANCE_LEVELS['average']['name']
    else:
        return PERFORMANCE_LEVELS['weak']['name']


def calculate_score(attention_type, game_data, vision_scores):
    game_data = {**DEFAULT_GAME_DATA, **game_data}
    
    calculators = {
        'selective': calculate_selective_score,
        'sustained': calculate_sustained_score,
        'tracking': calculate_tracking_score,
        'memory': calculate_memory_score,
        'inhibitory': calculate_inhibitory_score
    }
    
    calculator = calculators.get(attention_type)
    if not calculator:
        return {
            'final_score': 0,
            'performance_level': '较弱',
            'error': f'未知的注意力类型: {attention_type}'
        }
    
    result = calculator(game_data, vision_scores)
    result['performance_level'] = get_performance_level(result['final_score'])
    
    return result


def calculate_vision_scores(vision_data_list):
    if not vision_data_list:
        return {
            'head_stable': 0.5,
            'face_stable': 0.5,
            'blink_stable': 0.5
        }
    
    head_yaw_list = []
    head_pitch_list = []
    face_distance_list = []
    blink_count_list = []
    
    for data in vision_data_list:
        if data.get('head_yaw') is not None:
            head_yaw_list.append(data['head_yaw'])
        if data.get('head_pitch') is not None:
            head_pitch_list.append(data['head_pitch'])
        if data.get('face_distance') is not None:
            face_distance_list.append(data['face_distance'])
        if data.get('blink_count') is not None:
            blink_count_list.append(data['blink_count'])
    
    return {
        'head_stable': calculate_head_stable(head_yaw_list, head_pitch_list),
        'face_stable': calculate_face_stable(face_distance_list),
        'blink_stable': calculate_blink_stable(blink_count_list)
    }


class ScoringEngine:
    @staticmethod
    def calculate_head_stability(head_yaw, head_pitch):
        return calculate_head_stable([head_yaw] if head_yaw else [], [head_pitch] if head_pitch else [])
    
    @staticmethod
    def calculate_overall_score(vision_data, game_data):
        vision_scores = calculate_vision_scores([vision_data] if vision_data else [])
        return {
            'visual_score': vision_scores,
            'game_score': game_data
        }

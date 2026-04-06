import { 
    TrainingSessionManager, 
    GAME_TYPES, 
    ATTENTION_TYPES 
} from './training.js';
import { showError, ERROR_CODES } from './errors.js';
import { isAuthenticated, setToken, removeToken } from './request.js';

const trainingManager = new TrainingSessionManager();

async function runTrainingExample(childId, gameType) {
    if (!isAuthenticated()) {
        alert('请先登录');
        window.location.href = '/login.html';
        return;
    }
    
    try {
        const startResult = await trainingManager.start(childId, gameType);
        
        if (!startResult.success) {
            showError(startResult.error.code, startResult.error.message);
            return;
        }
        
        console.log('训练会话已创建:', startResult.data);
        const sessionId = startResult.data.session_id;
        
        const gameLoop = async () => {
            const visionResult = await trainingManager.uploadVision({
                head_yaw: 5.2,
                head_pitch: -3.1,
                face_distance: 150.5,
                blink_count: 0
            });
            
            if (!visionResult.success) {
                console.warn('视觉数据上传失败:', visionResult.error);
            }
            
            const gameResult = await trainingManager.uploadGame('game_result', {
                time: 45,
                correct: 8,
                error: 2,
                miss: 1,
                total_target: 10
            });
            
            if (!gameResult.success) {
                console.warn('游戏数据上传失败:', gameResult.error);
            }
        };
        
        await gameLoop();
        
        const endResult = await trainingManager.end();
        
        if (endResult.success) {
            console.log('训练结束:', endResult.data);
            displayTrainingResult(endResult.data);
        } else {
            showError(endResult.error.code, endResult.error.message);
        }
        
    } catch (error) {
        console.error('训练过程出错:', error);
        await trainingManager.interrupt({ progress: 50 });
    }
}

function displayTrainingResult(result) {
    const { summary, earned_badges, recommendations } = result;
    
    console.log('最终得分:', summary.final_score);
    console.log('表现等级:', summary.performance_level);
    console.log('获得勋章:', earned_badges);
    console.log('建议:', recommendations);
    
    alert(`训练完成！\n得分: ${summary.final_score}\n等级: ${summary.performance_level}`);
}

async function viewTrainingHistory(childId) {
    const result = await getTrainingHistory(childId, {
        limit: 10,
        offset: 0
    });
    
    if (result.success) {
        const { total, records } = result.data;
        console.log(`共 ${total} 条记录`);
        records.forEach(record => {
            console.log(`${record.game_name}: ${record.final_score}分 (${record.performance_level})`);
        });
    } else {
        showError(result.error.code, result.error.message);
    }
}

async function viewTrainingTrend(childId) {
    const result = await getTrainingTrend(childId, { days: 30 });
    
    if (result.success) {
        const { trend, overall } = result.data;
        console.log('总体平均分:', overall.avg_score);
        console.log('训练次数:', overall.total_sessions);
        
        Object.entries(trend).forEach(([type, data]) => {
            if (data.records.length > 0) {
                console.log(`${ATTENTION_TYPES[type]}: ${data.avg_score}分, 趋势: ${data.trend}`);
            }
        });
    } else {
        showError(result.error.code, result.error.message);
    }
}

function handleLoginSuccess(token) {
    setToken(token);
    window.location.href = '/child-home.html';
}

function handleLogout() {
    removeToken();
    window.location.href = '/login.html';
}

export {
    runTrainingExample,
    viewTrainingHistory,
    viewTrainingTrend,
    handleLoginSuccess,
    handleLogout,
    trainingManager
};

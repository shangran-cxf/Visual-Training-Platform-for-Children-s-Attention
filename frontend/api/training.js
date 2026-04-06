import { apiGet, apiPost, generateUUID } from './request.js';
import { ERROR_CODES, GAME_TYPES, ATTENTION_TYPES } from './config.js';
import { showError, handleSessionExpired, handleActiveSessionExists } from './errors.js';

async function startTrainingSession(childId, gameType, deviceId = 'web-browser') {
    const result = await apiPost('/api/training/session/start', {
        child_id: childId,
        game_type: gameType,
        device_id: deviceId
    });
    
    if (!result.success && result.error?.code === ERROR_CODES.ACTIVE_SESSION_EXISTS) {
        const continueSession = handleActiveSessionExists(null);
        if (continueSession) {
            return { success: false, shouldContinue: true };
        }
    }
    
    return result;
}

async function endTrainingSession(sessionId) {
    return apiPost('/api/training/session/end', {
        session_id: sessionId
    });
}

async function sendHeartbeat(sessionId) {
    return apiPost('/api/training/session/heartbeat', {
        session_id: sessionId
    });
}

async function interruptTrainingSession(sessionId, currentState = null) {
    return apiPost('/api/training/session/interrupt', {
        session_id: sessionId,
        current_state: currentState
    });
}

async function uploadVisionData(sessionId, data) {
    return apiPost('/api/training/vision-data', {
        session_id: sessionId,
        request_id: generateUUID(),
        timestamp: new Date().toISOString(),
        ...data
    });
}

async function uploadGameData(sessionId, eventType, data) {
    return apiPost('/api/training/game-data', {
        session_id: sessionId,
        request_id: generateUUID(),
        timestamp: new Date().toISOString(),
        event_type: eventType,
        ...data
    });
}

async function getTrainingHistory(childId, params = {}) {
    return apiGet(`/api/training/history/${childId}`, params);
}

async function getTrainingDetail(sessionId) {
    return apiGet(`/api/training/detail/${sessionId}`);
}

async function getTrainingTrend(childId, params = {}) {
    return apiGet(`/api/training/trend/${childId}`, params);
}

class TrainingSessionManager {
    constructor() {
        this.sessionId = null;
        this.heartbeatInterval = null;
        this.heartbeatFrequency = 30000;
    }
    
    async start(childId, gameType, deviceId = 'web-browser') {
        const result = await startTrainingSession(childId, gameType, deviceId);
        
        if (result.success) {
            this.sessionId = result.data.session_id;
            this.startHeartbeat();
        }
        
        return result;
    }
    
    startHeartbeat() {
        this.stopHeartbeat();
        
        this.heartbeatInterval = setInterval(async () => {
            if (this.sessionId) {
                const result = await sendHeartbeat(this.sessionId);
                if (!result.success) {
                    console.warn('Heartbeat failed:', result.error);
                    if (result.error?.code === ERROR_CODES.SESSION_EXPIRED) {
                        this.stopHeartbeat();
                        handleSessionExpired();
                    }
                }
            }
        }, this.heartbeatFrequency);
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    async end() {
        this.stopHeartbeat();
        
        if (this.sessionId) {
            const result = await endTrainingSession(this.sessionId);
            this.sessionId = null;
            return result;
        }
        
        return { success: false, error: { code: 'NO_SESSION', message: '没有活跃的会话' } };
    }
    
    async interrupt(currentState = null) {
        this.stopHeartbeat();
        
        if (this.sessionId) {
            const result = await interruptTrainingSession(this.sessionId, currentState);
            this.sessionId = null;
            return result;
        }
        
        return { success: false, error: { code: 'NO_SESSION', message: '没有活跃的会话' } };
    }
    
    async uploadVision(data) {
        if (!this.sessionId) {
            return { success: false, error: { code: 'NO_SESSION', message: '没有活跃的会话' } };
        }
        return uploadVisionData(this.sessionId, data);
    }
    
    async uploadGame(eventType, data) {
        if (!this.sessionId) {
            return { success: false, error: { code: 'NO_SESSION', message: '没有活跃的会话' } };
        }
        return uploadGameData(this.sessionId, eventType, data);
    }
    
    getActiveSessionId() {
        return this.sessionId;
    }
    
    isActive() {
        return !!this.sessionId;
    }
}

export {
    startTrainingSession,
    endTrainingSession,
    sendHeartbeat,
    interruptTrainingSession,
    uploadVisionData,
    uploadGameData,
    getTrainingHistory,
    getTrainingDetail,
    getTrainingTrend,
    TrainingSessionManager,
    GAME_TYPES,
    ATTENTION_TYPES
};

/**
 * Vision Data Uploader
 * Reads window.__visionBridge__ (exposed by floating-ball.js) at 2 Hz and
 * uploads frames to POST /api/training/vision-data.
 *
 * Frames are buffered from page-load so that the entire gameplay period
 * is captured, even though the session is created at game-end.
 *
 * Usage:
 *   visionUploader.start(sessionId)   // flushes buffer + begins live upload
 *   visionUploader.stop()             // stops live upload (keeps sessionId for in-flight flushes)
 */
(function () {
  var intervalId = null;
  var sessionId = null;
  var lastBlinkCount = 0;
  var UPLOAD_INTERVAL_MS = 500;
  var MAX_BUFFER_FRAMES = 600; // 5 minutes at 2 Hz

  // ── Frame buffer: collects from page-load, flushed on start() ──
  var frameBuffer = [];
  var collectIntervalId = null;
  var framesCollected = 0;

  console.log('[vision-uploader] 初始化，开始缓冲帧数据...');

  function getBaseUrl() {
    return window.location.origin;
  }

  function getAuthHeaders() {
    return {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + (localStorage.getItem('auth_token') || ''),
    };
  }

  function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0;
      var v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function sampleFrame() {
    var v = window.__visionBridge__;
    if (!v) return null;
    return {
      attention_score: v.attentionScore || 0,
      face_detected: v.isFaceDetected ? 1 : 0,
      head_yaw: v.headYaw || 0,
      head_pitch: v.headPitch || 0,
      face_area: v.faceArea || 0,
      face_distance: v.faceArea || 0,
      blink_rate: v.blinkRate || 0,
      blink_total: v.blinkCount || 0,
      focus_duration: UPLOAD_INTERVAL_MS / 1000,
      timestamp: new Date().toISOString(),
    };
  }

  // ── Always-on collection (runs from page load) ──
  function collectFrame() {
    var frame = sampleFrame();
    if (frame) {
      frameBuffer.push(frame);
      framesCollected++;
      if (frameBuffer.length > MAX_BUFFER_FRAMES) {
        frameBuffer.shift();
      }
    }
  }

  // Start collecting immediately
  collectIntervalId = setInterval(collectFrame, UPLOAD_INTERVAL_MS);

  // ── Upload a single frame ──
  function uploadOneFrame(frame, blinkDelta, sid) {
    // 用传入的 sid，不读外层的 sessionId（避免 stop() 竞态）
    var effectiveSid = sid || sessionId;
    if (!effectiveSid) return Promise.resolve();
    return fetch(getBaseUrl() + '/api/training/vision-data', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        session_id: effectiveSid,
        request_id: generateUUID(),
        timestamp: frame.timestamp || new Date().toISOString(),
        attention_score: frame.attention_score,
        face_detected: frame.face_detected,
        head_yaw: frame.head_yaw,
        head_pitch: frame.head_pitch,
        face_area: frame.face_area,
        face_distance: frame.face_distance,
        blink_rate: frame.blink_rate,
        blink_count: blinkDelta || 0,
        focus_duration: frame.focus_duration,
      }),
    }).catch(function () {
      // 静默忽略上传错误
    });
  }

  // ── Flush buffered frames with computed blink deltas ──
  function flushAndStart(sid) {
    var buffered = frameBuffer.slice();
    frameBuffer = [];
    var count = buffered.length;

    console.log('[vision-uploader] 开始上传 ' + count + ' 帧缓冲数据 (session: ' + sid + ')');

    var prevBlinkTotal = 0;
    var chain = Promise.resolve();
    for (var i = 0; i < buffered.length; i++) {
      var frame = buffered[i];
      var blinkTotal = frame.blink_total || 0;
      var blinkDelta = 0;
      if (i === 0) {
        blinkDelta = Math.max(0, blinkTotal - lastBlinkCount);
      } else {
        blinkDelta = Math.max(0, blinkTotal - prevBlinkTotal);
      }
      prevBlinkTotal = blinkTotal;
      chain = chain.then(function () {
        return uploadOneFrame(frame, blinkDelta, sid);
      });
    }

    // Update lastBlinkCount to the final buffered value
    if (buffered.length > 0) {
      lastBlinkCount = buffered[buffered.length - 1].blink_total || lastBlinkCount;
    }

    return chain;
  }

  // ── Live upload (called by setInterval after start) ──
  function liveUploadFrame() {
    var frame = sampleFrame();
    if (!frame) return;
    var blinkTotal = frame.blink_total || 0;
    var blinkDelta = Math.max(0, blinkTotal - lastBlinkCount);
    lastBlinkCount = blinkTotal;
    // 用闭包中的 sessionId（stop() 不再清它）
    uploadOneFrame(frame, blinkDelta, sessionId);
  }

  // ── Public API ──
  window.visionUploader = {
    // 返回 Promise，resolve 时所有缓冲帧已上传完毕
    start: function (sid) {
      sessionId = sid;
      console.log(
        '[vision-uploader] start() — session=' + sid + ', 缓冲帧=' + frameBuffer.length + ', 已采集=' + framesCollected,
      );
      // Flush all frames collected during gameplay
      var flushPromise = flushAndStart(sid);
      // Then begin live upload
      if (intervalId) clearInterval(intervalId);
      intervalId = setInterval(liveUploadFrame, UPLOAD_INTERVAL_MS);
      return flushPromise;
    },

    stop: function () {
      console.log('[vision-uploader] stop() — 缓冲帧=' + frameBuffer.length + ', 已采集=' + framesCollected);
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
      // 不清 sessionId，保证正在飞的 flushAndStart 请求不丢失
    },
  };
})();

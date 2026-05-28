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
 *   visionUploader.stop()             // stops upload
 */
(function () {
  let intervalId = null;
  let sessionId = null;
  let lastBlinkCount = 0;
  const UPLOAD_INTERVAL_MS = 500;
  const MAX_BUFFER_FRAMES = 600; // 5 minutes at 2 Hz

  // ── Frame buffer: collects from page-load, flushed on start() ──
  let frameBuffer = [];
  let collectIntervalId = null;

  function getBaseUrl() {
    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    return isLocal ? 'http://localhost:5000' : window.location.origin;
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
      if (frameBuffer.length > MAX_BUFFER_FRAMES) {
        frameBuffer.shift();
      }
    }
  }

  // Start collecting immediately
  collectIntervalId = setInterval(collectFrame, UPLOAD_INTERVAL_MS);

  // ── Upload a single frame ──
  async function uploadOneFrame(frame, blinkDelta) {
    try {
      await fetch(getBaseUrl() + '/api/training/vision-data', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          session_id: sessionId,
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
      });
    } catch (e) {
      // Silently ignore upload errors
    }
  }

  // ── Flush buffered frames with computed blink deltas ──
  async function flushAndStart() {
    var buffered = frameBuffer.slice();
    frameBuffer = [];

    var prevBlinkTotal = 0;
    for (var i = 0; i < buffered.length; i++) {
      var frame = buffered[i];
      var blinkTotal = frame.blink_total || 0;
      var blinkDelta = 0;
      if (i === 0) {
        // First frame: delta from last known count before this session
        blinkDelta = Math.max(0, blinkTotal - lastBlinkCount);
      } else {
        blinkDelta = Math.max(0, blinkTotal - prevBlinkTotal);
      }
      prevBlinkTotal = blinkTotal;
      await uploadOneFrame(frame, blinkDelta);
    }

    // Update lastBlinkCount to the final buffered value
    if (buffered.length > 0) {
      lastBlinkCount = buffered[buffered.length - 1].blink_total || lastBlinkCount;
    }
  }

  // ── Live upload (called by setInterval after start) ──
  function liveUploadFrame() {
    var frame = sampleFrame();
    if (!frame) return;
    var blinkTotal = frame.blink_total || 0;
    var blinkDelta = Math.max(0, blinkTotal - lastBlinkCount);
    lastBlinkCount = blinkTotal;
    uploadOneFrame(frame, blinkDelta);
  }

  // ── Public API ──
  window.visionUploader = {
    start: function (sid) {
      sessionId = sid;
      // Flush all frames collected during gameplay
      flushAndStart();
      // Then begin live upload
      if (intervalId) clearInterval(intervalId);
      intervalId = setInterval(liveUploadFrame, UPLOAD_INTERVAL_MS);
    },

    stop: function () {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
      sessionId = null;
    },
  };
})();

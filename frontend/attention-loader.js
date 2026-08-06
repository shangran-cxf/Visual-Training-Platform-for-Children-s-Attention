/**
 * 专注力检测自动加载器
 * 在所有游戏页面自动添加悬浮小球
 */

(function () {
  if (window.attentionLoaded) return;
  window.attentionLoaded = true;

  const path = window.location.pathname;
  const isGamePage = path.includes('/training/') || path.includes('/detect/');
  if (!isGamePage) return;

  console.log('🎯 专注力检测模块加载中...');

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  async function init() {
    await loadMediaPipe();
    await loadFloatingBall();
    console.log('✅ 专注力检测模块已启动');
  }

  function loadMediaPipe() {
    return new Promise((resolve) => {
      if (window.FilesetResolver && window.FaceLandmarker) {
        resolve();
        return;
      }

      // 使用 +esm 端点获取真正的 ES Module 版本
      const importMap = document.createElement('script');
      importMap.type = 'importmap';
      importMap.textContent = JSON.stringify({
        imports: {
          '@mediapipe/tasks-vision': 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/+esm',
        },
      });
      document.head.appendChild(importMap);

      const moduleScript = document.createElement('script');
      moduleScript.type = 'module';
      moduleScript.textContent = `
        import * as mp from '@mediapipe/tasks-vision';
        window.FilesetResolver = mp.FilesetResolver;
        window.FaceLandmarker = mp.FaceLandmarker;
      `;
      moduleScript.onload = () => {
        const checkInterval = setInterval(() => {
          if (window.FilesetResolver && window.FaceLandmarker) {
            clearInterval(checkInterval);
            resolve();
          }
        }, 50);
        setTimeout(() => {
          clearInterval(checkInterval);
          resolve();
        }, 5000);
      };
      moduleScript.onerror = () => {
        console.error('MediaPipe ESM 加载失败');
        resolve();
      };
      document.head.appendChild(moduleScript);
    });
  }

  function loadFloatingBall() {
    return new Promise((resolve) => {
      if (document.getElementById('floating-attention-ball')) {
        resolve();
        return;
      }
      const script = document.createElement('script');
      script.src = '../floating-ball.js';
      script.onload = resolve;
      document.head.appendChild(script);
    });
  }
})();

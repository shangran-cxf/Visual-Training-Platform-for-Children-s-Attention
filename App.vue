<template>
  <div class="container">
    <h1>儿童专注力视觉训练</h1>
    <p class="subtitle">MediaPipe Face Mesh - 实时人脸关键点检测</p>
    
    <div class="video-container">
      <video ref="videoElement" autoplay muted playsinline></video>
      <canvas ref="canvasElement"></canvas>
    </div>
    
    <div class="controls">
      <button @click="startCamera" :disabled="cameraRunning" class="btn-primary">
        🎥 启动摄像头
      </button>
      <button @click="stopCamera" :disabled="!cameraRunning" class="btn-secondary">
        ⏹️ 停止摄像头
      </button>
    </div>
    
    <div class="status">
      <p>📊 状态: {{ status }}</p>
      <p v-if="faceCount > 0" class="face-count">👤 检测到 {{ faceCount }} 张人脸</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { FilesetResolver, FaceLandmarker } from '@mediapipe/tasks-vision'

// DOM 元素引用
const videoElement = ref(null)
const canvasElement = ref(null)

// 状态变量
const status = ref('未启动')
const cameraRunning = ref(false)
const faceCount = ref(0)

// MediaPipe 实例
let faceLandmarker = null
let animationId = null
let stream = null

// 初始化人脸检测模型
const initFaceLandmarker = async () => {
  status.value = '🔄 加载模型中...'
  try {
    const vision = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision/wasm"
    )
    
    faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        delegate: "GPU"
      },
      runningMode: "VIDEO",
      numFaces: 1,                                //控制人脸数量
      refineLandmarks: true,                      // 细化关键点（嘴唇、眼睛）
      minFaceDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
      outputFaceBlendshapes: true,                // 开启表情
      outputFacialTransformationMatrixes: true    // 开启头部姿态
    })
    
    status.value = '✅ 模型加载完成，点击启动摄像头'
    console.log('FaceLandmarker 初始化成功，支持表情:', !!faceLandmarker)
  } catch (err) {
    console.error('模型加载失败:', err)
    status.value = '❌ 模型加载失败，请刷新页面重试'
  }
}

// 启动摄像头
const startCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    videoElement.value.srcObject = stream
    await videoElement.value.play()
    
    // 设置 canvas 尺寸
    canvasElement.value.width = videoElement.value.videoWidth
    canvasElement.value.height = videoElement.value.videoHeight
    
    cameraRunning.value = true
    status.value = '🔍 检测中...'
    
    // 开始检测循环
    detectFrame()
  } catch (err) {
    console.error('摄像头启动失败:', err)
    status.value = '❌ 摄像头启动失败，请检查权限'
  }
}

// 停止摄像头
const stopCamera = () => {
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  cameraRunning.value = false
  faceCount.value = 0
  status.value = '⏸️ 摄像头已停止'
  
  // 清空 canvas
  const ctx = canvasElement.value.getContext('2d')
  ctx.clearRect(0, 0, canvasElement.value.width, canvasElement.value.height)
}

// 人脸检测循环
const detectFrame = () => {
  if (!cameraRunning.value || !faceLandmarker) return
  
  const video = videoElement.value
  const canvas = canvasElement.value
  const ctx = canvas.getContext('2d')
  
  if (video.videoWidth && video.videoHeight) {
    const results = faceLandmarker.detectForVideo(video, performance.now())
    
    // 输出结果的所有属性
    console.log('=== 检测结果详情 ===')
    console.log('结果的所有属性:', Object.keys(results))
    console.log('faceLandmarks 数量:', results.faceLandmarks?.length || 0)
    console.log('faceBlendshapes:', results.faceBlendshapes)
    console.log('facialTransformationMatrixes:', results.facialTransformationMatrixes)
    
    // 检查是否有其他可能的属性名
    if (results.blendshapes) console.log('blendshapes:', results.blendshapes)
    if (results.matrixes) console.log('matrixes:', results.matrixes)
    
    // 如果有关键点，输出第一个点的坐标
    if (results.faceLandmarks && results.faceLandmarks.length > 0) {
      const firstPoint = results.faceLandmarks[0][0]
      console.log('第一个关键点(鼻尖)坐标:', firstPoint)
    }
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    
    if (results.faceLandmarks && results.faceLandmarks.length > 0) {
      faceCount.value = results.faceLandmarks.length
    } else {
      faceCount.value = 0
    }
  }
  
  animationId = requestAnimationFrame(detectFrame)
}

// 绘制连接线的辅助函数
const drawConnectors = (ctx, landmarks, connections, style) => {
  ctx.beginPath()
  for (const connection of connections) {
    const start = landmarks[connection[0]]
    const end = landmarks[connection[1]]
    if (start && end) {
      ctx.moveTo(start.x * canvasElement.value.width, start.y * canvasElement.value.height)
      ctx.lineTo(end.x * canvasElement.value.width, end.y * canvasElement.value.height)
    }
  }
  ctx.strokeStyle = style.color
  ctx.lineWidth = style.lineWidth
  ctx.stroke()
}

// 绘制关键点的辅助函数
const drawLandmarks = (ctx, landmarks, style) => {
  for (const landmark of landmarks) {
    ctx.beginPath()
    ctx.arc(
      landmark.x * canvasElement.value.width,
      landmark.y * canvasElement.value.height,
      style.radius,
      0,
      2 * Math.PI
    )
    ctx.fillStyle = style.color
    ctx.fill()
  }
}

// 页面加载时初始化模型
initFaceLandmarker()

// 组件销毁时清理资源
onBeforeUnmount(() => {
  stopCamera()
  if (faceLandmarker) {
    faceLandmarker.close()
  }
})
</script>

<style scoped>
.container {
  text-align: center;
  padding: 20px;
  font-family: 'Microsoft YaHei', Arial, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

h1 {
  color: white;
  margin-bottom: 10px;
  font-size: 2rem;
}

.subtitle {
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 30px;
}

.video-container {
  position: relative;
  width: 800px;
  height: 600px;
  margin: 0 auto;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  background: #000;
}

video, canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

video {
  opacity: 0;
}

.controls {
  margin-top: 30px;
  display: flex;
  gap: 20px;
  justify-content: center;
}

button {
  padding: 12px 32px;
  font-size: 16px;
  font-weight: bold;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background-color: #4CAF50;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #45a049;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
}

.btn-secondary {
  background-color: #f44336;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #da190b;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(244, 67, 54, 0.4);
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  transform: none;
}

.status {
  margin-top: 30px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  display: inline-block;
  min-width: 300px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.status p {
  margin: 5px 0;
  font-size: 16px;
  color: #333;
}

.face-count {
  font-size: 18px;
  font-weight: bold;
  color: #4CAF50;
}
</style>
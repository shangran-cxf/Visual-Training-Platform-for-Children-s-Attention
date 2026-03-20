<template>
  <div class="container">
    <h1>儿童专注力视觉训练</h1>
    
    <div class="video-container">
      <video ref="videoElement" autoplay muted playsinline></video>
      <canvas ref="canvasElement"></canvas>
    </div>
    
    <div class="controls">
      <button @click="startCamera" :disabled="cameraRunning" class="btn-start">
        🎥 开始拍摄
      </button>
      <button @click="stopCamera" :disabled="!cameraRunning" class="btn-stop">
        ⏹️ 停止拍摄
      </button>
      <button @click="exportData" :disabled="collectedData.length === 0" class="btn-export">
        📥 导出数据
      </button>
    </div>
    
    <div class="status">
      <p>状态: {{ status }}</p>
      <p v-if="faceCount > 0">检测到 {{ faceCount }} 张人脸</p>
      <p v-if="collectedData.length > 0">已收集 {{ collectedData.length }} 帧数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { FilesetResolver, FaceLandmarker } from '@mediapipe/tasks-vision'

// DOM 元素
const videoElement = ref(null)
const canvasElement = ref(null)

// 状态
const status = ref('未启动')
const cameraRunning = ref(false)
const faceCount = ref(0)
const collectedData = ref([])

// MediaPipe 实例
let faceLandmarker = null
let animationId = null
let stream = null

// 初始化模型
const initFaceLandmarker = async () => {
  status.value = '加载模型中...'
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
      numFaces: 1,
      outputFaceBlendshapes: true,
      outputFacialTransformationMatrixes: true,
      minFaceDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    })
    
    status.value = '✅ 就绪，点击开始拍摄'
  } catch (err) {
    console.error(err)
    status.value = '模型加载失败'
  }
}

// 开始拍摄
const startCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    videoElement.value.srcObject = stream
    await videoElement.value.play()
    
    canvasElement.value.width = videoElement.value.videoWidth
    canvasElement.value.height = videoElement.value.videoHeight
    
    cameraRunning.value = true
    status.value = '🔍 拍摄中，数据自动收集...'
    
    // 开始检测循环
    detectFrame()
  } catch (err) {
    console.error(err)
    status.value = '摄像头启动失败'
  }
}

// 停止拍摄
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
  status.value = '⏸️ 已停止'
}

// 检测循环
const detectFrame = () => {
  if (!cameraRunning.value || !faceLandmarker) {
    animationId = requestAnimationFrame(detectFrame)
    return
  }
  
  const video = videoElement.value
  const canvas = canvasElement.value
  const ctx = canvas.getContext('2d')
  
  if (video.videoWidth && video.videoHeight) {
    const results = faceLandmarker.detectForVideo(video, performance.now())
    
    // 自动收集数据
    collectedData.value.push({
      timestamp: Date.now(),
      results: results
    })
    
    // 绘制画面
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    
    // 更新人脸数量
    faceCount.value = results.faceLandmarks?.length || 0
  }
  
  animationId = requestAnimationFrame(detectFrame)
}

// 导出数据
const exportData = () => {
  if (collectedData.value.length === 0) {
    alert('没有数据')
    return
  }
  
  const exportObj = {
    exportTime: new Date().toISOString(),
    totalFrames: collectedData.value.length,
    frames: collectedData.value
  }
  
  const jsonStr = JSON.stringify(exportObj, null, 2)
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `face_data_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  
  alert(`✅ 已导出 ${collectedData.value.length} 帧数据`)
}

// 初始化
initFaceLandmarker()

// 清理
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

h1 {
  color: white;
}

.video-container {
  position: relative;
  width: 800px;
  height: 600px;
  margin: 20px auto;
  border-radius: 16px;
  overflow: hidden;
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
  margin-top: 20px;
  display: flex;
  gap: 20px;
  justify-content: center;
}

button {
  padding: 12px 32px;
  font-size: 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.btn-start {
  background-color: #4CAF50;
  color: white;
}

.btn-stop {
  background-color: #f44336;
  color: white;
}

.btn-export {
  background-color: #2196f3;
  color: white;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.status {
  margin-top: 20px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  display: inline-block;
  min-width: 300px;
}
</style>

# MediaPipe Face Mesh 视觉模型导出数据格式说明
摄像头按帧进行拍摄,最后输出若干帧
其中,每帧都包含以下三个方面:
faceLandmarks（面部关键点） :包含478个关键点,输出xyz坐标
faceBlendshapes(表情参数)   :包含52个表情参数
facialTransformationMatrixes(4×4 矩阵):  显示头部旋转情况
---

## 一、faceLandmarks（面部关键点）

### 图片示例
```json
{
    "x": 0.5110673904418945,
    "y": 0.44461679458618164,
    "z": 0.0256019476801157,
    "visibility": 0
}
```

### 参数含义

| 参数 | 类型 | 含义 | 取值范围 |
|------|------|------|----------|
| **x** | float | 水平坐标 | 0 = 最左，1 = 最右 |
| **y** | float | 垂直坐标 | 0 = 最上，1 = 最下 |
| **z** | float | 深度坐标 | 负值 = 向前凸出，正值 = 向后凹陷 |
| **visibility** | int | 可见性 | 0 = 可见（固定值，可忽略） |

### 格式说明
- 每个关键点是一个对象，包含 x, y, z, visibility
- 每帧包含 **478 个**这样的关键点，按固定索引顺序排列
- 所有坐标都是**归一化坐标**，与图像分辨率无关

---

## 二、faceBlendshapes（表情参数）

### 图片示例
```json
{
  "index": 18,
  "score": 0.19476306438446045,
  "categoryName": "eyeLookUpRight",
  "displayName": ""
}
```

### 参数含义

| 参数 | 类型 | 含义 | 取值范围 |
|------|------|------|----------|
| **index** | int | 参数编号 | 0 - 51 |
| **score** | float | 表情强度 | 0 = 无动作，1 = 最大强度 |
| **categoryName** | string | 参数名称 | 见下表 |
| **displayName** | string | 显示名称 | 通常为空 |

### 常见 categoryName 含义

| 参数名 | 含义 |
|--------|------|
| eyeBlinkLeft / Right | 眨眼 |
| eyeLookUp / Down / Left / Right | 眼球方向 |
| eyeSquintLeft / Right | 眯眼 |
| mouthSmile | 微笑 |
| jawOpen | 张嘴 |
| browInnerUp | 眉毛上扬 |
| browDownLeft / Right | 皱眉 |
| mouthPucker | 撅嘴 |

### 格式说明
- 每帧包含 **52 个**表情参数
- 每个参数是一个对象，包含 index, score, categoryName
- score 值越大，该表情动作越明显

---

## 三、facialTransformationMatrixes（头部姿态矩阵）

### 图片示例
```json
"facialTransformationMatrices": [
    {
    "rows": 4,
    "columns": 4,
    "data": [
    0.9977283477783203,
    -0.009112467989325523,
    -0.06675438582897186,
    0,
    0.038390178233385086,
    0.8911184668540955,
    0.45214468240737915,
    0,
    0.055365897715091705,
    -0.453680157661438,
    0.8894436359405518,
    0,
    -2.1606533527374268,
    9.273404121398926,
    -48.15559005737305,
    1
    ]
    }
]
```

### 参数含义

| 参数 | 含义 |
|------|------|
| **rows** | 行数，固定为 4 |
| **columns** | 列数，固定为 4 |
| **data** | 16 个浮点数，按行排列的 4×4 矩阵 |

### 矩阵结构
```
[ R11 R12 R13 Tx ]   ← 第1行
[ R21 R22 R23 Ty ]   ← 第2行
[ R31 R32 R33 Tz ]   ← 第3行
[ 0   0   0   1  ]   ← 第4行
```

### 各部分含义

| 部分 | 位置 | 含义 |
|------|------|------|
| **R (旋转矩阵)** | 左上角 3×3 | 头部的旋转（可计算 yaw, pitch, roll） |
| **T (平移向量)** | 右上角 3×1 | 头部的空间位置偏移 |
| **最后一行** | 第4行 | 固定为 [0,0,0,1] |

### 格式说明
- 每帧包含 **1 个** 4×4 变换矩阵
- data 数组长度为 16，按行优先顺序存储
- 矩阵描述头部在 3D 空间中的旋转和平移

---

## 四、总结：每帧数据完整结构

```json
{
  "timestamp": 1710921600000,           // 时间戳（毫秒）
  "results": {
    "faceLandmarks": [                  // 478 个关键点
      [
        {"x": 0.511, "y": 0.444, "z": 0.025, "visibility": 0},
        {"x": 0.512, "y": 0.445, "z": 0.024, "visibility": 0},
        ... // 共 478 个
      ]
    ],
    "faceBlendshapes": [                // 52 个表情参数
      [
        {"index": 0, "score": 0.000001, "categoryName": "_neutral"},
        {"index": 18, "score": 0.195, "categoryName": "eyeLookUpRight"},
        ... // 共 52 个
      ]
    ],
    "facialTransformationMatrixes": [   // 1 个 4×4 矩阵
      {
        "rows": 4,
        "columns": 4,
        "data": [16个浮点数]
      }
    ]
  }
}
```

---

## 五、数据用途速查

| 数据类型 | 主要用途 |
|----------|----------|
| **faceLandmarks** | 面部位置、是否正对、张嘴检测、微笑检测 |
| **faceBlendshapes** | 眨眼频率、情绪识别、专注度判断 |
| **facialTransformationMatrixes** | 头部转向、低头抬头、距离远近 |

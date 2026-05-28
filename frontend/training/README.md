# frontend/training/ — 注意力训练游戏

11 个游戏页面，覆盖五大注意力维度。

## 游戏列表

| 游戏 | 文件 | 训练维度 | 后端标识 |
|---|---|---|---|
| 太空小火箭（舒尔特方格） | `schulte.html` | 选择性注意 | schulte |
| 垃圾小卫士（找数字） | `find-numbers.html` | 选择性注意 | find-numbers |
| 魔法迷宫 | `magic-maze.html` | 持续性注意 | magic-maze |
| 浇花游戏 | `water-plants.html` | 持续性注意 | water-plants |
| 追踪太阳 | `sun-tracking.html` | 视觉追踪 | sun-tracking |
| 寻找动物 | `animal-searching.html` | 视觉追踪 | animal-searching |
| 记忆翻牌 | `card-matching.html` | 工作记忆 | card-matching |
| 甜品店小帮工 | `reverse-memory.html` | 工作记忆 | reverse-memory |
| 红绿灯 | `traffic-light.html` | 抑制控制 | traffic-light |
| 海底捉迷藏 | `command-adventure.html` | 抑制控制 | command-adventure |
| 红绿灯（备选版） | `trafficlight-game.html` | 抑制控制 | 无 |

## 注意力维度

| 维度 | 描述 | 对应游戏 |
|---|---|---|
| 选择性注意 | 目标搜索 + 抗干扰 + 速度 | 太空小火箭、垃圾小卫士 |
| 持续性注意 | 维持专注 + 抗疲劳 + 稳定性 | 魔法迷宫、浇花游戏 |
| 视觉追踪 | 眼球运动 + 轨迹跟随 | 追踪太阳、寻找动物 |
| 工作记忆 | 信息暂存 + 操作转换 | 记忆翻牌、倒序记忆 |
| 抑制控制 | 冲动抑制 + 行为控制 | 红绿灯、指令冒险 |

## 通用机制

- 每个游戏页面通过 `attention-loader.js` 自动加载面部检测
- 游戏过程中 `floating-ball.js` 实时采集视觉数据并上传
- 训练数据通过 `training.js` API 客户端发送到后端
- 所有页面独立包含 CSS（内联 `<style>`）和游戏逻辑（内联 `<script>`）

## 文件结构

```
frontend/training/
├── index.html          # 训练中心页面，根据评估数据推荐游戏
├── schulte.html        # 太空小火箭 - 舒尔特方格训练
├── find-numbers.html   # 垃圾小卫士 - 数字搜索训练
├── magic-maze.html     # 魔法迷宫 - 迷宫导航训练
├── water-plants.html   # 浇花游戏 - 持续注意训练
├── sun-tracking.html   # 追踪太阳 - 视觉追踪训练
├── animal-searching.html # 寻找动物 - 视觉搜索训练
├── card-matching.html  # 记忆翻牌 - 工作记忆训练
├── reverse-memory.html # 甜品店小帮工 - 序列记忆训练
├── traffic-light.html  # 红绿灯 - 抑制控制训练
├── command-adventure.html # 海底捉迷藏 - 抑制控制训练
├── trafficlight-game.html # 红绿灯（备选版，未接入后端）
└── README.md           # 本说明文件
```

## 数据流程

1. **前端游戏** → 收集游戏数据（得分、时间、正确率等）
2. **视觉采集** → 通过摄像头实时采集头部稳定度、面部稳定度、眨眼稳定度
3. **数据上传** → 通过 `/api/training/game-data` 接口上传游戏数据
4. **会话结束** → 通过 `/api/training/session/end` 接口提交最终得分
5. **后端计算** → 基于游戏数据和视觉数据计算综合评分
6. **存储展示** → 结果存储到数据库，供前端展示和分析

## 评分机制

每个游戏根据其训练维度采用不同的评分算法：
- **选择性注意**: 基于正确率、速度和视觉稳定性
- **持续性注意**: 基于任务完成度、时间和专注稳定性
- **视觉追踪**: 基于追踪准确度和头部运动稳定性
- **工作记忆**: 基于记忆准确率和反应时间
- **抑制控制**: 基于正确响应、错误响应和障碍规避

最终得分结合游戏表现（60%）和视觉注意力数据（40%）计算得出。

## 后端配置对应

后端 `config.py` 中的 `GAME_TYPES` 配置定义了游戏与注意力维度的映射关系：

| 后端标识 | 游戏名称 | 注意力类型 |
|---|---|---|
| schulte | 太空小火箭 | selective |
| find-numbers | 垃圾小卫士 | selective |
| magic-maze | 魔法迷宫 | sustained |
| water-plants | 浇花游戏 | sustained |
| sun-tracking | 追踪太阳 | tracking |
| animal-searching | 寻找动物 | tracking |
| card-matching | 记忆翻牌 | memory |
| reverse-memory | 倒序记忆 | memory |
| traffic-light | 红绿灯 | inhibitory |
| command-adventure | 指令冒险 | inhibitory |

> **注意**: `trafficlight-game.html` 是红绿灯游戏的备选版本，目前未在后端配置中注册，不参与正式训练评分。
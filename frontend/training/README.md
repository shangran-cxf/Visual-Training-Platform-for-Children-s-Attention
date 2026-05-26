# frontend/training/ — 注意力训练游戏

11 个游戏页面，覆盖五大注意力维度。

## 游戏列表

| 游戏 | 文件 | 训练维度 |
|---|---|---|
| 太空火箭（舒尔特方格） | `schulte.html` | 选择性注意、持续性注意 |
| 垃圾卫士（找数字） | `find-numbers.html` | 选择性注意 |
| 记忆翻牌 | `card-matching.html` | 工作记忆 |
| 倒序记忆 | `reverse-memory.html` | 工作记忆 |
| 红绿灯 | `traffic-light.html` | 抑制控制 |
| 红绿灯（备选版） | `trafficlight-game.html` | 抑制控制 |
| 指令冒险 | `command-adventure.html` | 抑制控制 |
| 魔法迷宫 | `magic-maze.html` | 持续性注意 |
| 阳光追踪 | `sun-tracking.html` | 视觉追踪 |
| 动物搜寻 | `animal-searching.html` | 视觉追踪 |
| 浇水植物 | `water-plants.html` | 持续性注意 |

## 通用机制

- 每个游戏页面通过 `attention-loader.js` 自动加载面部检测
- 游戏过程中 `floating-ball.js` 实时采集视觉数据并上传
- 训练数据通过 `training.js` API 客户端发送到后端
- 所有页面独立包含 CSS（内联 `<style>`）和游戏逻辑（内联 `<script>`）

## 游戏总览

`index.html` — 训练中心页面，根据评估数据推荐游戏。

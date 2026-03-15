# pacman_duel Agent 设计

## 1. 概述

本文档描述 Pacman、Slime 和 Helper 的运行时 agent 家族以及具体算法。

所有 agent 共享同一个运行时接口：

```python
class Agent(Protocol):
    def next_action(self, state: GameState, config: dict) -> Direction: ...
    def reset(self) -> None: ...
```

Agent 不允许直接修改 `GameState`，只能决定下一步动作。

## 2. Pacman Agents

Pacman agent 的目标是活下来并吃完所有豆子。

### `pacman/HumanAgent`

- 输入来源：UI 键盘输入
- 行为：返回输入层最近一次缓冲的方向
- 当前控制方式：方向键
- Reset 行为：把缓冲输入清回 `STAY`

### `pacman/RandomAgent`

- 目标：作为简单的 Pacman baseline 策略
- 决策规则：
  - 只在路口或拐角重新选方向
  - 如果有别的选项，就不要立刻掉头
  - 一旦选定方向，在走廊中持续直行
  - 只有在没有别的路可走时才允许回头
- 依赖共享的随机游走辅助逻辑：`src/algorithms/random_walk.py`

### `pacman/RLAgent`

- 状态：规划中，尚未实现
- 预期职责：加载 Pacman 阵营训练好的模型，只负责推理
- 约束：训练必须放在 gameplay 进程之外

## 3. Slime Agents

Slime agent 的目标是抓到 Pacman。

### `slime/RandomAgent`

- 目标：作为敌方阵营的简单 baseline
- 决策规则：
  - 只在路口或拐角重新选方向
  - 如果有别的选项，就不要立刻掉头
  - 一旦选定方向，在走廊中持续直行
  - 只有在死胡同时才允许回头
- 依赖共享的随机游走辅助逻辑：`src/algorithms/random_walk.py`

### `slime/ShortestPathAgent`

- 目标：尽可能直接地追 Pacman
- 路径算法：BFS 最短路径
- 默认目标：Pacman
- 行为：
  - 计算到目标角色的最短可行路径上的第一步
  - 如果已经到达目标，或者目标不可达，则返回 `STAY`

### `slime/CopycatAgent`

- 目标：先到达 Pacman 的起点，再模仿 Pacman 的路径
- 两阶段行为：
  1. 使用 BFS 寻路到 Pacman 的初始位置
  2. 精确回放 Pacman 的历史动作，包括 `STAY`
- 回放状态：
  - 内部维护 replay index
  - `reset()` 时回到 replay 起点

### `slime/RLAgent`

- 状态：规划中，尚未实现
- 预期职责：加载 slime 阵营训练好的模型，只负责推理
- 约束：训练必须放在 gameplay 进程之外

## 4. Helper Agents

Helper 属于 slime 阵营 agent 家族，但在玩法上还有额外的节奏限制。

### 角色说明

- Helper 使用 slime 阵营的 agent，而不是独立的第三类 agent。
- Helper 当前可以使用的 slime-side 算法包括：
  - `slime/RandomAgent`
  - `slime/ShortestPathAgent`
  - `slime/CopycatAgent`

### 速度缩放

- Helper 的移动速度有意设计得比 slime 更慢。
- 当前规则：
  - Helper 每隔 `HELPER_SPEED_SCALING_FACTOR` 个 tick 才移动一次
  - 其余 tick 中，helper 的动作会被转换成 `STAY`
- 这条节奏规则放在 rules 层统一处理，而不是写进每一个 helper 可用 agent 内部。

## 5. 配置规则

- Pacman 配置只能选择 Pacman-side agent。
- Slime 配置只能选择 slime-side agent。
- Helper 配置也只能选择 slime-side agent。
- `AppController` 负责在构造运行时 agent 时校验这些约束。

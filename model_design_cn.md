# pacman_duel 模型与训练设计文档

## 1. 目的

本文细化 `pacman_duel` 中 reinforcement learning 相关的设计，重点解释“后续 RL 训练可能需要额外的线程或进程隔离”这句话应该如何落地。

简化来说就是：

- 实时对局和 UI 必须保持响应
- RL 训练通常是长时间、重计算任务
- 训练过程应当与本地图形界面和对局主循环隔离
- 游戏运行时应当加载训练好的模型做推理，而不是在对局中直接训练

对这个项目来说，默认推荐“进程隔离”。基于线程的训练只适合作为轻量实验时的受限备选方案。

## 2. 核心问题

RL 训练和普通 agent 推理在运行特性上完全不同。

### 为什么训练不同

- 训练可能持续数分钟甚至数小时
- 它通常是 CPU 密集型任务，未来也可能占用 GPU
- 它可能分配较大的 replay buffer、rollout buffer 或 checkpoint
- 它可能需要多个并行环境
- 它可能因为 observation、reward 或第三方库问题而中途崩溃

### 为什么这会影响主程序

- GUI 事件循环可能卡死
- 对局 tick 主循环可能阻塞或漂移
- 一次训练失败可能把整个应用进程带崩
- 资源竞争会让胜率展示和本地输入不稳定
- UI、训练和游戏规则耦合后，测试和维护都会明显变难

## 3. 推荐设计

推荐把训练、推理和实时对局明确拆成三种职责。

### 推荐原则

- `core/` 负责游戏规则和状态推进
- `training/` 负责 RL 环境封装、训练入口和评估脚本
- `agents/rl_agent.py` 只负责推理
- `ui/` 和 `app.py` 不直接执行梯度更新或长时间训练循环

### 这意味着什么

在正常对局中：

- 应用加载一个已经训练好的模型
- `RLAgent` 把 `GameState` 转换成 observation
- 模型预测一个动作
- 引擎在当前 tick 内应用这个动作

在训练过程中：

- 独立训练进程创建一个或多个 RL 环境
- 训练器持续推进环境并更新模型
- checkpoint 定期保存到磁盘
- 游戏程序之后再加载这些 checkpoint 做推理

## 4. 为什么优先用进程隔离

线程和进程都可以把工作移出 UI 线程，但它们解决问题的能力并不相同。

### 进程的优势

- 崩溃隔离更好
- 内存边界更清晰
- 更适合 CPU 密集型任务
- 更容易终止、重启和监控
- 更适合与已经自行管理 worker 的训练库配合

### 线程的局限

- Python 的 `GIL` 会限制 CPU 密集型纯 Python 代码的收益
- 训练库仍然会和 GUI、主循环争抢资源
- 故障隔离较弱，因为所有逻辑仍在同一个进程里
- UI 线程和训练线程混用后，调试会更脆弱

### 结论

默认使用独立进程执行 RL 训练。线程仅用于日志转发、进度轮询、checkpoint 扫描这类轻量后台任务。

## 5. 建议目录结构

```text
pacman_duel/
  src/
    app.py
    algorithms/
      pathfinding.py
    core/
      board.py
      domain.py
      rules.py
      engine.py
    agents/
      base.py
      human.py
      random_agent.py
      shortest_path.py
      copycat.py
      rl_agent.py
    training/
      env.py
      observation.py
      reward.py
      train_rl.py
      evaluate_rl.py
      checkpoints.py
    stats/
      history_store.py
      winrate.py
      summaries.py
    ui/
      main_window.py
      menu_screen.py
      config_panel.py
      game_view.py
      stats_panel.py
    config/
      schemas.py
      presets.py
  models/
    checkpoints/
    exported/
  tests/
    test_rules.py
    test_pathfinding.py
    test_agents.py
    test_win_conditions.py
    test_training_env.py
```

## 6. 模块职责

### `src/core/`

- 定义棋盘、实体、规则和确定性的状态推进
- 必须独立于 UI 和 RL 框架
- 必须可以单独测试

### `src/algorithms/`

- 存放可复用算法，例如 BFS 路径搜索
- 可被 gameplay agent、评估代码以及未来的模型工具复用
- 可以依赖 `core/` 中的领域类型，但不应该承载游戏规则

### `src/training/env.py`

- 把核心引擎包装成 `gymnasium` 风格环境
- 处理 `reset()`、`step()`、observation、reward 和终止信号
- 不能依赖 GUI widget 或人工输入

### `src/training/observation.py`

- 把 `GameState` 转换为模型可消费的数组或张量
- 统一 observation 空间设计，避免训练和推理不一致

### `src/training/reward.py`

- 编码 reward shaping 规则
- 让奖励逻辑显式、可版本化

### `src/training/train_rl.py`

- 作为训练入口脚本
- 创建环境、模型、callback 和 checkpoint 策略
- 应能被单独命令行运行

### `src/training/evaluate_rl.py`

- 离线评估训练结果与基线 agent 的对战表现
- 输出后续可供 UI 或模型选择使用的指标

### `src/training/checkpoints.py`

- 定义 checkpoint 的命名、元数据和保留策略
- 统一文件布局和模型元信息

### `src/agents/rl_agent.py`

- 从磁盘加载训练好的模型
- 把当前状态转成 observation
- 为当前 tick 返回一个动作
- 不负责训练

## 7. 运行时边界

建议保持以下清晰边界：

- 对局进程：UI、对局主循环、历史记录、推理
- 训练进程：环境 rollout、模型更新、checkpoint 写入
- 文件边界：checkpoint 与元数据

### 可以跨边界传递的数据

- 模型路径
- 模型元数据
- 可选的训练进度快照
- 评估结果摘要

### 不应直接跨边界共享的数据

- 活跃的 GUI widget
- 可变的对局会话对象
- UI 和训练器共享的内存态 engine 实例

## 8. 训练流程

### 离线训练流程

1. 构建或选择训练配置
2. 在独立进程中启动 `train_rl.py`
3. 创建一个或多个基于 `core/` 的训练环境
4. 周期性保存 checkpoint
5. 与基线 agent 做离线评估
6. 将某个 checkpoint 标记为可用于对局推理

### 对局推理流程

1. 用户在 UI 中选择基于 RL 的 agent
2. 应用加载某个 checkpoint 及其元数据
3. `RLAgent` 把当前 `GameState` 转换成 observation
4. 模型预测一个动作
5. 引擎像处理其他 agent 一样应用该动作

## 9. 建议接口

具体实现可以调整，但接口边界应保持收敛。

### 推理侧 agent

```python
class RLAgent(Agent):
    def __init__(self, model_path: str, encoder: ObservationEncoder) -> None: ...
    def next_action(self, state: GameState, config: dict) -> Direction: ...
    def reset(self) -> None: ...
```

### 训练侧环境

```python
class PacmanDuelEnv(gym.Env):
    def reset(self, *, seed: int | None = None, options: dict | None = None): ...
    def step(self, action: int): ...
```

这里最重要的不是类签名本身，而是训练和推理要共享同一套 observation 与 action 约定，同时不把 UI 逻辑混进来。

## 10. 如果以后要在应用里触发训练

如果产品后面需要一个“Train Model”按钮，也应当把训练委托给子进程，而不是直接在应用主进程里跑。

### 安全模式

- UI 启动一个子进程
- 子进程运行 `train_rl.py`
- 通过日志、轮询或简单本地 IPC 回报进度
- checkpoint 写入磁盘
- UI 只展示状态，不自己执行训练步骤

### 应避免

- 在 GUI 主线程里跑完整训练循环
- 在 `RLAgent` 内直接调用训练逻辑
- 让实时对局和训练器共享同一个可变 engine 状态

## 11. 最小可行落地方案

项目的第一个 RL 里程碑不需要一开始就把训练完全集成进应用。

### Phase 1

- `RLAgent` 先做占位实现或仅负责加载模型
- 先把 `core/` 做成可测试、可复用、确定性的引擎
- 增加 `training/env.py` 包装
- 增加独立脚本 `train_rl.py`

### Phase 2

- 统一 checkpoint 和元数据格式
- 增加对 `RandomAgent`、`ShortestPathAgent` 的离线评估
- 在 UI 中增加模型选择入口

### Phase 3

- 增加可选的“应用管理的子进程训练”
- 增加训练进度展示和 checkpoint 管理
- 增加多套训练预设

## 12. 测试策略

建议从三层验证这个架构。

### 核心规则测试

- 规则执行是否确定
- 胜负判定是否正确
- 合法动作约束是否稳定

### 训练环境测试

- `reset()` 和 `step()` 的接口契约
- reward 行为
- 终止条件
- observation 编码一致性

### 推理测试

- 模型加载
- observation 到 action 的调用链
- checkpoint 缺失或损坏时的安全降级行为

## 13. 最终建议

对 `pacman_duel` 来说，应从一开始就把 RL 训练设计成“离线任务”或“子进程隔离任务”。

这样可以同时保证：

- 游戏响应性
- 架构模块化
- 核心规则可复用
- RL 技术栈可替换
- 后续网页前端和本地 GUI 都更容易接入

如果只保留一条原则，那就是：对局只做推理，训练放到别处。

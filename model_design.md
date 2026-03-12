# pacman_duel Model and Training Design

## 1. Purpose

This document refines the reinforcement learning portion of `pacman_duel`, especially the statement that RL training may require thread or process isolation later.

The short version is:

- real-time gameplay and UI must stay responsive
- RL training is long-running and compute-heavy
- training should be isolated from the local GUI and match session loop
- the runtime game should load trained models for inference instead of training inside the match

For this project, process isolation is the recommended default. Thread-based training should be treated as a limited fallback for lightweight experiments only.

## 2. Main Problem

Training an RL policy has very different runtime characteristics from ordinary agent inference.

### Why training is different

- It can run for minutes or hours.
- It is often CPU-heavy and may also use GPU resources later.
- It may allocate large replay buffers, rollout buffers, or model checkpoints.
- It may need multiple parallel environments.
- It may crash due to invalid observations, unstable rewards, or third-party library issues.

### Why this is risky inside the main app

- The GUI event loop can freeze.
- The match tick loop can stall or drift.
- A training failure can take down the entire app process.
- Resource contention can make win-rate display and local controls unreliable.
- The architecture becomes harder to test because UI, training, and game logic become coupled.

## 3. Recommended Design

The recommended design is to keep training, inference, and gameplay as separate responsibilities.

### Recommended rule

- `core/` owns the game rules and state transitions.
- `training/` owns RL environment wrappers, training entry points, and evaluation scripts.
- `agents/rl_agent.py` owns inference only.
- `ui/` and `app.py` must never run gradient updates or long training loops directly.

### Practical consequence

During a normal match:

- the app loads a saved model
- `RLAgent` converts `GameState` into an observation
- the model predicts an action
- the engine applies the action as part of the current tick

During training:

- a separate training process creates one or more RL environments
- the trainer steps the environments repeatedly
- checkpoints are saved to disk
- the gameplay app can later load one of those checkpoints

## 4. Why Process Isolation Is Preferred

Both threads and processes can move work off the UI thread, but they do not solve the same problems equally well.

### Benefits of processes

- Better crash isolation
- Cleaner memory ownership
- Better fit for CPU-bound workloads
- Easier to terminate, restart, and monitor
- Better compatibility with libraries that already manage their own worker threads

### Limits of threads

- Python's `GIL` reduces usefulness for CPU-heavy pure Python code
- Training libraries may still compete with the GUI and main loop for resources
- Fault isolation is weak because everything still lives in one process
- Debugging mixed UI and training thread interactions is more fragile

### Recommendation

Use a separate process for RL training by default. Use threads only for short-lived background tasks such as log streaming, progress polling, or light checkpoint discovery.

## 5. Proposed Directory Layout

```text
pacman_duel/
  src/
    app.py
    core/
      board.py
      models.py
      rules.py
      engine.py
      pathfinding.py
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

## 6. Module Responsibilities

### `src/core/`

- Defines the board, entities, rules, and deterministic state transitions
- Must stay independent from UI and RL frameworks
- Must be easy to test in isolation

### `src/training/env.py`

- Wraps the core engine as a `gymnasium`-style environment
- Handles `reset()`, `step()`, `observation`, `reward`, and termination signals
- Must not depend on GUI widgets or user input

### `src/training/observation.py`

- Converts `GameState` into model-ready tensors or arrays
- Centralizes observation-space decisions so gameplay inference and training stay aligned

### `src/training/reward.py`

- Encodes reward shaping rules
- Keeps reward logic explicit and versionable

### `src/training/train_rl.py`

- Runs the training entry point
- Builds environments, models, callbacks, and checkpoint policies
- Should be executable as a standalone command

### `src/training/evaluate_rl.py`

- Runs offline evaluation against baseline agents
- Produces metrics that can later inform UI summaries or model selection

### `src/training/checkpoints.py`

- Defines checkpoint naming, metadata, and retention policy
- Keeps file layout and model metadata consistent

### `src/agents/rl_agent.py`

- Loads a trained model from disk
- Converts the current state into an observation
- Returns one action for the current tick
- Must not perform training

## 7. Runtime Boundaries

The clean boundary is:

- gameplay process: match loop, UI, history, inference
- training process: environment rollout, model updates, checkpoint writes
- file boundary: saved checkpoints and metadata

### Data that crosses the boundary

- model path
- model metadata
- optional training progress snapshots
- evaluation summaries

### Data that should not cross directly

- live GUI widgets
- mutable game-session objects
- in-memory engine instances shared between UI and trainer

## 8. Training Workflow

### Offline training workflow

1. Build or select a training configuration.
2. Start `train_rl.py` in a separate process.
3. Create one or more training environments backed by `core/`.
4. Save checkpoints periodically.
5. Run evaluation against baseline agents.
6. Mark a checkpoint as ready for gameplay inference.

### Gameplay inference workflow

1. User selects an RL-backed agent in the UI.
2. The app loads a saved checkpoint and metadata.
3. `RLAgent` converts the current `GameState` into an observation.
4. The model predicts an action.
5. The engine applies the action in the same way as any other agent.

## 9. Suggested Interfaces

The exact implementation can vary, but the interfaces should stay narrow.

### Inference-side agent

```python
class RLAgent(Agent):
    def __init__(self, model_path: str, encoder: ObservationEncoder) -> None: ...
    def next_action(self, state: GameState, config: dict) -> Direction: ...
    def reset(self) -> None: ...
```

### Training-side environment

```python
class PacmanDuelEnv(gym.Env):
    def reset(self, *, seed: int | None = None, options: dict | None = None): ...
    def step(self, action: int): ...
```

The important point is not the exact class signature. The important point is that inference and training use the same observation and action conventions without sharing UI concerns.

## 10. If Training Must Be Triggered From the App

If the product later needs a "Train Model" button, the app should still delegate training to a subprocess.

### Safe pattern

- UI starts a subprocess
- subprocess runs `train_rl.py`
- progress is reported through logs, polling, or a simple local IPC channel
- checkpoints are written to disk
- UI displays status but does not execute training steps itself

### Avoid

- Running a full training loop in the main GUI thread
- Calling training code directly inside `RLAgent`
- Sharing mutable engine state between a live match and the trainer

## 11. Minimum Viable Plan

For the first RL milestone, the project does not need full integrated training support.

### Phase 1

- Keep `RLAgent` as a placeholder or model-loader only
- Implement `core/` so it is deterministic and testable
- Add a `training/env.py` wrapper
- Add a standalone `train_rl.py`

### Phase 2

- Save checkpoints and metadata in a stable format
- Add offline evaluation against `RandomAgent` and `ShortestPathAgent`
- Expose model selection in the UI

### Phase 3

- Add optional app-managed subprocess training
- Add progress display and checkpoint management
- Add support for multiple training presets

## 12. Testing Strategy

The architecture should be validated with tests at three levels.

### Core tests

- deterministic rule execution
- correct win/loss conditions
- stable legal-action behavior

### Training environment tests

- `reset()` and `step()` shape and contract
- reward behavior
- termination behavior
- observation encoding consistency

### Inference tests

- model loading
- observation-to-action path
- safe fallback behavior when checkpoint files are missing or invalid

## 13. Final Recommendation

For `pacman_duel`, RL training should be designed as an offline or subprocess-isolated workflow from the beginning.

This keeps:

- the game responsive
- the architecture modular
- the core rules reusable
- the RL stack replaceable
- future web and GUI frontends simpler

If there is only one rule to preserve, it is this: gameplay performs inference, while training happens elsewhere.

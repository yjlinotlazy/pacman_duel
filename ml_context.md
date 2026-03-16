# pacman_duel ML Context

## Purpose

This file records the current reinforcement-learning implementation boundary for `pacman_duel`.

The immediate goal remains to keep gameplay inference and training separate, but the first runtime and training scaffolding is now implemented.

## Current Architectural Seam

The existing runtime already has a clean integration point for RL agents:

- [src/agents/base.py](/home/yli/e/Dropbox/github/pacman_duel/src/agents/base.py) defines the shared `Agent` protocol:
  - `next_action(state, config) -> Direction`
  - `reset() -> None`
- [src/game_session.py](/home/yli/e/Dropbox/github/pacman_duel/src/game_session.py) only asks each agent for one action per tick.
- [src/app_controller.py](/home/yli/e/Dropbox/github/pacman_duel/src/app_controller.py) is responsible for constructing agent instances from `AgentConfig`.
- [src/core/](/home/yli/e/Dropbox/github/pacman_duel/src/core) contains deterministic rules and should remain independent from ML frameworks.

Because of this, RL should be added as a new agent implementation, not as a special case in the game loop or rules engine.

## Design Principle

Treat RL as just another action source behind the existing `Agent` protocol.

That means:

- `GameSession` should not know whether an action came from human input, BFS, random walk, or a neural network.
- `core/` should remain unchanged unless a genuinely shared domain abstraction is needed.
- Training code should remain separate from live gameplay inference.

## Current Runtime Files

Inference-side runtime agents:

- `src/agents/pacman/rl.py`
- `src/agents/slime/rl.py`

These files implement the same runtime interface as existing agents.

Shared RL support modules:

- `src/agents/rl/encoding.py`
- `src/agents/rl/checkpoints.py`
- `src/agents/rl/action_mapping.py`
- `src/agents/rl/runner.py`

Training-side scaffolding:

- `src/training/env.py`
- `src/training/observation.py`
- `src/training/reward.py`
- `src/training/train_rl.py`
- `src/training/checkpoints.py`
- `src/training/evaluate_rl.py`

## Why Separate Pacman And Slime RL Agents

Pacman-side and slime-side policies should remain separate unless later evidence shows a unified policy contract is actually better.

Reasons:

- Their objectives differ.
- Their observations may need different feature emphasis.
- Slime-side behavior may need explicit role awareness for `SLIME` vs `HELPER`.
- Separate runtime classes make checkpoint validation and future debugging more explicit.

## Inference Flow

The current per-tick RL inference flow is:

1. Receive `GameState` in `next_action`.
2. Encode the state into a deterministic observation for the acting role.
3. Run a checkpoint-backed policy runner.
4. Convert the selected action index into `Direction`.
5. Return the mapped direction.
6. If output is malformed or unsupported, fall back safely.

The gameplay engine and rules remain responsible for normal action sanitization.

## Observation Contract

The current observation encoder returns a typed dataclass, `EncodedObservation`.

Current interface:

```python
def encode_observation(state: GameState, role: Role) -> EncodedObservation:
    ...
```

Current properties:

- Deterministic for identical inputs.
- Independent from UI state.
- Versioned.
- Role-aware.
- Safe to call once per tick.

Current version:

- `OBSERVATION_VERSION = "v2"`

Current contents include:

- role and tick metadata
- board size
- actor, Pacman, slime, helper, and start positions
- sorted dot and wall coordinates
- Pacman history

The dataclass also exposes:

- `as_dict()` for structured serialization/debugging
- `flat_features()` for a stable numeric feature vector shared by the training scaffold and simple inference runners

## Action Mapping Contract

Define one fixed mapping between model action indices and runtime `Direction` values.

Recommended mapping:

```python
ACTION_INDEX_TO_DIRECTION = (
    Direction.UP,
    Direction.LEFT,
    Direction.DOWN,
    Direction.RIGHT,
    Direction.STAY,
)
```

Rationale:

- It is explicit and easy to test.
- It matches existing directional concepts already used by the runtime.
- Including `STAY` makes the policy space complete and avoids hidden runtime assumptions.

The reverse mapping should be defined in the same module if training code will need it.

## Checkpoint Metadata Requirements

Checkpoint loading currently validates metadata before an RL agent is allowed to act.

Required metadata should include:

- `schema_version`
- `role_family` with values such as `pacman` or `slime`
- `observation_version`
- `action_mapping_version`
- runner-specific policy payload

Current checkpoint policy formats:

- `runner_type = "static_scores"`
  - fixed `action_scores`
- `runner_type = "linear"`
  - `weights`
  - `bias`

The long-term checkpoint format can evolve, but the runtime now expects a checkpoint to produce a runner object rather than exposing raw checkpoint contents to the agent.

Training-side checkpoint export is now centralized in `src/training/checkpoints.py`.

Current conventions:

- filenames are timestamped and role-prefixed
- payloads are written in a runtime-compatible JSON format
- metadata always includes schema, observation, and action-mapping versions
- retention can prune older checkpoints by role family

If metadata does not match the runtime contract, the load should fail fast with a clear error.

## AppController Integration

[src/app_controller.py](/home/yli/e/Dropbox/github/pacman_duel/src/app_controller.py) should remain the only place that translates user-facing config into concrete runtime agents.

Current additions:

- Pacman-side config should allow algorithm `"rl"`.
- Slime-side config should allow algorithm `"rl"`.
- The GUI now exposes RL controller selections and checkpoint path fields per role.

Expected `AgentConfig.params` keys for RL agents:

- `checkpoint_path`
- optional `device`
- optional role-specific parameters if later required

This keeps runtime construction explicit and consistent with how baseline agents are currently created.

## Failure Handling

RL agent code should fail safely and predictably.

Current handling:

- invalid checkpoint path: fail agent construction with clear error
- metadata mismatch: fail agent construction with clear error
- malformed static checkpoint payload: fail checkpoint load with clear error
- malformed runner outputs: return `Direction.STAY`
- unsupported action index: return `Direction.STAY`
- invalid UI start configuration: show a status error instead of crashing the app

The runtime should never crash mid-match because a model returned an unexpected value if that case can be handled locally and safely.

## Reset Behavior

`reset()` should clear any per-match cached state held by the RL agent.

Examples:

- recurrent hidden state, if that is added later
- rolling observation buffers, if they are introduced later

If the first implementation is stateless inference, `reset()` can be a no-op for protocol compatibility.

## Testing Priorities

Milestone 6 has focused on contract stability, not model quality.

Tests should cover:

- observation encoding shape/content stability
- action-index mapping stability
- checkpoint metadata validation
- runner parsing and simple inference behavior
- `AppController` construction of Pacman and slime RL agents
- RL checkpoint path selection in the config panel
- start-match UI error handling for missing RL checkpoints
- training environment reset/step/reward scaffolding

The key objective is to make the runtime contract stable before implementing any real training workflow.

## Current Status

Implemented:

- RL agents are available through `AppController`.
- RL options and checkpoint paths are available in the GUI config panel.
- The app handles missing or invalid RL startup config without crashing.
- A runner boundary exists between agents and checkpoint payloads.
- A shared observation contract is used by both runtime inference and training scaffolding.
- A minimal standalone training package exists outside the UI and gameplay loop.
- Training-side checkpoint save/export helpers exist with retention support.
- Offline evaluation can run RL checkpoints against baseline agents and summarize results.

Still intentionally deferred:

- real ML framework integration
- checkpoint save/export conventions from training
- offline evaluation tooling
- richer training environment action handling for uncontrolled roles
- app-managed training orchestration

## Recommended Next Steps

1. Add checkpoint save/export conventions so training artifacts match runtime expectations.
2. Replace placeholder training episode logic with a real training loop.
3. Expand policy runner support beyond `static_scores` and `linear`.
4. Add richer evaluation reporting and checkpoint-selection workflows in the app.
5. Add operational logging and richer failure diagnostics around checkpoint loading and inference.

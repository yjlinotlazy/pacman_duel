# pacman_duel ML Context

## Purpose

This file records the intended implementation approach for reinforcement-learning-backed agents in `pacman_duel`.

The immediate goal is inference-only RL agents that fit the current runtime architecture without leaking training concerns into gameplay code.

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

## Planned Runtime Files

Add these inference-side runtime agents:

- `src/agents/pacman/rl.py`
- `src/agents/slime/rl.py`

These files should implement the same runtime interface as existing agents.

Likely supporting modules:

- `src/agents/rl/encoding.py`
- `src/agents/rl/checkpoints.py`
- `src/agents/rl/action_mapping.py`

These support modules should hold shared ML-facing contracts so they are not duplicated across Pacman-side and slime-side agents.

## Why Separate Pacman And Slime RL Agents

Pacman-side and slime-side policies should remain separate unless later evidence shows a unified policy contract is actually better.

Reasons:

- Their objectives differ.
- Their observations may need different feature emphasis.
- Slime-side behavior may need explicit role awareness for `SLIME` vs `HELPER`.
- Separate runtime classes make checkpoint validation and future debugging more explicit.

## Inference Flow

The intended per-tick RL inference flow is:

1. Receive `GameState` in `next_action`.
2. Encode the state into a deterministic observation for the acting role.
3. Run one model forward pass.
4. Convert the selected action index into `Direction`.
5. Return the mapped direction.
6. If output is malformed or unsupported, fall back safely.

The gameplay engine and rules remain responsible for normal action sanitization.

## Observation Contract

Define one stable observation encoder function that takes current immutable game state and acting role, then returns an ML-friendly observation object.

Tentative interface:

```python
def encode_observation(state: GameState, role: Role) -> object:
    ...
```

Requirements:

- Deterministic for identical inputs.
- Independent from UI state.
- Stable enough to be versioned.
- Role-aware.
- Safe to call once per tick.

The exact tensor format can evolve, but the contract must be versioned and tested once introduced.

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

Checkpoint loading should validate metadata before an RL agent is allowed to act.

Required metadata should include:

- `schema_version`
- `role_family` with values such as `pacman` or `slime`
- `observation_version`
- `action_mapping_version`
- model-specific architecture identifier if needed

Optional metadata may include:

- training board assumptions
- reward version
- expected framework/runtime version

If metadata does not match the runtime contract, the load should fail fast with a clear error.

## AppController Integration

[src/app_controller.py](/home/yli/e/Dropbox/github/pacman_duel/src/app_controller.py) should remain the only place that translates user-facing config into concrete runtime agents.

Planned additions:

- Pacman-side config should allow algorithm `"rl"`.
- Slime-side config should allow algorithm `"rl"`.

Expected `AgentConfig.params` keys for RL agents:

- `checkpoint_path`
- optional `device`
- optional role-specific parameters if later required

This keeps runtime construction explicit and consistent with how baseline agents are currently created.

## Failure Handling

RL agent code should fail safely and predictably.

Expected handling:

- invalid checkpoint path: fail agent construction with clear error
- metadata mismatch: fail agent construction with clear error
- malformed model output: return `Direction.STAY`
- unsupported action index: return `Direction.STAY`

The runtime should never crash mid-match because a model returned an unexpected value if that case can be handled locally and safely.

## Reset Behavior

`reset()` should clear any per-match cached state held by the RL agent.

Examples:

- recurrent hidden state, if that is added later
- rolling observation buffers, if they are introduced later

If the first implementation is stateless inference, `reset()` can be a no-op for protocol compatibility.

## Testing Priorities

Milestone 6 should focus on contract stability, not model quality.

Tests should cover:

- observation encoding shape/content stability
- action-index mapping stability
- checkpoint metadata validation
- safe fallback for malformed outputs
- `AppController` construction of Pacman and slime RL agents

The key objective is to make the runtime contract stable before implementing any real training workflow.

## Non-Goals For The First RL Pass

The first RL integration should not:

- embed training loops into gameplay code
- add ML framework dependencies into `src/core/`
- make `GameSession` aware of RL-specific logic
- optimize for advanced inference features before the contract is stable

## Recommended Next Steps

1. Add shared RL contract helpers for observation encoding, checkpoint validation, and action mapping.
2. Add inference-only RL agent classes under `src/agents/pacman/` and `src/agents/slime/`.
3. Extend `AppController` to construct RL agents from `AgentConfig`.
4. Add tests that lock down the observation/action/checkpoint contract.
5. Only after that, implement the standalone training package under a separate `training/` area.

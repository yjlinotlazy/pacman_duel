# pacman_duel Agent Design

## 1. Overview

This document describes the runtime agent families and the concrete algorithms used by Pacman, Slime, and Helper.

All agents share the same runtime contract:

```python
class Agent(Protocol):
    def next_action(self, state: GameState, config: dict) -> Direction: ...
    def reset(self) -> None: ...
```

Agents must not mutate `GameState`. They only choose the next action.

## 2. Pacman Agents

Pacman agents optimize for survival and clearing all dots.

### `pacman/HumanAgent`

- Input source: UI keyboard input
- Behavior: returns the most recent buffered direction from the input layer
- Current controls: arrow keys
- Reset behavior: clears buffered input back to `STAY`

### `pacman/RandomAgent`

- Goal: provide a simple baseline Pacman policy
- Decision rule:
  - choose a new direction only at intersections or corners
  - avoid immediately reversing direction when other options exist
  - keep moving straight through corridors once a direction has been chosen
  - reverse only when no direction other than going back is available
- Uses the shared corridor-aware random-walk helper in `src/algorithms/random_walk.py`

### `pacman/RLAgent`

- Status: planned, not yet implemented
- Expected role: load a Pacman-side trained model and run inference only
- Constraint: training must stay outside the gameplay process

## 3. Slime Agents

Slime agents optimize for catching Pacman.

### `slime/RandomAgent`

- Goal: provide a simple enemy-side baseline
- Decision rule:
  - choose a new direction only at intersections or corners
  - avoid immediately reversing direction when other options exist
  - keep moving straight through corridors once a direction has been chosen
  - reverse only when forced at a dead end
- Uses the shared corridor-aware random-walk helper in `src/algorithms/random_walk.py`

### `slime/ShortestPathAgent`

- Goal: chase Pacman as directly as possible
- Pathfinding: BFS shortest path
- Default target: Pacman
- Behavior:
  - compute the first step on a shortest walkable path toward the target role
  - return `STAY` if already at target or if no path exists

### `slime/CopycatAgent`

- Goal: imitate Pacman's path after reaching Pacman's start
- Two-phase behavior:
  1. Seek Pacman's initial position using BFS
  2. Replay Pacman's recorded action history exactly, including `STAY`
- Replay state:
  - maintains an internal replay index
  - `reset()` returns replay to the beginning

### `slime/RLAgent`

- Status: planned, not yet implemented
- Expected role: load a slime-side trained model and run inference only
- Constraint: training must stay outside the gameplay process

## 4. Helper Agents

Helper belongs to the slime-side family, but its gameplay behavior has an extra pacing rule.

### Role Notes

- Helper uses the same agent family as slime, not a separate third family.
- Helper can run slime-side algorithms such as:
  - `slime/RandomAgent`
  - `slime/ShortestPathAgent`
  - `slime/CopycatAgent`

### Movement Scaling

- Helper movement is intentionally slower than slime movement.
- Current rule:
  - Helper moves only once every `HELPER_SPEED_SCALING_FACTOR` ticks
  - On other ticks, helper action is converted to `STAY`
- This pacing is enforced in the rules layer, not inside each helper-capable agent implementation.

## 5. Configuration Rules

- Pacman-side config must only allow Pacman agents.
- Slime-side config must only allow slime-side agents.
- Helper config must also only allow slime-side agents.
- `AppController` is responsible for validating these constraints when constructing runtime agents.

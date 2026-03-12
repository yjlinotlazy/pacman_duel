# pacman_duel Design

## 1. Overview

`pacman_duel` is a Pacman-style duel game built around two opposing sides and pluggable AI strategies. The primary product goal is to help players understand reinforcement learning through direct play, observation, and comparison of different control algorithms.

- Pacman wins by eating all dots.
- The enemy side wins when either the slime or helper catches Pacman.
- If Pacman eats the last dot on the same tick that an enemy catches Pacman, Pacman wins.
- The system must support `Human vs AI`, `AI vs Human`, and `AI vs AI`.
- Advanced mode must support algorithm-specific parameters and win rate display based on stored historical results.

The design should prioritize:

- clean separation between game rules, AI logic, match history/statistics, and UI
- fast iteration for algorithms such as BFS and reinforcement learning
- support either a web UI or a local GUI, with Wayland support required for the local build
- testability of the core game rules without UI dependencies
- clear extension points for future boards, user-provided ML models, additional slimes, and cross-platform packaging

## 2. Recommended Tech Stack

### Primary stack

- Language: `Python 3.12+`
- GUI: `PySide6`
- Numeric utilities: `numpy`
- Validation/config schemas: `pydantic` or `dataclasses`
- Testing: `pytest`

### Optional later additions

- Reinforcement learning: `stable-baselines3`, `gymnasium`
- Packaging: `pyinstaller` or `briefcase`
- Web version later: `FastAPI + WebSocket` backend or a dedicated TypeScript frontend

### Why this stack

- `PySide6` is a good fit for a local GUI with menus, parameter panels, and history-based win-rate displays.
- Python keeps pathfinding, statistics processing, and AI iteration cheap.
- The game is small enough that Python performance should be sufficient if the core loop is kept simple.

### Pros

- Fast to prototype and extend
- Good fit for algorithm experimentation
- Strong separation between pure game logic and UI
- Easy to unit test

### Cons

- Supporting both local and web frontends will require clear boundaries around UI and session orchestration
- Python has lower performance headroom than Rust/C++
- RL training may require process/thread separation later; in practice, training should be isolated from gameplay and UI, with process isolation preferred. See `model_design.md` for the detailed design.

## 3. Architecture Summary

The system is split into five major layers:

1. `Core Game Engine`
2. `Agents / AI`
3. `Match History / Statistics`
4. `UI Layer`
5. `Application Orchestration`

![Architecture diagram](docs/diagrams/images/architecture.png)

Source: `docs/diagrams/mermaid/architecture.mmd`

## 4. Directory Layout

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
  tests/
    test_rules.py
    test_pathfinding.py
    test_agents.py
    test_win_conditions.py
```

## 5. Core Domain Model

The game should be a fixed-tick, grid-based state machine.

### Main entities

- `Pacman`
- `Slime`
- `Helper`
- `Board`
- `Dots`

### Core model responsibilities

- `Position`: immutable grid coordinates
- `EntityState`: per-character runtime state
- `Board`: walls, dots, bounds checks
- `GameState`: full snapshot of the match

![Domain model diagram](docs/diagrams/images/domain_model.png)

Source: `docs/diagrams/mermaid/domain_model.mmd`

### Suggested enums

- `Direction`: `UP`, `DOWN`, `LEFT`, `RIGHT`, `STAY`
- `Role`: `PACMAN`, `SLIME`, `HELPER`
- `MatchStatus`: `RUNNING`, `PACMAN_WIN`, `ENEMY_WIN`
- `Tile`: `WALL`, `DOT`, `EMPTY`

## 6. Engine and Rules

The engine owns state transitions. The rules layer owns the detailed mechanics.

### Tick order

1. Collect actions from all active controllers
2. Validate requested movement
3. Apply movement
4. Resolve dot consumption
5. Resolve capture
6. Resolve win/loss
7. Persist history needed by agents such as `Copycat`

![Tick flow diagram](docs/diagrams/images/tick_flow.png)

Source: `docs/diagrams/mermaid/tick_flow.mmd`

### Main classes

![Engine and rules diagram](docs/diagrams/images/engine_rules.png)

Source: `docs/diagrams/mermaid/engine_rules.mmd`

### Important rule decisions

- Invalid movement becomes `STAY`.
- The helper always exists as part of the enemy side.
- The helper uses shortest-path behavior by default.
- If final-dot consumption and capture happen on the same tick, Pacman wins.
- Pacman human control uses `UP`, `DOWN`, `LEFT`, `RIGHT`.
- `q` and `esc` are UI-level controls to leave the match and return to the main menu, not core rule logic.

## 7. Agent Design

Agents must not mutate the game state. They only return an action for the current tick.

### Agent interface

```python
class Agent(Protocol):
    def next_action(self, state: GameState, config: dict) -> Direction: ...
    def reset(self) -> None: ...
```

### Agent hierarchy

![Agent hierarchy diagram](docs/diagrams/images/agent_hierarchy.png)

Source: `docs/diagrams/mermaid/agent_hierarchy.mmd`

### Built-in strategies

#### `HumanAgent`

- Reads last valid input from UI
- Should be independent from direct widget logic

#### `RandomAgent`

- Chooses randomly from legal actions
- Useful as baseline and for smoke testing

#### `ShortestPathAgent`

- Uses BFS
- Slime target: current Pacman position
- Helper target: current Pacman position
- Configurable tie-breaking can be added later

#### `CopycatAgent`

Two-phase behavior:

1. Move toward Pacman's initial position
2. Replay Pacman's historical actions exactly, including optional `STAY`

![Copycat state diagram](docs/diagrams/images/copycat_state.png)

Source: `docs/diagrams/mermaid/copycat_state.mmd`

#### `RLAgent`

- Keep interface stable first
- A stub implementation is acceptable in the first milestone
- Training should stay outside the real-time UI loop

## 8. Application and Session Layer

The application layer coordinates screens, match setup, and session lifetime.

![Application and session diagram](docs/diagrams/images/app_session.png)

Source: `docs/diagrams/mermaid/app_session.mmd`

### Responsibilities

#### `MainWindow`

- owns current screen/widget tree
- routes menu and navigation events

#### `AppController`

- creates and destroys sessions
- translates UI selections into runtime configuration
- drives frame updates
- refreshes history-based win-rate summaries for the selected configuration

#### `GameSession`

- bundles one match config, its agents, and its engine
- provides the per-tick interface used by the UI timer

## 9. Match History and Win-Rate Statistics

Advanced mode shows win rates using stored real match results rather than simulated rollouts.

### Why it is a separate layer

- gameplay should persist every completed match result
- win-rate displays should come from historical data, not from synthetic simulations
- the storage layer should support later filtering by algorithm, parameter set, board, and version

### Main interfaces

```python
class MatchHistoryStore(Protocol):
    def record_result(self, result: MatchResult) -> None: ...
    def query_summary(self, query: StatsQuery) -> WinRateSummary: ...
```

### Result models

- `MatchResult`
  - winner
  - tick_count
  - pacman_controller
  - slime_controller
  - helper_controller
  - parameter_snapshot
  - board_id
  - played_at

- `WinRateSummary`
  - `pacman_win_rate`
  - `enemy_win_rate`
  - `samples`
  - optional confidence or warning when sample size is small

### Storage notes

- start with a simple local file or SQLite-backed store
- writes happen after each completed match
- reads must be fast enough to refresh advanced-mode UI immediately after a config change

## 10. UI Design

The UI should stay thin. It renders state and captures input, but it does not implement game rules.

### Main screens

- `MainMenu`
  - start game
  - advanced mode
  - quit

- `ModeConfigPanel`
  - choose controller for Pacman and Slime
  - choose AI algorithm for each AI-controlled side
  - show algorithm parameter controls

- `AdvancedPanel`
  - shows parameter editor
  - reads historical win-rate statistics for the current configuration
  - displays summary stats and sample counts

- `GameView`
  - draws board and entities
  - receives keyboard input
  - maps arrow keys to Pacman movement
  - supports `q` / `esc` to return to menu

## 11. Configuration Model

Advanced mode should be schema-driven so the UI can build parameter forms dynamically.

```python
class AgentConfig(BaseModel):
    controller_type: str
    algorithm: str
    params: dict[str, Any]


class MatchConfig(BaseModel):
    pacman_config: AgentConfig
    slime_config: AgentConfig
    helper_config: AgentConfig
    tick_ms: int = 120
    board_preset: str = "default"
```

### Benefits

- one shared config format for UI, runtime, and stored match history queries
- easy preset serialization
- algorithm-specific forms can be generated from metadata

## 12. Persistence and Concurrency Model

### Real-time match

- UI thread owns Qt event loop
- `QTimer` triggers game ticks
- each tick reads current inputs and advances one frame

### Match history writes

- result persistence can happen synchronously if cheap, or on a background worker if storage latency becomes visible
- writes must not block rendering long enough to affect match flow
- persisted data should include enough metadata to support future analysis and filtering

### Future RL training

- use a dedicated process if training becomes heavy
- keep training outside the play session lifecycle

## 13. Testing Strategy

The core logic must be tested independently from the GUI.

### Priority test areas

#### Rules

- illegal movement becomes `STAY`
- dot consumption decrements `dots_remaining`
- simultaneous final-dot and capture resolves to Pacman win

#### Pathfinding

- BFS returns the shortest valid route
- BFS handles blocked targets cleanly

#### Agents

- `RandomAgent` only returns legal actions
- `ShortestPathAgent` reduces distance when path exists
- `CopycatAgent` switches from seek mode to replay mode correctly

#### Statistics

- completed matches are persisted exactly once
- win-rate summaries use historical data filters correctly
- low-sample summaries are labeled clearly

## 14. Suggested Implementation Plan

### Milestone 1

- implement `Board`, `GameState`, `RuleEngine`, `GameEngine`
- implement `HumanAgent`, `RandomAgent`, `ShortestPathAgent`
- build basic menu and game view
- persist completed match results

### Milestone 2

- implement `CopycatAgent`
- add advanced mode configuration UI
- add history-backed win-rate display

### Milestone 3

- add `RLAgent` integration
- add preset save/load
- add richer statistics filters and summaries
- refine balancing and parameter tuning

## 15. Design Constraints and Principles

- Keep `GameState` independent from UI frameworks.
- Keep rules deterministic where possible.
- Reuse the same core match/result model across gameplay, persistence, and statistics.
- Persist match data in a format that can survive future schema extension.
- Prefer pure functions or stateless services in the rules layer.
- Do not let agents mutate state directly.
- Keep RL support behind a stable interface so it can remain optional early on.

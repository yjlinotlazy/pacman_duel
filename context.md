# pacman_duel Context

## Purpose

`pacman_duel` is a local-first Pacman-style duel game intended to help players understand reinforcement learning by comparing human play and different AI strategies.

## Current Runtime Shape

- Local GUI exists and is runnable through `python src/app.py` or `python -m src.app`
- The top control panel remains visible during gameplay
- A match can be started, replayed with the same config, stopped, or replaced with a new config without leaving the screen
- `q` / `Esc` stop the current match
- `r` replays the current match config

## Core Modules

### Core

- `src/core/domain.py`
  - shared immutable runtime state
  - `GameState` includes:
    - board and entity positions
    - `tick`
    - `speed_scaling_factor`
    - `pacman_start`
    - `pacman_history`
- `src/core/board.py`
  - parses ASCII board layouts
- `src/core/rules.py`
  - legal actions
  - action sanitization
  - speed scaling for slime/helper
  - dot consumption
  - win/loss resolution
- `src/core/engine.py`
  - advances one match tick at a time

### Algorithms

- `src/algorithms/pathfinding.py`
  - BFS first-step shortest path
- `src/algorithms/random_walk.py`
  - corridor-aware random movement
  - avoids immediate backtracking when alternatives exist
  - keeps moving straight until a corner/intersection or forced reversal

### Agents

Agents are split by side.

- `src/agents/pacman/`
  - `human.py`
  - `random.py`
- `src/agents/slime/`
  - `random.py`
  - `shortest_path.py`
  - `copycat.py`

Important:

- Pacman agents and slime agents are intentionally separate because their goals differ
- Helper is treated as part of the slime-side family
- Detailed agent behavior docs live in `agents.md` and `agents_cn.md`

### App / Session

- `src/game_session.py`
  - runs one match using already-constructed agents and engine
- `src/app_controller.py`
  - builds sessions from `MatchConfig`
  - validates Pacman-side vs slime-side agent choices

### Stats

- `src/stats/history_store.py`
  - JSONL-backed match history store
- `src/stats/winrate.py`
  - query/filter/summarize historical results

### UI

- `src/ui/config_panel.py`
  - board selector
  - Pacman/slime/helper selectors
  - enemy speed scaling selector
- `src/ui/game_view.py`
  - board rendering
  - human keyboard input
  - timer-driven or adaptive stepping
- `src/ui/main_window.py`
  - persistent controls above board

## Boards

- Board layouts live in `src/boards/`
- Built-in boards currently include:
  - `default_board.py`
  - `classic_inspired_board.py`

Notes:

- Board parser supports `#`, `.`, space, `P`, `S`, `H`
- Default board has been checked for full reachability from Pacman spawn

## Movement / Gameplay Rules

- Pacman wins by clearing all dots
- Enemy wins if slime or helper catches Pacman
- If final dot and capture happen on the same tick, Pacman wins
- Invalid movement becomes `STAY`
- Slime and helper speed are scaled by `GameState.speed_scaling_factor`
- `speed_scaling_factor` may be:
  - integer like `1`, `2`, `3`
  - `"adaptive"` in the UI
- In adaptive mode:
  - UI does not run the timer
  - one tick happens when the player presses a direction key

## Enemy Pacing Rules

- Slime and helper both obey speed scaling
- Helper copycat has extra pacing:
  - active for 20 ticks
  - then forced to `STAY` for 5 ticks

## UI Configuration Options

Current top-panel options:

- Board
- Pacman controller
- Slime AI
- Helper AI
- Enemy speed scaling

Current buttons:

- Start Match
- Replay Current Config
- Stop Match
- Quit App

## Tests

- Tests are under `tests/`
- UI tests use `QT_QPA_PLATFORM=offscreen`
- Recent suite status was passing with 44 tests

## Important Docs

- `README.md`
- `design.md`
- `design_cn.md`
- `agents.md`
- `agents_cn.md`
- `model_design.md`
- `model_design_cn.md`
- `execution_plan.md`
- `instructions.md`
- `instructions_cn.md`

## Known Gaps

- No stats panel in the UI yet
- Match results are not yet automatically persisted from the gameplay loop
- RL runtime agents are not implemented yet
- Training package is not implemented yet

## Practical Guidance For Future Edits

- Prefer keeping game rules in `src/core/` and not in UI code
- Put reusable algorithms in `src/algorithms/`
- Keep Pacman-side and slime-side agent families separate
- Use `apply_patch` for manual file edits
- When changing UI behavior, preserve the persistent top control panel pattern

# pacman_duel Execution Plan

## Goal

Deliver a playable local version of `pacman_duel` with a clean separation between core rules, agents, UI, statistics, and reinforcement learning support, while keeping the RL training workflow isolated from gameplay.

## Guiding Constraints

- Keep `core/` independent from UI and ML frameworks.
- Keep gameplay inference separate from RL training.
- Prefer deterministic logic and testability before UI polish.
- Treat the local GUI as the first production path.
- Delay web and remote-serving concerns until the local architecture is stable.

## Milestone 1: Core Engine

### Objectives

- Define the core domain model.
- Implement deterministic game-state transitions.
- Lock down rule behavior with tests.

### Tasks

- [ ] Define `Position`, `EntityState`, `Board`, `GameState`, and required enums.
- [ ] Define legal movement and bounds-checking behavior.
- [ ] Implement tick processing order in the engine.
- [ ] Implement dot consumption rules.
- [ ] Implement capture rules.
- [ ] Implement win/loss resolution rules.
- [ ] Preserve the rule that Pacman wins if the last dot is eaten on the same tick as capture.
- [ ] Add unit tests for normal and edge-case rule behavior.

### Exit Criteria

- Core rule tests pass.
- Engine behavior is deterministic for fixed inputs.
- No UI code is required to test the engine.

## Milestone 2: Baseline Agents

### Objectives

- Establish one stable `Agent` interface.
- Implement baseline strategies needed for gameplay and evaluation.

### Tasks

- [ ] Define the `Agent` protocol.
- [ ] Implement `HumanAgent`.
- [ ] Implement `RandomAgent`.
- [ ] Implement `ShortestPathAgent` using BFS.
- [ ] Implement `CopycatAgent` with two-phase replay behavior.
- [ ] Ensure all agents return actions without mutating game state.
- [ ] Add tests for baseline agent behavior.

### Exit Criteria

- All built-in agents run through the same interface.
- Baseline agents can be attached to a match session interchangeably.
- Agent behavior is covered by targeted tests.

## Milestone 3: Match Orchestration

### Objectives

- Create the application-side match lifecycle.
- Keep session control independent from any specific UI.

### Tasks

- [ ] Implement `GameSession` to own one match configuration, engine instance, and agent set.
- [ ] Implement `AppController` to create, reset, destroy, and switch sessions.
- [ ] Add configuration translation from UI-friendly options to runtime config.
- [ ] Expose a clean step/tick interface for the presentation layer.
- [ ] Add tests for session startup, stepping, reset, and teardown.

### Exit Criteria

- A match can be created and advanced without GUI dependencies.
- Session lifecycle behavior is stable and testable.
- The orchestration layer is reusable by future local or web frontends.

## Milestone 4: Persistence and Statistics

### Objectives

- Persist completed match results.
- Generate history-backed summaries and win-rate views.

### Tasks

- [ ] Implement a history storage format.
- [ ] Persist match outcome, agent choices, and relevant config metadata.
- [ ] Implement summary generation utilities.
- [ ] Implement win-rate aggregation from stored results.
- [ ] Add tests for storage and aggregation behavior.

### Exit Criteria

- Match results survive app restarts.
- Win-rate summaries are generated from real stored history.
- Statistics logic does not depend on UI rendering.

## Milestone 5: Local GUI

### Objectives

- Deliver a playable local desktop version using `PySide6`.
- Keep UI limited to control flow and rendering.

### Tasks

- [ ] Implement `MainWindow`.
- [ ] Implement menu and configuration screens.
- [ ] Implement the game view.
- [ ] Implement a stats panel for history-backed summaries.
- [ ] Wire keyboard input for human-controlled matches.
- [ ] Support leaving a match and returning to the menu without affecting core rules.
- [ ] Verify the local GUI works under Wayland.

### Exit Criteria

- A full local match can be started, played, and exited from the GUI.
- Configuration and stats panels work against the orchestration and stats layers.
- UI code does not contain core game-rule logic.

## Milestone 6: RL Integration Boundary

### Objectives

- Define the ML-facing interfaces before full training support exists.
- Prevent RL code from leaking into gameplay orchestration.

### Tasks

- [ ] Add `agents/rl_agent.py` as an inference-only agent.
- [ ] Define observation encoding conventions.
- [ ] Define action-index to `Direction` mapping.
- [ ] Define checkpoint metadata requirements.
- [ ] Define model-loading behavior and failure handling.
- [ ] Add tests for observation/action contract stability.

### Exit Criteria

- `RLAgent` has a stable runtime contract.
- Inference assumptions are documented and testable.
- No training loop is embedded in the gameplay process.

## Milestone 7: Training Package

### Objectives

- Build RL training as a standalone workflow.
- Reuse `core/` without introducing UI dependencies.

### Tasks

- [ ] Implement `training/env.py` as a `gymnasium`-style wrapper.
- [ ] Implement `training/observation.py`.
- [ ] Implement `training/reward.py`.
- [ ] Implement `training/train_rl.py`.
- [ ] Ensure training can run in a separate process from the app.
- [ ] Add tests for `reset()`, `step()`, reward behavior, and episode termination.

### Exit Criteria

- Training can be started independently from the GUI.
- The environment contract is stable and tested.
- The training package depends on `core/`, not on `ui/`.

## Milestone 8: Checkpointing and Offline Evaluation

### Objectives

- Make trained models reproducible and selectable.
- Validate trained policies before live gameplay use.

### Tasks

- [ ] Implement checkpoint save/load conventions.
- [ ] Implement metadata versioning for checkpoints.
- [ ] Implement retention rules for multiple checkpoints.
- [ ] Implement `training/evaluate_rl.py`.
- [ ] Compare trained policies against baseline agents.
- [ ] Record evaluation summaries that can inform model selection.

### Exit Criteria

- Training produces reusable checkpoints.
- Evaluation can be run offline against baseline agents.
- Model metadata is sufficient to detect incompatible versions.

## Milestone 9: In-Game ML Inference

### Objectives

- Use trained models in live matches.
- Keep inference local and lightweight.

### Tasks

- [ ] Load checkpoints at session start.
- [ ] Keep the model in memory during gameplay.
- [ ] Convert `GameState` to observations on each tick.
- [ ] Run one forward pass per decision.
- [ ] Map predicted actions to legal game moves.
- [ ] Add fallback behavior for invalid outputs or load failures.

### Exit Criteria

- An RL-backed agent can participate in a live match.
- The model is used only for inference during gameplay.
- Gameplay remains responsive while the model is active.

## Milestone 10: Operational Hardening

### Objectives

- Make the system resilient to model and integration failures.
- Prepare for later expansion without redesigning the runtime boundary.

### Tasks

- [ ] Handle missing checkpoint files cleanly.
- [ ] Handle incompatible checkpoint metadata versions.
- [ ] Handle observation-schema drift safely.
- [ ] Add logging for model load and inference failures.
- [ ] Add safe fallbacks when RL inference is unavailable.
- [ ] Document operational expectations for local model storage.

### Exit Criteria

- The app remains playable when RL assets are missing or invalid.
- Failure modes are visible and diagnosable.
- RL integration does not compromise core gameplay stability.

## Optional Milestone 11: App-Managed Training

### Objectives

- Allow the app to trigger training without embedding training in the main process.

### Tasks

- [ ] Launch training through a subprocess.
- [ ] Report progress through logs, polling, or lightweight IPC.
- [ ] Surface checkpoint status in the app.
- [ ] Prevent the UI from directly executing training steps.

### Exit Criteria

- Training can be initiated from the app without blocking gameplay.
- The training runtime remains isolated from the GUI process.

## Optional Milestone 12: Web and TypeScript Frontend Expansion

### Objectives

- Reuse the existing core and orchestration boundaries for web delivery.

### Tasks

- [ ] Define the minimal backend/session API needed by a web client.
- [ ] Decide whether to use a Python-served web UI or a dedicated TypeScript frontend.
- [ ] Reuse existing session orchestration instead of reimplementing core rules.
- [ ] Keep ML inference boundaries unchanged.

### Exit Criteria

- Web delivery reuses the same core gameplay model.
- Frontend expansion does not require redesigning the engine.

## Cross-Cutting Work

### Documentation

- [ ] Keep `design.md`, `design_cn.md`, `model_design.md`, and `model_design_cn.md` aligned with implementation.
- [ ] Document module boundaries as they become concrete.

### Testing

- [ ] Maintain fast unit tests for `core/`.
- [ ] Add integration tests for sessions and persistence.
- [ ] Add targeted tests for RL observation and action contracts.

### Code Quality

- [ ] Keep boundaries explicit between `core/`, `agents/`, `training/`, `stats/`, and `ui/`.
- [ ] Avoid leaking UI concerns into rules or ML code.
- [ ] Avoid leaking training concerns into gameplay runtime.

## Recommended Build Order

1. Milestone 1: Core Engine
2. Milestone 2: Baseline Agents
3. Milestone 3: Match Orchestration
4. Milestone 4: Persistence and Statistics
5. Milestone 5: Local GUI
6. Milestone 6: RL Integration Boundary
7. Milestone 7: Training Package
8. Milestone 8: Checkpointing and Offline Evaluation
9. Milestone 9: In-Game ML Inference
10. Milestone 10: Operational Hardening
11. Optional Milestone 11: App-Managed Training
12. Optional Milestone 12: Web and TypeScript Frontend Expansion

## Definition of Success

The project is in a strong first-release state when:

- local desktop gameplay works end to end
- rules, agents, and stats are testable without the GUI
- trained models can be loaded for inference during matches
- RL training runs outside the gameplay process
- future web delivery can build on the same architecture without reworking the core engine

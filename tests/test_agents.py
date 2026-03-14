from __future__ import annotations

from dataclasses import replace

from src.agents.copycat import CopycatAgent
from src.agents.human import HumanAgent
from src.agents.random_agent import RandomAgent
from src.agents.shortest_path import ShortestPathAgent
from src.core.engine import GameEngine
from src.core.domain import Direction, Position, Role
from tests.conftest import build_state


def test_random_agent_returns_legal_action() -> None:
    state = build_state(
        (
            "#####",
            "#P  #",
            "# .H#",
            "# S #",
            "#####",
        )
    )

    agent = RandomAgent(Role.PACMAN, seed=7)
    action = agent.next_action(state, {})

    assert action in {
        Direction.STAY,
        Direction.RIGHT,
        Direction.DOWN,
    }


def test_human_agent_defaults_to_stay_without_input() -> None:
    state = build_state(
        (
            "#####",
            "#P  #",
            "# .H#",
            "# S #",
            "#####",
        )
    )

    agent = HumanAgent(Role.PACMAN)

    assert agent.next_action(state, {}) == Direction.STAY


def test_human_agent_returns_latest_buffered_input() -> None:
    state = build_state(
        (
            "#####",
            "#P  #",
            "# .H#",
            "# S #",
            "#####",
        )
    )

    agent = HumanAgent(Role.PACMAN)
    agent.set_pending_action(Direction.RIGHT)
    agent.set_pending_action(Direction.DOWN)

    assert agent.next_action(state, {}) == Direction.DOWN


def test_human_agent_reset_clears_pending_input() -> None:
    state = build_state(
        (
            "#####",
            "#P  #",
            "# .H#",
            "# S #",
            "#####",
        )
    )

    agent = HumanAgent(Role.PACMAN)
    agent.set_pending_action(Direction.RIGHT)
    agent.reset()

    assert agent.next_action(state, {}) == Direction.STAY


def test_copycat_agent_seeks_pacman_start_before_replay() -> None:
    state = build_state(
        (
            "#######",
            "#P   S#",
            "#  . H#",
            "#######",
        )
    )

    agent = CopycatAgent(Role.SLIME)

    assert agent.next_action(state, {}) == Direction.LEFT


def test_copycat_agent_replays_history_after_reaching_pacman_start() -> None:
    state = build_state(
        (
            "#####",
            "#P  #",
            "# .H#",
            "# S #",
            "#####",
        )
    )
    replay_state = replace(
        state,
        slime=state.slime.__class__(role=Role.SLIME, position=state.pacman_start),
        pacman_history=(Direction.RIGHT, Direction.STAY, Direction.DOWN),
    )
    agent = CopycatAgent(Role.SLIME)

    assert agent.next_action(replay_state, {}) == Direction.RIGHT
    assert agent.next_action(replay_state, {}) == Direction.STAY
    assert agent.next_action(replay_state, {}) == Direction.DOWN
    assert agent.next_action(replay_state, {}) == Direction.STAY


def test_copycat_agent_reset_restarts_replay_sequence() -> None:
    state = build_state(
        (
            "#####",
            "#P  #",
            "# .H#",
            "# S #",
            "#####",
        )
    )
    replay_state = replace(
        state,
        slime=state.slime.__class__(role=Role.SLIME, position=state.pacman_start),
        pacman_history=(Direction.RIGHT, Direction.DOWN),
    )
    agent = CopycatAgent(Role.SLIME)

    assert agent.next_action(replay_state, {}) == Direction.RIGHT
    agent.reset()

    assert agent.next_action(replay_state, {}) == Direction.RIGHT


def test_shortest_path_agent_moves_toward_target() -> None:
    state = build_state(
        (
            "#######",
            "#S   P#",
            "# ### #",
            "#H    #",
            "#######",
        )
    )

    agent = ShortestPathAgent(Role.SLIME, target_role=Role.PACMAN)

    assert agent.next_action(state, {}) == Direction.RIGHT


def test_shortest_path_agent_stays_when_already_at_target() -> None:
    state = build_state(
        (
            "#####",
            "#PS #",
            "# .H#",
            "#####",
        )
    )

    agent = ShortestPathAgent(Role.SLIME, target_role=Role.SLIME)

    assert agent.next_action(state, {}) == Direction.STAY


def test_engine_advances_tick() -> None:
    state = build_state(
        (
            "######",
            "#P. S#",
            "#   H#",
            "######",
        )
    )

    engine = GameEngine(state)
    next_state = engine.step(
        {
            Role.PACMAN: Direction.RIGHT,
            Role.SLIME: Direction.LEFT,
            Role.HELPER: Direction.STAY,
        }
    )

    assert next_state.tick == 1
    assert next_state.pacman.position == Position(2, 1)

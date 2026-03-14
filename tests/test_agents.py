from __future__ import annotations

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

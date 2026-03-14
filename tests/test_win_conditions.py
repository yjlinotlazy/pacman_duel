from __future__ import annotations

from src.core.engine import GameEngine
from src.core.domain import Direction, MatchStatus, Role
from tests.conftest import build_state


def test_pacman_wins_after_consuming_final_dot() -> None:
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
            Role.SLIME: Direction.STAY,
            Role.HELPER: Direction.STAY,
        }
    )

    assert next_state.status == MatchStatus.PACMAN_WIN


def test_match_does_not_advance_after_terminal_state() -> None:
    state = build_state(
        (
            "######",
            "#PS H#",
            "# ...#",
            "######",
        )
    )

    engine = GameEngine(state)
    first = engine.step(
        {
            Role.PACMAN: Direction.STAY,
            Role.SLIME: Direction.LEFT,
            Role.HELPER: Direction.STAY,
        }
    )
    second = engine.step(
        {
            Role.PACMAN: Direction.RIGHT,
            Role.SLIME: Direction.LEFT,
            Role.HELPER: Direction.LEFT,
        }
    )

    assert first.status == MatchStatus.ENEMY_WIN
    assert second == first

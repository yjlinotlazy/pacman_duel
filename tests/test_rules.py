from __future__ import annotations

from src.core.engine import GameEngine
from src.core.domain import Direction, MatchStatus, Position, Role
from src.core.rules import legal_actions, sanitize_action
from tests.conftest import build_state


def test_invalid_movement_becomes_stay() -> None:
    state = build_state(
        (
            "#####",
            "#P S#",
            "# .H#",
            "#####",
        )
    )

    engine = GameEngine(state)
    next_state = engine.step(
        {
            Role.PACMAN: Direction.UP,
            Role.SLIME: Direction.STAY,
            Role.HELPER: Direction.STAY,
        }
    )

    assert next_state.pacman.position == Position(1, 1)
    assert next_state.pacman_history == (Direction.STAY,)


def test_legal_actions_include_stay_and_walkable_moves() -> None:
    state = build_state(
        (
            "#####",
            "#P  #",
            "# .H#",
            "# S #",
            "#####",
        )
    )

    actions = legal_actions(state, Role.PACMAN)

    assert Direction.STAY in actions
    assert Direction.RIGHT in actions
    assert Direction.DOWN in actions
    assert Direction.UP not in actions


def test_dot_consumption_removes_dot() -> None:
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

    assert Position(2, 1) not in next_state.dots


def test_capture_results_in_enemy_win() -> None:
    state = build_state(
        (
            "######",
            "#PS H#",
            "# ...#",
            "######",
        )
    )

    engine = GameEngine(state)
    next_state = engine.step(
        {
            Role.PACMAN: Direction.STAY,
            Role.SLIME: Direction.LEFT,
            Role.HELPER: Direction.STAY,
        }
    )

    assert next_state.status == MatchStatus.ENEMY_WIN


def test_last_dot_same_tick_as_capture_is_pacman_win() -> None:
    state = build_state(
        (
            "#######",
            "#P    #",
            "#.S  H#",
            "#######",
        )
    )

    engine = GameEngine(state)
    next_state = engine.step(
        {
            Role.PACMAN: Direction.DOWN,
            Role.SLIME: Direction.LEFT,
            Role.HELPER: Direction.STAY,
        }
    )

    assert next_state.pacman.position == Position(1, 2)
    assert next_state.slime.position == Position(1, 2)
    assert next_state.status == MatchStatus.PACMAN_WIN


def test_sanitize_action_maps_illegal_move_to_stay() -> None:
    state = build_state(
        (
            "#####",
            "#P S#",
            "# .H#",
            "#####",
        )
    )

    assert sanitize_action(state, Role.PACMAN, Direction.UP) == Direction.STAY

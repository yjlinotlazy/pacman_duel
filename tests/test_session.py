from __future__ import annotations

from src.agents.pacman.random import RandomAgent as PacmanRandomAgent
from src.agents.slime.shortest_path import ShortestPathAgent
from src.core.engine import GameEngine
from src.core.domain import MatchStatus, Role
from src.game_session import GameSession
from tests.conftest import build_state


def test_session_collects_actions_for_all_roles() -> None:
    state = build_state(
        (
            "#######",
            "#P   S#",
            "#  . H#",
            "#######",
        )
    )
    session = GameSession(
        engine=GameEngine(state),
        agents={
            Role.PACMAN: PacmanRandomAgent(seed=1),
            Role.SLIME: ShortestPathAgent(Role.SLIME),
            Role.HELPER: ShortestPathAgent(Role.HELPER),
        },
    )

    actions = session.collect_actions()

    assert set(actions) == {Role.PACMAN, Role.SLIME, Role.HELPER}


def test_session_can_run_headless_match_to_completion() -> None:
    state = build_state(
        (
            "########",
            "#P....S#",
            "#   H  #",
            "########",
        )
    )
    session = GameSession(
        engine=GameEngine(state),
        agents={
            Role.PACMAN: PacmanRandomAgent(seed=3),
            Role.SLIME: ShortestPathAgent(Role.SLIME),
            Role.HELPER: ShortestPathAgent(Role.HELPER),
        },
    )

    final_state = session.run_until_finished(max_ticks=50)

    assert final_state.status in {MatchStatus.PACMAN_WIN, MatchStatus.ENEMY_WIN}
    assert final_state.tick <= 50

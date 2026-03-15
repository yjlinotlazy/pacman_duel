from __future__ import annotations

import pytest

from src.agents.pacman.human import HumanAgent
from src.agents.pacman.random import RandomAgent as PacmanRandomAgent
from src.agents.slime.copycat import CopycatAgent
from src.agents.slime.shortest_path import ShortestPathAgent
from src.app_controller import AgentConfig, AppController, MatchConfig
from src.core.domain import Direction, Role


def make_match_config(
    pacman_config: AgentConfig | None = None,
    slime_config: AgentConfig | None = None,
    helper_config: AgentConfig | None = None,
) -> MatchConfig:
    return MatchConfig(
        board_layout=(
            "#######",
            "#P...S#",
            "#  . H#",
            "#######",
        ),
        pacman_config=pacman_config or AgentConfig("human"),
        slime_config=slime_config or AgentConfig("ai", "shortest_path"),
        helper_config=helper_config or AgentConfig("ai", "copycat"),
    )


def test_create_session_builds_current_session_from_config() -> None:
    controller = AppController()

    session = controller.create_session(make_match_config())

    assert controller.current_session is session
    assert isinstance(session.agents[Role.PACMAN], HumanAgent)
    assert isinstance(session.agents[Role.SLIME], ShortestPathAgent)
    assert isinstance(session.agents[Role.HELPER], CopycatAgent)


def test_reset_session_restores_initial_state() -> None:
    controller = AppController()
    session = controller.create_session(
        make_match_config(
            pacman_config=AgentConfig("human"),
            slime_config=AgentConfig("ai", "random", {"seed": 7}),
            helper_config=AgentConfig("ai", "random", {"seed": 11}),
        )
    )
    pacman_agent = session.agents[Role.PACMAN]
    assert isinstance(pacman_agent, HumanAgent)

    pacman_agent.set_pending_action(Direction.RIGHT)
    session.step()
    assert session.state.tick == 1

    reset_session = controller.reset_session()

    assert reset_session is session
    assert reset_session.state.tick == 0
    assert reset_session.state.pacman.position == reset_session.state.pacman_start
    assert pacman_agent.next_action(reset_session.state, {}) == Direction.STAY


def test_destroy_session_clears_current_session() -> None:
    controller = AppController()
    controller.create_session(make_match_config())

    controller.destroy_session()

    assert controller.current_session is None


def test_switch_session_replaces_current_session() -> None:
    controller = AppController()
    first = controller.create_session(make_match_config())

    second = controller.switch_session(
        make_match_config(
            pacman_config=AgentConfig("ai", "random", {"seed": 3}),
            slime_config=AgentConfig("ai", "copycat"),
            helper_config=AgentConfig("ai", "shortest_path"),
        )
    )

    assert second is controller.current_session
    assert second is not first
    assert isinstance(second.agents[Role.PACMAN], PacmanRandomAgent)
    assert isinstance(second.agents[Role.SLIME], CopycatAgent)
    assert isinstance(second.agents[Role.HELPER], ShortestPathAgent)


def test_create_session_rejects_unknown_algorithm() -> None:
    controller = AppController()

    with pytest.raises(ValueError, match="Unsupported slime algorithm"):
        controller.create_session(
            make_match_config(
                slime_config=AgentConfig("ai", "teleport"),
            )
        )


def test_reset_session_requires_active_session() -> None:
    controller = AppController()

    with pytest.raises(RuntimeError, match="No active session"):
        controller.reset_session()

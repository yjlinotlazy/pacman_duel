from __future__ import annotations

from dataclasses import replace

from src.agents.pacman.human import HumanAgent
from src.agents.pacman.random import RandomAgent as PacmanRandomAgent
from src.agents.slime.copycat import CopycatAgent
from src.agents.slime.random import RandomAgent as SlimeRandomAgent
from src.agents.slime.shortest_path import ShortestPathAgent
from src.core.engine import GameEngine
from src.core.domain import Direction, EntityState, Position, Role
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

    agent = PacmanRandomAgent(seed=7)
    action = agent.next_action(state, {})

    assert action in {
        Direction.STAY,
        Direction.RIGHT,
        Direction.DOWN,
    }


def test_random_agent_keeps_going_straight_in_corridor() -> None:
    state = build_state(
        (
            "#######",
            "#P   S#",
            "### #H#",
            "#######",
        )
    )
    state = replace(
        state,
        pacman=EntityState(role=Role.PACMAN, position=Position(2, 1)),
    )

    agent = PacmanRandomAgent(seed=1)
    agent._current_direction = Direction.RIGHT
    first = agent.next_action(state, {})

    assert first == Direction.RIGHT


def test_random_agent_does_not_immediately_reverse_at_intersection() -> None:
    state = build_state(
        (
            "#######",
            "#  .  #",
            "#  P S#",
            "#  H  #",
            "#######",
        )
    )

    agent = PacmanRandomAgent(seed=2)
    agent._current_direction = Direction.RIGHT

    assert agent.next_action(state, {}) in {Direction.UP, Direction.RIGHT, Direction.DOWN}
    assert agent.next_action(state, {}) != Direction.LEFT


def test_random_agent_can_reverse_at_dead_end_when_no_other_move_exists() -> None:
    state = build_state(
        (
            "#####",
            "#SPH#",
            "#####",
        )
    )

    agent = SlimeRandomAgent(Role.SLIME, seed=3)
    agent._current_direction = Direction.LEFT

    assert agent.next_action(state, {}) == Direction.RIGHT


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

    agent = HumanAgent()

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

    agent = HumanAgent()
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

    agent = HumanAgent()
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


def test_copycat_helper_pauses_for_five_ticks_after_every_twenty_ticks() -> None:
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
        helper=EntityState(role=Role.HELPER, position=state.pacman_start),
        pacman_history=(Direction.RIGHT,) * 30,
        tick=20,
    )
    agent = CopycatAgent(Role.HELPER)

    assert agent.next_action(replay_state, {}) == Direction.STAY
    assert agent.next_action(replace(replay_state, tick=24), {}) == Direction.STAY
    assert agent.next_action(replace(replay_state, tick=25), {}) == Direction.RIGHT


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

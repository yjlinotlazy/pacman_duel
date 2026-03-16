from __future__ import annotations

from src.agents.rl.encoding import OBSERVATION_VERSION
from src.core.domain import MatchStatus, Role
from src.training.env import TrainingEnv
from src.training.reward import compute_reward


def test_training_env_reset_returns_shared_observation() -> None:
    env = TrainingEnv(
        board_layout=(
            "#######",
            "#P  .S#",
            "#    H#",
            "#######",
        )
    )

    observation = env.reset()

    assert observation.version == OBSERVATION_VERSION
    assert observation.role == "pacman"
    assert observation.board_size == (7, 4)


def test_training_env_step_advances_tick_and_returns_reward() -> None:
    env = TrainingEnv(
        board_layout=(
            "#######",
            "#P  .S#",
            "#    H#",
            "#######",
        )
    )
    env.reset()

    result = env.step(3)

    assert result.info["tick"] == 1
    assert isinstance(result.reward, float)
    assert result.terminated is False


def test_compute_reward_rewards_pacman_for_winning_transition() -> None:
    env = TrainingEnv(
        board_layout=(
            "#####",
            "#PS #",
            "# .H#",
            "#####",
        )
    )
    initial = env.reset()
    del initial
    previous_state = env.state
    env._engine._state = env.state.__class__(
        board=env.state.board,
        pacman=env.state.pacman,
        slime=env.state.slime,
        helper=env.state.helper,
        dots=frozenset(),
        status=MatchStatus.PACMAN_WIN,
        tick=1,
        speed_scaling_factor=env.state.speed_scaling_factor,
        pacman_start=env.state.pacman_start,
        pacman_history=env.state.pacman_history,
    )

    reward = compute_reward(previous_state, env.state, Role.PACMAN)

    assert reward > 0.0

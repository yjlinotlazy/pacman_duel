"""Minimal entrypoint placeholder for standalone RL training workflows."""

from __future__ import annotations

from src.core.domain import Role
from src.training.env import TrainingEnv


def run_training_episode(board_layout: tuple[str, ...], controlled_role: Role = Role.PACMAN) -> float:
    """Run one placeholder episode with repeated STAY actions and return total reward."""
    env = TrainingEnv(board_layout=board_layout, controlled_role=controlled_role)
    env.reset()
    total_reward = 0.0
    while True:
        step_result = env.step(4)
        total_reward += step_result.reward
        if step_result.terminated:
            return total_reward

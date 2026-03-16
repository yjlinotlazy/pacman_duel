"""Minimal entrypoint placeholder for standalone RL training workflows."""

from __future__ import annotations

from src.core.domain import Role
from src.training.checkpoints import save_versioned_checkpoint
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


def export_static_policy_checkpoint(
    output_dir: str,
    *,
    role_family: str,
    action_scores: list[float],
    label: str = "policy",
    retention_limit: int | None = None,
) -> str:
    """Write one runtime-compatible static-score checkpoint for later evaluation."""
    checkpoint_path = save_versioned_checkpoint(
        output_dir,
        role_family=role_family,
        runner_type="static_scores",
        policy={"action_scores": action_scores},
        label=label,
        retention_limit=retention_limit,
    )
    return str(checkpoint_path)

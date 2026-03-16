"""Reward helpers for standalone RL training."""

from __future__ import annotations

from src.core.domain import GameState, MatchStatus, Role


def compute_reward(previous_state: GameState, next_state: GameState, role: Role) -> float:
    """Compute a simple dense reward from one transition."""
    reward = -0.01
    dots_cleared = len(previous_state.dots) - len(next_state.dots)
    reward += float(dots_cleared) * 0.5

    if next_state.status == MatchStatus.PACMAN_WIN:
        return reward + (1.0 if role == Role.PACMAN else -1.0)
    if next_state.status == MatchStatus.ENEMY_WIN:
        return reward + (-1.0 if role == Role.PACMAN else 1.0)
    return reward


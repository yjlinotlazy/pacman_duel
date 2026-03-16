"""Inference-only slime-side RL agent."""

from __future__ import annotations

from pathlib import Path

from src.agents.rl.action_mapping import best_direction_for_scores
from src.agents.rl.checkpoints import RLCheckpoint, load_rl_checkpoint
from src.agents.rl.encoding import encode_observation
from src.core.domain import Direction, GameState, Role


class RLAgent:
    """Choose slime-side actions from a validated RL checkpoint."""

    def __init__(self, role: Role, checkpoint_path: str | Path) -> None:
        """Load one slime-side checkpoint for inference."""
        if role not in {Role.SLIME, Role.HELPER}:
            raise ValueError(f"Unsupported slime-side RL role: {role}")
        self.role = role
        self._checkpoint = load_rl_checkpoint(checkpoint_path, expected_role_family="slime")

    def next_action(self, state: GameState, config: dict | None = None) -> Direction:
        """Run one inference step and map the result to a runtime direction."""
        del config
        observation = encode_observation(state, self.role)
        return best_direction_for_scores(self._checkpoint.runner.action_scores(observation))

    def reset(self) -> None:
        """Reset hook for protocol compatibility; current inference is stateless."""
        return None

    @property
    def checkpoint(self) -> RLCheckpoint:
        """Expose loaded checkpoint metadata for testing and diagnostics."""
        return self._checkpoint

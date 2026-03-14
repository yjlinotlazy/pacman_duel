"""Random-move baseline agent."""

from __future__ import annotations

import random

from src.core.domain import Direction, GameState, Role
from src.core.rules import legal_actions


class RandomAgent:
    """Choose uniformly from the currently legal moves for one role."""

    def __init__(self, role: Role, seed: int | None = None) -> None:
        """Bind the agent to a role and optional deterministic RNG seed."""
        self.role = role
        self._rng = random.Random(seed)

    def next_action(self, state: GameState, config: dict | None = None) -> Direction:
        """Return one random legal move for the configured role."""
        return self._rng.choice(legal_actions(state, self.role))

    def reset(self) -> None:
        """Reset hook for protocol compatibility; no state is currently stored."""
        return None

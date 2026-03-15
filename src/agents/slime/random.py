"""Random slime-side baseline agent."""

from __future__ import annotations

import random

from src.algorithms.random_walk import choose_corridor_random_direction
from src.core.domain import Direction, GameState, Role


class RandomAgent:
    """Choose uniformly from the currently legal moves for one slime-side role."""

    def __init__(self, role: Role, seed: int | None = None) -> None:
        """Bind the agent to a slime-side role and optional deterministic seed."""
        self.role = role
        self._rng = random.Random(seed)
        self._current_direction: Direction | None = None

    def next_action(self, state: GameState, config: dict | None = None) -> Direction:
        """Return one corridor-aware random move for the configured slime-side role."""
        del config
        self._current_direction = choose_corridor_random_direction(
            state=state,
            role=self.role,
            rng=self._rng,
            current_direction=self._current_direction,
        )
        return self._current_direction

    def reset(self) -> None:
        """Clear the remembered movement direction before a new match."""
        self._current_direction = None

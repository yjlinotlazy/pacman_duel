"""Random Pacman baseline agent."""

from __future__ import annotations

import random

from src.algorithms.random_walk import choose_corridor_random_direction
from src.core.domain import Direction, GameState, Role


class RandomAgent:
    """Choose uniformly from Pacman's currently legal moves."""

    def __init__(self, seed: int | None = None) -> None:
        """Create a Pacman random policy with an optional deterministic seed."""
        self._rng = random.Random(seed)
        self._current_direction: Direction | None = None

    def next_action(self, state: GameState, config: dict | None = None) -> Direction:
        """Return one corridor-aware random Pacman move."""
        del config
        self._current_direction = choose_corridor_random_direction(
            state=state,
            role=Role.PACMAN,
            rng=self._rng,
            current_direction=self._current_direction,
        )
        return self._current_direction

    def reset(self) -> None:
        """Clear the remembered movement direction before a new match."""
        self._current_direction = None

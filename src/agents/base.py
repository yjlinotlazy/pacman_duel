from __future__ import annotations

"""Shared agent protocol used by session orchestration."""

from typing import Protocol

from src.core.domain import Direction, GameState


class Agent(Protocol):
    """Minimal interface every controllable role implementation must satisfy."""

    def next_action(self, state: GameState, config: dict) -> Direction:
        """Choose one action for the current tick without mutating state."""
        ...

    def reset(self) -> None:
        """Clear any per-match internal state before a new game starts."""
        ...

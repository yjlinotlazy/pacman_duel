"""Human-controlled agent driven by externally supplied input."""

from __future__ import annotations

from src.core.domain import Direction, GameState, Role


class HumanAgent:
    """Return the latest queued human input for one role."""

    def __init__(self, role: Role) -> None:
        """Bind the agent to a role and start with no pending input."""
        self.role = role
        self._pending_action = Direction.STAY

    def set_pending_action(self, action: Direction) -> None:
        """Store the next action supplied by the UI or other input layer."""
        self._pending_action = action

    def next_action(self, state: GameState, config: dict | None = None) -> Direction:
        """Return the latest queued action, defaulting to `STAY`."""
        del state, config
        return self._pending_action

    def reset(self) -> None:
        """Clear any queued input before starting a new match."""
        self._pending_action = Direction.STAY

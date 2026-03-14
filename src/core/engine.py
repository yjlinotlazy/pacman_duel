"""Engine that applies per-tick actions using the core rule helpers."""

from __future__ import annotations

from dataclasses import replace

from .domain import Direction, EntityState, GameState, Role
from .rules import apply_action, consume_dot, resolve_status


class GameEngine:
    """Owns the current match state and advances it one tick at a time."""

    def __init__(self, initial_state: GameState) -> None:
        """Store the initial state and start the engine from that snapshot."""
        self._initial_state = initial_state
        self._state = initial_state

    @property
    def state(self) -> GameState:
        """Return the current engine state."""
        return self._state

    def reset(self) -> GameState:
        """Restore the engine back to its initial match state."""
        self._state = self._initial_state
        return self._state

    def step(self, actions: dict[Role, Direction]) -> GameState:
        """Advance the match by one tick using the provided role actions."""
        if self._state.status.value != "running":
            return self._state

        next_state = self._state
        for role in (Role.PACMAN, Role.SLIME, Role.HELPER):
            next_state = apply_action(
                next_state,
                role,
                actions.get(role, Direction.STAY),
            )

        next_state = consume_dot(next_state)
        next_state = resolve_status(replace(next_state, tick=next_state.tick + 1))
        self._state = next_state
        return self._state


def build_initial_state(
    board: "Board",
    spawns: dict[Role, "Position"],
) -> GameState:
    """Construct the first `GameState` from a parsed board and spawn map."""

    return GameState(
        board=board,
        pacman=EntityState(role=Role.PACMAN, position=spawns[Role.PACMAN]),
        slime=EntityState(role=Role.SLIME, position=spawns[Role.SLIME]),
        helper=EntityState(role=Role.HELPER, position=spawns[Role.HELPER]),
        dots=board.initial_dots,
        pacman_start=spawns[Role.PACMAN],
    )

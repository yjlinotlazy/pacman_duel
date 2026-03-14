"""Copycat agent that seeks Pacman's spawn and then replays Pacman's moves."""

from __future__ import annotations

from src.algorithms.pathfinding import bfs_shortest_path_direction
from src.core.domain import Direction, GameState, Role


class CopycatAgent:
    """Seek Pacman's start position, then replay Pacman's recorded actions."""

    def __init__(self, role: Role, target_role: Role = Role.PACMAN) -> None:
        """Bind the acting role and the role whose history should be copied."""
        self.role = role
        self.target_role = target_role
        self._replay_index = 0

    def next_action(self, state: GameState, config: dict | None = None) -> Direction:
        """Chase the target spawn first, then replay the target action history."""
        del config
        current_position = state.entity_for(self.role).position
        target_start = state.pacman_start
        if target_start is None:
            return Direction.STAY

        if current_position != target_start:
            return bfs_shortest_path_direction(
                start=current_position,
                goal=target_start,
                is_walkable=state.board.is_walkable,
            )

        if self._replay_index >= len(state.pacman_history):
            return Direction.STAY

        action = state.pacman_history[self._replay_index]
        self._replay_index += 1
        return action

    def reset(self) -> None:
        """Restart replay tracking for a new match."""
        self._replay_index = 0

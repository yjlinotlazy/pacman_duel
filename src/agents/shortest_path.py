from __future__ import annotations

"""Shortest-path pursuit agent built on BFS."""

from src.algorithms.pathfinding import bfs_shortest_path_direction
from src.core.domain import Direction, GameState, Role


class ShortestPathAgent:
    """Move toward a target role using the board's shortest walkable path."""

    def __init__(self, role: Role, target_role: Role = Role.PACMAN) -> None:
        """Bind the acting role and the role it should chase."""
        self.role = role
        self.target_role = target_role

    def next_action(self, state: GameState, config: dict | None = None) -> Direction:
        """Choose the first BFS step from the actor to the current target."""
        start = state.entity_for(self.role).position
        goal = state.entity_for(self.target_role).position
        return bfs_shortest_path_direction(
            start=start,
            goal=goal,
            is_walkable=state.board.is_walkable,
        )

    def reset(self) -> None:
        """Reset hook for protocol compatibility; no state is currently stored."""
        return None

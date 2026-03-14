"""Pathfinding helpers used by pursuit-style agents."""

from __future__ import annotations

from collections import deque

from src.core.domain import Direction, MOVE_PRIORITY, Position


def bfs_shortest_path_direction(
    start: Position,
    goal: Position,
    is_walkable: callable,
) -> Direction:
    """Return the first move on a BFS shortest path, or `STAY` if unreachable."""
    if start == goal:
        return Direction.STAY

    frontier: deque[Position] = deque([start])
    first_step: dict[Position, Direction | None] = {start: None}

    while frontier:
        current = frontier.popleft()
        for direction in MOVE_PRIORITY:
            nxt = current.moved(direction)
            if nxt in first_step or not is_walkable(nxt):
                continue

            candidate = direction if current == start else first_step[current]
            first_step[nxt] = candidate
            if nxt == goal:
                return candidate or Direction.STAY
            frontier.append(nxt)

    return Direction.STAY

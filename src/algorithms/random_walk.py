"""Shared random-walk helpers for corridor-aware movement policies."""

from __future__ import annotations

import random

from src.core.domain import Direction, GameState, Position, Role
from src.core.rules import legal_actions

OPPOSITE_DIRECTION: dict[Direction, Direction] = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
    Direction.STAY: Direction.STAY,
}


def choose_corridor_random_direction(
    state: GameState,
    role: Role,
    rng: random.Random,
    current_direction: Direction | None,
) -> Direction:
    """Choose a random direction while avoiding backtracking except at dead ends."""
    directional_actions = [
        direction
        for direction in legal_actions(state, role)
        if direction is not Direction.STAY
    ]
    if not directional_actions:
        return Direction.STAY

    reverse_direction = (
        OPPOSITE_DIRECTION[current_direction]
        if current_direction not in {None, Direction.STAY}
        else None
    )
    forward_is_legal = current_direction in directional_actions

    if current_direction is None or current_direction is Direction.STAY or not forward_is_legal:
        return _choose_non_reverse_or_fallback(directional_actions, reverse_direction, rng)

    if _is_decision_point(directional_actions):
        return _choose_non_reverse_or_fallback(directional_actions, reverse_direction, rng)

    return current_direction


def _choose_non_reverse_or_fallback(
    directional_actions: list[Direction],
    reverse_direction: Direction | None,
    rng: random.Random,
) -> Direction:
    """Pick randomly from non-reverse actions, falling back to reverse if necessary."""
    if reverse_direction is None:
        return rng.choice(directional_actions)

    options = [direction for direction in directional_actions if direction != reverse_direction]
    if options:
        return rng.choice(options)
    return reverse_direction


def _is_decision_point(directional_actions: list[Direction]) -> bool:
    """Return whether the actor is at an intersection or a corner."""
    if len(directional_actions) <= 1:
        return False
    if len(directional_actions) >= 3:
        return True

    first, second = directional_actions
    return OPPOSITE_DIRECTION[first] != second

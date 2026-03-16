"""Stable mapping between policy outputs and runtime directions."""

from __future__ import annotations

from collections.abc import Sequence

from src.core.domain import Direction

ACTION_MAPPING_VERSION = "v1"

ACTION_INDEX_TO_DIRECTION: tuple[Direction, ...] = (
    Direction.UP,
    Direction.LEFT,
    Direction.DOWN,
    Direction.RIGHT,
    Direction.STAY,
)

DIRECTION_TO_ACTION_INDEX: dict[Direction, int] = {
    direction: index for index, direction in enumerate(ACTION_INDEX_TO_DIRECTION)
}


def direction_from_action_index(action_index: int) -> Direction:
    """Map one policy output index to a runtime direction."""
    if 0 <= action_index < len(ACTION_INDEX_TO_DIRECTION):
        return ACTION_INDEX_TO_DIRECTION[action_index]
    return Direction.STAY


def best_direction_for_scores(action_scores: Sequence[object]) -> Direction:
    """Choose the best direction from an ordered score vector."""
    if len(action_scores) != len(ACTION_INDEX_TO_DIRECTION):
        return Direction.STAY

    best_index = 0
    best_score = action_scores[0]
    if not isinstance(best_score, int | float):
        return Direction.STAY

    for index, score in enumerate(action_scores[1:], start=1):
        if not isinstance(score, int | float):
            return Direction.STAY
        if score > best_score:
            best_index = index
            best_score = score
    return direction_from_action_index(best_index)


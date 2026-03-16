"""Versioned observation encoding for runtime RL inference."""

from __future__ import annotations

from typing import cast

from src.core.domain import GameState, Position, Role

OBSERVATION_VERSION = "v1"


def encode_observation(state: GameState, role: Role) -> dict[str, object]:
    """Convert the current immutable game state into a deterministic observation."""
    return {
        "version": OBSERVATION_VERSION,
        "role": role.value,
        "tick": state.tick,
        "speed_scaling_factor": state.speed_scaling_factor,
        "board_size": (state.board.width, state.board.height),
        "actor_position": _position_tuple(state.entity_for(role).position),
        "pacman_position": _position_tuple(state.pacman.position),
        "slime_position": _position_tuple(state.slime.position),
        "helper_position": _position_tuple(state.helper.position),
        "pacman_start": _position_tuple(state.pacman_start),
        "dots": tuple(sorted(_dot_position_tuple(dot) for dot in state.dots)),
        "walls": tuple(
            sorted(
                (x, y)
                for y in range(state.board.height)
                for x in range(state.board.width)
                if not state.board.is_walkable(Position(x, y))
            )
        ),
        "pacman_history": tuple(direction.name for direction in state.pacman_history),
    }


def _position_tuple(position: Position | None) -> tuple[int, int] | None:
    """Render positions in a JSON-friendly stable form."""
    if position is None:
        return None
    return (position.x, position.y)


def _dot_position_tuple(position: Position) -> tuple[int, int]:
    """Render known-present positions without the optional return type."""
    return cast(tuple[int, int], _position_tuple(position))

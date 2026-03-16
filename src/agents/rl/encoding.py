"""Versioned observation encoding for runtime RL inference."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.domain import Direction, GameState, Position, Role

OBSERVATION_VERSION = "v2"

GridPoint = tuple[int, int]


@dataclass(frozen=True, slots=True)
class EncodedObservation:
    """Typed, versioned observation shared by runtime inference and training."""

    version: str
    role: str
    tick: int
    speed_scaling_factor: int | str
    board_size: GridPoint
    actor_position: GridPoint
    pacman_position: GridPoint
    slime_position: GridPoint
    helper_position: GridPoint
    pacman_start: GridPoint
    dots: tuple[GridPoint, ...]
    walls: tuple[GridPoint, ...]
    pacman_history: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        """Render the observation in a JSON-friendly structured form."""
        return {
            "version": self.version,
            "role": self.role,
            "tick": self.tick,
            "speed_scaling_factor": self.speed_scaling_factor,
            "board_size": self.board_size,
            "actor_position": self.actor_position,
            "pacman_position": self.pacman_position,
            "slime_position": self.slime_position,
            "helper_position": self.helper_position,
            "pacman_start": self.pacman_start,
            "dots": self.dots,
            "walls": self.walls,
            "pacman_history": self.pacman_history,
        }

    def flat_features(self) -> tuple[float, ...]:
        """Convert the observation into a stable numeric feature vector."""
        width, height = self.board_size
        speed = float(self.speed_scaling_factor) if isinstance(self.speed_scaling_factor, int) else 0.0
        history_counts = tuple(float(self.pacman_history.count(direction.name)) for direction in Direction)
        return (
            float(self.tick),
            float(width),
            float(height),
            speed,
            float(self.actor_position[0]),
            float(self.actor_position[1]),
            float(self.pacman_position[0]),
            float(self.pacman_position[1]),
            float(self.slime_position[0]),
            float(self.slime_position[1]),
            float(self.helper_position[0]),
            float(self.helper_position[1]),
            float(self.pacman_start[0]),
            float(self.pacman_start[1]),
            float(len(self.dots)),
            float(len(self.walls)),
            *history_counts,
        )


def encode_observation(state: GameState, role: Role) -> EncodedObservation:
    """Convert the current immutable game state into a deterministic observation."""
    pacman_start = state.pacman_start
    if pacman_start is None:
        raise ValueError("GameState.pacman_start must be set for RL observation encoding")

    return EncodedObservation(
        version=OBSERVATION_VERSION,
        role=role.value,
        tick=state.tick,
        speed_scaling_factor=state.speed_scaling_factor,
        board_size=(state.board.width, state.board.height),
        actor_position=_position_tuple(state.entity_for(role).position),
        pacman_position=_position_tuple(state.pacman.position),
        slime_position=_position_tuple(state.slime.position),
        helper_position=_position_tuple(state.helper.position),
        pacman_start=_position_tuple(pacman_start),
        dots=tuple(sorted(_position_tuple(dot) for dot in state.dots)),
        walls=tuple(
            sorted(
                (x, y)
                for y in range(state.board.height)
                for x in range(state.board.width)
                if not state.board.is_walkable(Position(x, y))
            )
        ),
        pacman_history=tuple(direction.name for direction in state.pacman_history),
    )


def _position_tuple(position: Position) -> GridPoint:
    """Render positions in a stable tuple form."""
    return (position.x, position.y)

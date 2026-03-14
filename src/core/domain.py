from __future__ import annotations

"""Core immutable domain types shared by the engine, rules, and agents."""

from dataclasses import dataclass, replace
from enum import Enum


class Direction(Enum):
    """Grid movement directions used by all controllers and rules."""

    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    STAY = (0, 0)

    @property
    def delta(self) -> tuple[int, int]:
        """Return the `(dx, dy)` movement vector for this direction."""
        return self.value


MOVE_PRIORITY: tuple[Direction, ...] = (
    Direction.UP,
    Direction.LEFT,
    Direction.DOWN,
    Direction.RIGHT,
)


class Role(Enum):
    """Logical roles that can act during a match tick."""

    PACMAN = "pacman"
    SLIME = "slime"
    HELPER = "helper"


class MatchStatus(Enum):
    """Terminal and non-terminal match states."""

    RUNNING = "running"
    PACMAN_WIN = "pacman_win"
    ENEMY_WIN = "enemy_win"


class Tile(Enum):
    """Board tile types for parsing and future rendering needs."""

    WALL = "#"
    DOT = "."
    EMPTY = " "


@dataclass(frozen=True, slots=True)
class Position:
    """Immutable grid coordinate."""

    x: int
    y: int

    def moved(self, direction: Direction) -> "Position":
        """Return a new position produced by applying one direction step."""
        dx, dy = direction.delta
        return Position(self.x + dx, self.y + dy)


@dataclass(frozen=True, slots=True)
class EntityState:
    """Runtime position for one actor on the board."""

    role: Role
    position: Position


@dataclass(frozen=True, slots=True)
class GameState:
    """Complete immutable snapshot of one match at a single tick."""

    board: "Board"
    pacman: EntityState
    slime: EntityState
    helper: EntityState
    dots: frozenset[Position]
    status: MatchStatus = MatchStatus.RUNNING
    tick: int = 0
    pacman_start: Position | None = None
    pacman_history: tuple[Direction, ...] = ()

    def __post_init__(self) -> None:
        """Default the recorded Pacman start position to the initial spawn."""
        if self.pacman_start is None:
            object.__setattr__(self, "pacman_start", self.pacman.position)

    def entity_for(self, role: Role) -> EntityState:
        """Return the entity state for the requested role."""
        return {
            Role.PACMAN: self.pacman,
            Role.SLIME: self.slime,
            Role.HELPER: self.helper,
        }[role]

    def with_entity(self, role: Role, entity: EntityState) -> "GameState":
        """Return a copy of the state with one entity replaced."""
        if role == Role.PACMAN:
            return replace(self, pacman=entity)
        if role == Role.SLIME:
            return replace(self, slime=entity)
        if role == Role.HELPER:
            return replace(self, helper=entity)
        raise ValueError(f"Unsupported role: {role}")

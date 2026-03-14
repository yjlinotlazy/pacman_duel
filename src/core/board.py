"""Board representation and parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import Position, Role


@dataclass(frozen=True, slots=True)
class Board:
    """Static board layout data shared across all game states."""

    width: int
    height: int
    walls: frozenset[Position]
    initial_dots: frozenset[Position]

    def in_bounds(self, position: Position) -> bool:
        """Return whether a position lies within the board rectangle."""
        return 0 <= position.x < self.width and 0 <= position.y < self.height

    def is_wall(self, position: Position) -> bool:
        """Return whether a position is occupied by a wall."""
        return position in self.walls

    def is_walkable(self, position: Position) -> bool:
        """Return whether an actor may move onto a position."""
        return self.in_bounds(position) and not self.is_wall(position)

    @classmethod
    def from_ascii(
        cls,
        lines: list[str] | tuple[str, ...],
    ) -> tuple["Board", dict[Role, Position]]:
        """Parse a rectangular ASCII map into board data and spawn positions."""
        if not lines:
            raise ValueError("Board layout cannot be empty")

        width = len(lines[0])
        if any(len(line) != width for line in lines):
            raise ValueError("Board layout must be rectangular")

        walls: set[Position] = set()
        dots: set[Position] = set()
        spawns: dict[Role, Position] = {}
        role_for_char = {"P": Role.PACMAN, "S": Role.SLIME, "H": Role.HELPER}

        for y, line in enumerate(lines):
            for x, cell in enumerate(line):
                position = Position(x, y)
                if cell == "#":
                    walls.add(position)
                elif cell == ".":
                    dots.add(position)
                elif cell in role_for_char:
                    role = role_for_char[cell]
                    if role in spawns:
                        raise ValueError(f"Duplicate spawn for {role.value}")
                    spawns[role] = position
                elif cell != " ":
                    raise ValueError(f"Unsupported board cell: {cell!r}")

        missing = {Role.PACMAN, Role.SLIME, Role.HELPER} - set(spawns)
        if missing:
            missing_names = ", ".join(sorted(role.value for role in missing))
            raise ValueError(f"Missing spawns for: {missing_names}")

        return (
            cls(
                width=width,
                height=len(lines),
                walls=frozenset(walls),
                initial_dots=frozenset(dots),
            ),
            spawns,
        )

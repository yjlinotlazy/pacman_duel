from __future__ import annotations

from src.core.board import Board
from src.core.domain import Direction, Position, Role


def test_board_ascii_parser_collects_spawns_and_dots() -> None:
    board, spawns = Board.from_ascii(
        (
            "#####",
            "#P.S#",
            "# .H#",
            "#####",
        )
    )

    assert board.width == 5
    assert board.height == 4
    assert spawns[Role.PACMAN] == Position(1, 1)
    assert spawns[Role.SLIME] == Position(3, 1)
    assert spawns[Role.HELPER] == Position(3, 2)
    assert Position(2, 2) in board.initial_dots


def test_board_parser_requires_all_spawns() -> None:
    try:
        Board.from_ascii(
            (
                "#####",
                "#P  #",
                "# . #",
                "#####",
            )
        )
    except ValueError as exc:
        assert "Missing spawns" in str(exc)
    else:
        raise AssertionError("Expected parser to reject missing spawns")

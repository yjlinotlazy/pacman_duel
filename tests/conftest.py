from __future__ import annotations

from src.core.board import Board
from src.core.engine import build_initial_state


def build_state(layout: tuple[str, ...]):
    board, spawns = Board.from_ascii(layout)
    return build_initial_state(board, spawns)

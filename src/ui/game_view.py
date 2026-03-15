"""Realtime board rendering and input capture for one active match."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QKeyEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.agents.human import HumanAgent
from src.core.domain import Direction, MatchStatus, Position, Role, Tile
from src.game_session import GameSession

CELL_SIZE = 36


class BoardCanvas(QWidget):
    """Draw the current game state as a simple grid board."""

    def __init__(self, session: GameSession, parent: QWidget | None = None) -> None:
        """Bind the canvas to a session-owned game state."""
        super().__init__(parent)
        self._session = session
        board = session.state.board
        self.setMinimumSize(board.width * CELL_SIZE, board.height * CELL_SIZE)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the board tiles, dots, and entities."""
        del event
        state = self._session.state
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#111111"))

        for y in range(state.board.height):
            for x in range(state.board.width):
                top_left_x = x * CELL_SIZE
                top_left_y = y * CELL_SIZE
                position = Position(x, y)
                if position in state.board.walls:
                    painter.fillRect(top_left_x, top_left_y, CELL_SIZE, CELL_SIZE, QColor("#24456b"))
                else:
                    painter.fillRect(top_left_x, top_left_y, CELL_SIZE, CELL_SIZE, QColor("#000000"))

                if position in state.dots:
                    painter.setBrush(QColor("#ffd24a"))
                    painter.setPen(Qt.PenStyle.NoPen)
                    dot_offset = CELL_SIZE // 2
                    painter.drawEllipse(top_left_x + dot_offset - 3, top_left_y + dot_offset - 3, 6, 6)

        self._draw_pacman(painter, state.pacman.position)
        self._draw_entity(painter, state.slime.position, QColor("#5ad18c"), 6)
        self._draw_entity(painter, state.helper.position, QColor("#ff7f6e"), 10)

    def _draw_pacman(self, painter: QPainter, position: Position) -> None:
        """Draw Pacman as a larger wedge so it cannot be confused with pellets."""
        center_x = position.x * CELL_SIZE + CELL_SIZE / 2
        center_y = position.y * CELL_SIZE + CELL_SIZE / 2
        radius = CELL_SIZE / 2 - 5

        painter.setBrush(QColor("#ffd24a"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPie(
            int(center_x - radius),
            int(center_y - radius),
            int(radius * 2),
            int(radius * 2),
            30 * 16,
            300 * 16,
        )

    def _draw_entity(self, painter: QPainter, position: Position, color: QColor, inset: int) -> None:
        """Draw one actor as a filled circle inside its grid cell."""
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            position.x * CELL_SIZE + inset,
            position.y * CELL_SIZE + inset,
            CELL_SIZE - inset * 2,
            CELL_SIZE - inset * 2,
        )


class GameView(QWidget):
    """Run one active session, render it, and forward keyboard input."""

    def __init__(
        self,
        session: GameSession,
        restart_match: Callable[[], None],
        return_to_menu: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        """Create the board view and start the match timer."""
        super().__init__(parent)
        self._session = session
        self._restart_match = restart_match
        self._return_to_menu = return_to_menu
        self._status_label = QLabel()
        self._board_canvas = BoardCanvas(session, self)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Arrow keys move Pacman. Press R to replay. Press Q or Esc to return to the menu."))
        layout.addWidget(self._status_label)
        layout.addWidget(self._board_canvas)
        self._attach_board_input()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(160)
        self._refresh_status()

    def showEvent(self, event) -> None:
        """Focus the board canvas when the view is shown."""
        super().showEvent(event)
        self._board_canvas.setFocus()

    def eventFilter(self, watched, event) -> bool:
        """Handle keyboard input from the focused board canvas."""
        if watched is self._board_canvas and event.type() == event.Type.KeyPress:
            self.keyPressEvent(event)
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Route global match keys for menu exit and human movement."""
        if event.key() == Qt.Key.Key_R:
            self._timer.stop()
            self._restart_match()
            return

        if event.key() in (Qt.Key.Key_Q, Qt.Key.Key_Escape):
            self._timer.stop()
            self._return_to_menu()
            return

        direction = {
            Qt.Key.Key_Up: Direction.UP,
            Qt.Key.Key_Down: Direction.DOWN,
            Qt.Key.Key_Left: Direction.LEFT,
            Qt.Key.Key_Right: Direction.RIGHT,
        }.get(event.key())
        if direction is None:
            super().keyPressEvent(event)
            return

        pacman_agent = self._session.agents.get(Role.PACMAN)
        if isinstance(pacman_agent, HumanAgent):
            pacman_agent.set_pending_action(direction)
        self._board_canvas.update()

    def _attach_board_input(self) -> None:
        """Route focused canvas key presses through the view-level handler."""
        self._board_canvas.installEventFilter(self)

    def _tick(self) -> None:
        """Advance the match and stop when it reaches a terminal state."""
        if self._session.state.status == MatchStatus.RUNNING:
            self._session.step()
        self._refresh_status()
        self._board_canvas.update()
        if self._session.state.status != MatchStatus.RUNNING:
            self._timer.stop()

    def _refresh_status(self) -> None:
        """Update the status text shown above the board."""
        state = self._session.state
        status_text = {
            MatchStatus.RUNNING: "Running",
            MatchStatus.PACMAN_WIN: "Pacman wins",
            MatchStatus.ENEMY_WIN: "Enemy wins",
        }[state.status]
        self._status_label.setText(f"Tick: {state.tick} | Status: {status_text}")

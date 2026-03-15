"""Main application window for the local GUI prototype."""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QStackedWidget

from src.app_controller import AppController, MatchConfig
from src.ui.game_view import GameView
from src.ui.menu_screen import MenuScreen


class MainWindow(QMainWindow):
    """Own the menu/game screens and route lifecycle actions through the controller."""

    def __init__(self, controller: AppController, parent=None) -> None:
        """Create the main window and show the menu by default."""
        super().__init__(parent)
        self._controller = controller
        self._current_config: MatchConfig | None = None
        self._stack = QStackedWidget(self)
        self.setCentralWidget(self._stack)
        self.setWindowTitle("pacman_duel")
        self.resize(680, 560)

        self._menu_screen = MenuScreen(
            start_match=self._start_match,
            quit_app=self.close,
            parent=self,
        )
        self._stack.addWidget(self._menu_screen)
        self._stack.setCurrentWidget(self._menu_screen)

    def _start_match(self, config: MatchConfig) -> None:
        """Create a session and show the playable game screen."""
        self._current_config = config
        session = self._controller.switch_session(config) if self._controller.current_session else self._controller.create_session(config)
        game_view = GameView(
            session=session,
            restart_match=self._restart_match,
            return_to_menu=self._show_menu,
            parent=self,
        )
        self._stack.addWidget(game_view)
        self._stack.setCurrentWidget(game_view)

    def _restart_match(self) -> None:
        """Start a fresh session using the most recent match configuration."""
        if self._current_config is None:
            return
        current_widget = self._stack.currentWidget()
        self._start_match(self._current_config)
        if current_widget is not None and current_widget is not self._menu_screen:
            self._stack.removeWidget(current_widget)
            current_widget.deleteLater()

    def _show_menu(self) -> None:
        """Return to the menu and tear down the active session."""
        current_widget = self._stack.currentWidget()
        self._controller.destroy_session()
        self._stack.setCurrentWidget(self._menu_screen)
        if current_widget is not None and current_widget is not self._menu_screen:
            self._stack.removeWidget(current_widget)
            current_widget.deleteLater()

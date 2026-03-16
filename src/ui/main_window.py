"""Main application window for the local GUI prototype."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from src.app_controller import AppController, MatchConfig
from src.ui.config_panel import ConfigPanel
from src.ui.game_view import GameView


class MainWindow(QMainWindow):
    """Own the menu/game screens and route lifecycle actions through the controller."""

    def __init__(self, controller: AppController, parent=None) -> None:
        """Create the main window and show the menu by default."""
        super().__init__(parent)
        self._controller = controller
        self._current_config: MatchConfig | None = None
        self.setWindowTitle("pacman_duel")
        self.resize(760, 760)

        root = QWidget(self)
        self.setCentralWidget(root)

        self._config_panel = ConfigPanel(self)
        self._status_banner = QLabel("Configure a match above, then start playing below.")
        self._status_banner.setWordWrap(True)

        start_button = QPushButton("Start Match")
        start_button.clicked.connect(self._start_match_from_panel)
        replay_button = QPushButton("Replay Current Config")
        replay_button.clicked.connect(self._restart_match)
        stop_button = QPushButton("Stop Match")
        stop_button.clicked.connect(self._clear_match)
        quit_button = QPushButton("Quit App")
        quit_button.clicked.connect(self.close)

        button_row = QHBoxLayout()
        button_row.addWidget(start_button)
        button_row.addWidget(replay_button)
        button_row.addWidget(stop_button)
        button_row.addWidget(quit_button)

        self._content_layout = QVBoxLayout()
        self._content_layout.addWidget(QLabel("Game Board"))
        self._content_layout.addWidget(self._status_banner)
        self._content_layout.addStretch()

        layout = QVBoxLayout(root)
        layout.addWidget(self._config_panel)
        layout.addLayout(button_row)
        layout.addLayout(self._content_layout)

    def _start_match_from_panel(self) -> None:
        """Start a match using the currently visible configuration controls."""
        self._start_match(self._config_panel.build_match_config())

    def _start_match(self, config: MatchConfig) -> None:
        """Create a session and show the playable game screen under the controls."""
        self._current_config = config
        session = self._controller.switch_session(config) if self._controller.current_session else self._controller.create_session(config)
        self._clear_match(destroy_session=False)
        game_view = GameView(
            session=session,
            restart_match=self._restart_match,
            return_to_menu=self._clear_match,
            parent=self,
        )
        self._content_layout.addWidget(game_view)
        self._content_layout.setStretchFactor(game_view, 1)
        self._status_banner.setText("Match running. You can change config above and start a new match at any time.")
        self._game_view = game_view

    def _restart_match(self) -> None:
        """Start a fresh session using the most recent match configuration."""
        if self._current_config is None:
            return
        self._start_match(self._current_config)

    def _clear_match(self, destroy_session: bool = True) -> None:
        """Remove the current board view while keeping the top controls visible."""
        if destroy_session:
            self._controller.destroy_session()

        game_view = getattr(self, "_game_view", None)
        if game_view is not None:
            self._content_layout.removeWidget(game_view)
            game_view.deleteLater()
            self._game_view = None
        self._status_banner.setText("Configure a match above, then start playing below.")

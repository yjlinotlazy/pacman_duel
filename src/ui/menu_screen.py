"""Main menu screen for launching a local match."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from src.app_controller import MatchConfig
from src.ui.config_panel import ConfigPanel


class MenuScreen(QWidget):
    """Collect match configuration and signal the app to start a game."""

    def __init__(
        self,
        start_match: Callable[[MatchConfig], None],
        quit_app: Callable[[], None],
        parent: QWidget | None = None,
    ) -> None:
        """Render the menu and wire the start action."""
        super().__init__(parent)
        self._start_match = start_match
        self._quit_app = quit_app
        self._config_panel = ConfigPanel(self)

        title = QLabel("pacman_duel")
        title.setObjectName("title")
        subtitle = QLabel("Local duel prototype: choose controllers and start a match.")
        start_button = QPushButton("Start Match")
        start_button.clicked.connect(self._handle_start)
        quit_button = QPushButton("Quit App")
        quit_button.clicked.connect(self._quit_app)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self._config_panel)
        layout.addWidget(start_button)
        layout.addWidget(quit_button)
        layout.addStretch()

    def _handle_start(self) -> None:
        """Translate the selected options into a new match request."""
        self._start_match(self._config_panel.build_match_config())

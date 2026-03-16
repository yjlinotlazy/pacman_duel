"""Simple configuration controls for starting a local match."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QWidget

from src.app_controller import AgentConfig, MatchConfig
from src.boards.classic_inspired_board import CLASSIC_INSPIRED_BOARD_LAYOUT
from src.boards.default_board import DEFAULT_BOARD_LAYOUT

BOARD_OPTIONS = (
    ("Default Maze", "default", DEFAULT_BOARD_LAYOUT),
    ("Classic Inspired", "classic_inspired", CLASSIC_INSPIRED_BOARD_LAYOUT),
)


class ConfigPanel(QWidget):
    """Collect minimal runtime configuration for a playable local match."""

    config_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the controller and algorithm selectors."""
        super().__init__(parent)

        self._pacman_controller = QComboBox()
        self._pacman_controller.addItem("Human", AgentConfig("human"))
        self._pacman_controller.addItem("AI: Random", AgentConfig("ai", "random"))

        self._board_selector = QComboBox()
        for label, board_id, board_layout in BOARD_OPTIONS:
            self._board_selector.addItem(label, (board_id, board_layout))

        self._slime_algorithm = QComboBox()
        self._slime_algorithm.addItem("Random", AgentConfig("ai", "random"))
        self._slime_algorithm.addItem("Shortest Path", AgentConfig("ai", "shortest_path"))
        self._slime_algorithm.addItem("Copycat", AgentConfig("ai", "copycat"))

        self._helper_algorithm = QComboBox()
        self._helper_algorithm.addItem("Shortest Path", AgentConfig("ai", "shortest_path"))
        self._helper_algorithm.addItem("Random", AgentConfig("ai", "random"))
        self._helper_algorithm.addItem("Copycat", AgentConfig("ai", "copycat"))

        self._speed_scaling_factor = QComboBox()
        self._speed_scaling_factor.addItem("1x (normal)", 1)
        self._speed_scaling_factor.addItem("2x slower", 2)
        self._speed_scaling_factor.addItem("3x slower", 3)
        self._speed_scaling_factor.addItem("Adaptive", "adaptive")
        self._speed_scaling_factor.setCurrentIndex(1)

        group = QGroupBox("Match Setup")
        form = QFormLayout(group)
        form.addRow("Board", self._board_selector)
        form.addRow("Pacman", self._pacman_controller)
        form.addRow("Slime AI", self._slime_algorithm)
        form.addRow("Helper AI", self._helper_algorithm)
        form.addRow("Enemy speed scaling", self._speed_scaling_factor)

        layout = QFormLayout(self)
        layout.addRow(group)

        for widget in (
            self._board_selector,
            self._pacman_controller,
            self._slime_algorithm,
            self._helper_algorithm,
            self._speed_scaling_factor,
        ):
            widget.currentIndexChanged.connect(self.config_changed.emit)

    def build_match_config(self) -> MatchConfig:
        """Build the `MatchConfig` selected by the user."""
        board_id, board_layout = self._board_selector.currentData()
        return MatchConfig(
            board_id=board_id,
            board_layout=board_layout,
            pacman_config=self._pacman_controller.currentData(),
            slime_config=self._slime_algorithm.currentData(),
            helper_config=self._helper_algorithm.currentData(),
            speed_scaling_factor=self._speed_scaling_factor.currentData(),
        )

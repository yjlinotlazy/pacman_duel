"""Simple configuration controls for starting a local match."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QGroupBox, QWidget

from src.app_controller import AgentConfig, MatchConfig

DEFAULT_BOARD_LAYOUT: tuple[str, ...] = (
    "##########",
    "#P......S#",
    "#.######.#",
    "#...H....#",
    "##########",
)


class ConfigPanel(QWidget):
    """Collect minimal runtime configuration for a playable local match."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the controller and algorithm selectors."""
        super().__init__(parent)

        self._pacman_controller = QComboBox()
        self._pacman_controller.addItem("Human", AgentConfig("human"))
        self._pacman_controller.addItem("AI: Random", AgentConfig("ai", "random"))

        self._slime_algorithm = QComboBox()
        self._slime_algorithm.addItem("Random", AgentConfig("ai", "random"))
        self._slime_algorithm.addItem("Shortest Path", AgentConfig("ai", "shortest_path"))
        self._slime_algorithm.addItem("Copycat", AgentConfig("ai", "copycat"))

        self._helper_algorithm = QComboBox()
        self._helper_algorithm.addItem("Shortest Path", AgentConfig("ai", "shortest_path"))
        self._helper_algorithm.addItem("Random", AgentConfig("ai", "random"))
        self._helper_algorithm.addItem("Copycat", AgentConfig("ai", "copycat"))

        group = QGroupBox("Match Setup")
        form = QFormLayout(group)
        form.addRow("Pacman", self._pacman_controller)
        form.addRow("Slime AI", self._slime_algorithm)
        form.addRow("Helper AI", self._helper_algorithm)

        layout = QFormLayout(self)
        layout.addRow(group)

    def build_match_config(self) -> MatchConfig:
        """Build the `MatchConfig` selected by the user."""
        return MatchConfig(
            board_layout=DEFAULT_BOARD_LAYOUT,
            pacman_config=self._pacman_controller.currentData(),
            slime_config=self._slime_algorithm.currentData(),
            helper_config=self._helper_algorithm.currentData(),
        )

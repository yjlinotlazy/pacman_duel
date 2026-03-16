"""Simple configuration controls for starting a local match."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

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
        self._pacman_controller.addItem("AI: RL", AgentConfig("ai", "rl"))

        self._board_selector = QComboBox()
        for label, board_id, board_layout in BOARD_OPTIONS:
            self._board_selector.addItem(label, (board_id, board_layout))

        self._slime_algorithm = QComboBox()
        self._slime_algorithm.addItem("Random", AgentConfig("ai", "random"))
        self._slime_algorithm.addItem("Shortest Path", AgentConfig("ai", "shortest_path"))
        self._slime_algorithm.addItem("Copycat", AgentConfig("ai", "copycat"))
        self._slime_algorithm.addItem("RL", AgentConfig("ai", "rl"))

        self._helper_algorithm = QComboBox()
        self._helper_algorithm.addItem("Shortest Path", AgentConfig("ai", "shortest_path"))
        self._helper_algorithm.addItem("Random", AgentConfig("ai", "random"))
        self._helper_algorithm.addItem("Copycat", AgentConfig("ai", "copycat"))
        self._helper_algorithm.addItem("RL", AgentConfig("ai", "rl"))

        self._pacman_checkpoint_path = QLineEdit()
        self._pacman_checkpoint_path.setPlaceholderText("Path to Pacman RL checkpoint")
        self._slime_checkpoint_path = QLineEdit()
        self._slime_checkpoint_path.setPlaceholderText("Path to Slime RL checkpoint")
        self._helper_checkpoint_path = QLineEdit()
        self._helper_checkpoint_path.setPlaceholderText("Path to Helper RL checkpoint")

        self._pacman_checkpoint_controls = self._build_checkpoint_controls(
            self._pacman_checkpoint_path,
            "Select Pacman RL checkpoint",
        )
        self._slime_checkpoint_controls = self._build_checkpoint_controls(
            self._slime_checkpoint_path,
            "Select Slime RL checkpoint",
        )
        self._helper_checkpoint_controls = self._build_checkpoint_controls(
            self._helper_checkpoint_path,
            "Select Helper RL checkpoint",
        )

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
        self._pacman_checkpoint_label = QLabel("Pacman RL checkpoint")
        form.addRow(self._pacman_checkpoint_label, self._pacman_checkpoint_controls)
        form.addRow("Slime AI", self._slime_algorithm)
        self._slime_checkpoint_label = QLabel("Slime RL checkpoint")
        form.addRow(self._slime_checkpoint_label, self._slime_checkpoint_controls)
        form.addRow("Helper AI", self._helper_algorithm)
        self._helper_checkpoint_label = QLabel("Helper RL checkpoint")
        form.addRow(self._helper_checkpoint_label, self._helper_checkpoint_controls)
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
        for widget in (
            self._pacman_controller,
            self._slime_algorithm,
            self._helper_algorithm,
        ):
            widget.currentIndexChanged.connect(self._sync_rl_field_visibility)
        for widget in (
            self._pacman_checkpoint_path,
            self._slime_checkpoint_path,
            self._helper_checkpoint_path,
        ):
            widget.textChanged.connect(self.config_changed.emit)
        self._sync_rl_field_visibility()

    def build_match_config(self) -> MatchConfig:
        """Build the `MatchConfig` selected by the user."""
        board_id, board_layout = self._board_selector.currentData()
        return MatchConfig(
            board_id=board_id,
            board_layout=board_layout,
            pacman_config=self._config_with_checkpoint(
                self._pacman_controller.currentData(),
                self._pacman_checkpoint_path.text(),
            ),
            slime_config=self._config_with_checkpoint(
                self._slime_algorithm.currentData(),
                self._slime_checkpoint_path.text(),
            ),
            helper_config=self._config_with_checkpoint(
                self._helper_algorithm.currentData(),
                self._helper_checkpoint_path.text(),
            ),
            speed_scaling_factor=self._speed_scaling_factor.currentData(),
        )

    def _build_checkpoint_controls(self, line_edit: QLineEdit, dialog_caption: str) -> QWidget:
        """Create one checkpoint-path row with a file picker shortcut."""
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(
            lambda: self._choose_checkpoint_path(line_edit, dialog_caption),
        )
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(line_edit)
        layout.addWidget(browse_button)
        return container

    def _choose_checkpoint_path(self, line_edit: QLineEdit, dialog_caption: str) -> None:
        """Prompt for one checkpoint path and store it in the matching line edit."""
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            dialog_caption,
            "",
            "Checkpoint Files (*.json);;All Files (*)",
        )
        if selected_path:
            line_edit.setText(selected_path)

    def _config_with_checkpoint(self, config: AgentConfig, checkpoint_path: str) -> AgentConfig:
        """Attach a checkpoint path only for RL controller selections."""
        if config.algorithm != "rl":
            return config
        params = dict(config.params)
        if checkpoint_path.strip():
            params["checkpoint_path"] = checkpoint_path.strip()
        return AgentConfig(config.controller_type, config.algorithm, params)

    def _sync_rl_field_visibility(self) -> None:
        """Show checkpoint selectors only for roles currently using RL."""
        self._set_checkpoint_row_visibility(
            self._pacman_checkpoint_label,
            self._pacman_checkpoint_controls,
            self._uses_rl(self._pacman_controller.currentData()),
        )
        self._set_checkpoint_row_visibility(
            self._slime_checkpoint_label,
            self._slime_checkpoint_controls,
            self._uses_rl(self._slime_algorithm.currentData()),
        )
        self._set_checkpoint_row_visibility(
            self._helper_checkpoint_label,
            self._helper_checkpoint_controls,
            self._uses_rl(self._helper_algorithm.currentData()),
        )

    def _uses_rl(self, config: AgentConfig) -> bool:
        """Return whether the selected controller requires a checkpoint path."""
        return config.algorithm == "rl"

    def _set_checkpoint_row_visibility(self, label: QLabel, controls: QWidget, visible: bool) -> None:
        """Toggle one checkpoint row as a unit."""
        label.setVisible(visible)
        controls.setVisible(visible)

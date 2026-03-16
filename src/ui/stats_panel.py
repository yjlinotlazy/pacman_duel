"""History-backed stats summary widget for the current match configuration."""

from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget

from src.stats.winrate import WinRateSummary


class StatsPanel(QWidget):
    """Display historical win-rate summaries for the selected configuration."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create a compact read-only stats display."""
        super().__init__(parent)

        self._samples_value = QLabel("0")
        self._pacman_win_rate_value = QLabel("0.0%")
        self._enemy_win_rate_value = QLabel("0.0%")

        group = QGroupBox("History Stats")
        form = QFormLayout(group)
        form.addRow("Samples", self._samples_value)
        form.addRow("Pacman win rate", self._pacman_win_rate_value)
        form.addRow("Enemy win rate", self._enemy_win_rate_value)

        layout = QFormLayout(self)
        layout.addRow(group)

    def set_summary(self, summary: WinRateSummary) -> None:
        """Render one computed summary into the widget labels."""
        self._samples_value.setText(str(summary.samples))
        self._pacman_win_rate_value.setText(f"{summary.pacman_win_rate * 100:.1f}%")
        self._enemy_win_rate_value.setText(f"{summary.enemy_win_rate * 100:.1f}%")

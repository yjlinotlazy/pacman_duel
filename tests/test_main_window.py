from __future__ import annotations

from PySide6.QtWidgets import QApplication

from src.app_controller import AppController
from src.ui.main_window import MainWindow


def _get_or_create_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_start_match_with_missing_rl_checkpoint_shows_error_banner() -> None:
    _get_or_create_app()
    window = MainWindow(AppController())
    window._config_panel._pacman_controller.setCurrentIndex(2)

    window._start_match_from_panel()

    assert "Unable to start match" in window._status_banner.text()

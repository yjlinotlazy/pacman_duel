"""Entry point for the local PySide6 prototype application."""

from __future__ import annotations

import sys
from pathlib import Path


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app_controller import AppController


def main() -> int:
    """Launch the local GUI application."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise SystemExit(
            "PySide6 is required to run the local GUI. Install it first.",
        ) from exc

    from src.ui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow(AppController())
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

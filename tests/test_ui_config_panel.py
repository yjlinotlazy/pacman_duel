from __future__ import annotations

from PySide6.QtWidgets import QApplication

from src.boards.classic_inspired_board import CLASSIC_INSPIRED_BOARD_LAYOUT
from src.boards.default_board import DEFAULT_BOARD_LAYOUT
from src.ui.config_panel import ConfigPanel


def _get_or_create_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_pacman_dropdown_only_contains_pacman_agent_options() -> None:
    _get_or_create_app()
    panel = ConfigPanel()

    options = [
        panel._pacman_controller.itemData(index)
        for index in range(panel._pacman_controller.count())
    ]

    assert [(option.controller_type, option.algorithm) for option in options] == [
        ("human", None),
        ("ai", "random"),
    ]


def test_slime_dropdown_contains_only_slime_side_algorithms() -> None:
    _get_or_create_app()
    panel = ConfigPanel()

    options = [
        panel._slime_algorithm.itemData(index)
        for index in range(panel._slime_algorithm.count())
    ]

    assert [(option.controller_type, option.algorithm) for option in options] == [
        ("ai", "random"),
        ("ai", "shortest_path"),
        ("ai", "copycat"),
    ]


def test_match_config_includes_selected_speed_scaling_factor() -> None:
    _get_or_create_app()
    panel = ConfigPanel()
    panel._speed_scaling_factor.setCurrentIndex(1)

    config = panel.build_match_config()

    assert config.speed_scaling_factor == 2


def test_match_config_can_select_adaptive_speed_scaling() -> None:
    _get_or_create_app()
    panel = ConfigPanel()
    panel._speed_scaling_factor.setCurrentIndex(3)

    config = panel.build_match_config()

    assert config.speed_scaling_factor == "adaptive"


def test_board_selector_defaults_to_default_board() -> None:
    _get_or_create_app()
    panel = ConfigPanel()

    assert panel.build_match_config().board_id == "default"
    assert panel.build_match_config().board_layout == DEFAULT_BOARD_LAYOUT


def test_board_selector_can_choose_classic_inspired_board() -> None:
    _get_or_create_app()
    panel = ConfigPanel()
    panel._board_selector.setCurrentIndex(1)

    assert panel.build_match_config().board_id == "classic_inspired"
    assert panel.build_match_config().board_layout == CLASSIC_INSPIRED_BOARD_LAYOUT

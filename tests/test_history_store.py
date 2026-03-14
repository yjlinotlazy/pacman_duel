from __future__ import annotations

from pathlib import Path

from src.core.domain import MatchStatus
from src.stats.history_store import JsonlMatchHistoryStore, MatchResult
from src.stats.winrate import StatsQuery, query_summary


def test_history_store_records_and_loads_results(tmp_path: Path) -> None:
    store = JsonlMatchHistoryStore(tmp_path / "history" / "matches.jsonl")
    result = MatchResult(
        winner=MatchStatus.PACMAN_WIN,
        tick_count=12,
        pacman_controller="human",
        slime_controller="shortest_path",
        helper_controller="copycat",
        parameter_snapshot={"difficulty": "normal"},
        board_id="default",
        played_at="2026-03-14T00:00:00+00:00",
    )

    store.record_result(result)

    assert store.load_results() == [result]


def test_history_store_returns_empty_results_for_missing_file(tmp_path: Path) -> None:
    store = JsonlMatchHistoryStore(tmp_path / "missing.jsonl")

    assert store.load_results() == []


def test_query_summary_filters_results_and_computes_win_rates() -> None:
    results = [
        MatchResult(
            winner=MatchStatus.PACMAN_WIN,
            tick_count=10,
            pacman_controller="human",
            slime_controller="shortest_path",
            helper_controller="copycat",
            parameter_snapshot={"seed": 1},
            board_id="default",
            played_at="2026-03-14T00:00:00+00:00",
        ),
        MatchResult(
            winner=MatchStatus.ENEMY_WIN,
            tick_count=15,
            pacman_controller="human",
            slime_controller="shortest_path",
            helper_controller="copycat",
            parameter_snapshot={"seed": 1},
            board_id="default",
            played_at="2026-03-14T00:01:00+00:00",
        ),
        MatchResult(
            winner=MatchStatus.ENEMY_WIN,
            tick_count=20,
            pacman_controller="random",
            slime_controller="shortest_path",
            helper_controller="copycat",
            parameter_snapshot={"seed": 2},
            board_id="alt",
            played_at="2026-03-14T00:02:00+00:00",
        ),
    ]

    summary = query_summary(
        results,
        StatsQuery(
            pacman_controller="human",
            slime_controller="shortest_path",
            parameter_snapshot={"seed": 1},
            board_id="default",
        ),
    )

    assert summary.samples == 2
    assert summary.pacman_win_rate == 0.5
    assert summary.enemy_win_rate == 0.5


def test_query_summary_returns_zero_rates_when_no_results_match() -> None:
    summary = query_summary(
        [],
        StatsQuery(pacman_controller="human"),
    )

    assert summary.samples == 0
    assert summary.pacman_win_rate == 0.0
    assert summary.enemy_win_rate == 0.0

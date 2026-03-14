"""Helpers for filtering stored matches and computing win-rate summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.domain import MatchStatus
from src.stats.history_store import MatchResult


@dataclass(frozen=True)
class StatsQuery:
    """Optional filters used when summarizing historical match results."""

    pacman_controller: str | None = None
    slime_controller: str | None = None
    helper_controller: str | None = None
    board_id: str | None = None
    parameter_snapshot: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WinRateSummary:
    """Win-rate summary computed from historical results."""

    pacman_win_rate: float
    enemy_win_rate: float
    samples: int


def query_summary(results: list[MatchResult], query: StatsQuery) -> WinRateSummary:
    """Filter results and compute Pacman/enemy win rates for the matching set."""
    filtered = [result for result in results if _matches_query(result, query)]
    samples = len(filtered)
    if samples == 0:
        return WinRateSummary(pacman_win_rate=0.0, enemy_win_rate=0.0, samples=0)

    pacman_wins = sum(result.winner == MatchStatus.PACMAN_WIN for result in filtered)
    enemy_wins = sum(result.winner == MatchStatus.ENEMY_WIN for result in filtered)
    return WinRateSummary(
        pacman_win_rate=pacman_wins / samples,
        enemy_win_rate=enemy_wins / samples,
        samples=samples,
    )


def _matches_query(result: MatchResult, query: StatsQuery) -> bool:
    """Return whether one stored result matches all requested filters."""
    if query.pacman_controller is not None and result.pacman_controller != query.pacman_controller:
        return False
    if query.slime_controller is not None and result.slime_controller != query.slime_controller:
        return False
    if query.helper_controller is not None and result.helper_controller != query.helper_controller:
        return False
    if query.board_id is not None and result.board_id != query.board_id:
        return False
    for key, value in query.parameter_snapshot.items():
        if result.parameter_snapshot.get(key) != value:
            return False
    return True

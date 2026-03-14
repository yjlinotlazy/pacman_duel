"""JSONL-backed storage for completed match results."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.core.domain import MatchStatus


@dataclass(frozen=True)
class MatchResult:
    """Serializable record of one completed match."""

    winner: MatchStatus
    tick_count: int
    pacman_controller: str
    slime_controller: str
    helper_controller: str
    parameter_snapshot: dict[str, Any] = field(default_factory=dict)
    board_id: str = "default"
    played_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )

    def to_record(self) -> dict[str, Any]:
        """Convert the result to a JSON-serializable dictionary."""
        record = asdict(self)
        record["winner"] = self.winner.value
        return record

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "MatchResult":
        """Build a result object from one persisted JSON record."""
        return cls(
            winner=MatchStatus(record["winner"]),
            tick_count=record["tick_count"],
            pacman_controller=record["pacman_controller"],
            slime_controller=record["slime_controller"],
            helper_controller=record["helper_controller"],
            parameter_snapshot=record.get("parameter_snapshot", {}),
            board_id=record.get("board_id", "default"),
            played_at=record.get("played_at", datetime.now(timezone.utc).isoformat()),
        )


class JsonlMatchHistoryStore:
    """Persist completed matches as one JSON object per line."""

    def __init__(self, path: str | Path) -> None:
        """Store results in a JSONL file at the provided path."""
        self.path = Path(path)

    def record_result(self, result: MatchResult) -> None:
        """Append one completed match result to the history file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="ascii") as handle:
            handle.write(json.dumps(result.to_record(), sort_keys=True))
            handle.write("\n")

    def load_results(self) -> list[MatchResult]:
        """Load all recorded match results from disk."""
        if not self.path.exists():
            return []

        results: list[MatchResult] = []
        with self.path.open("r", encoding="ascii") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue
                results.append(MatchResult.from_record(json.loads(stripped)))
        return results

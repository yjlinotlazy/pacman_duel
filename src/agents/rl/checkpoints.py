"""Checkpoint loading and metadata validation for runtime RL agents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.agents.rl.action_mapping import ACTION_MAPPING_VERSION
from src.agents.rl.encoding import OBSERVATION_VERSION


class RLCheckpointError(ValueError):
    """Raised when an RL checkpoint cannot be loaded safely."""


@dataclass(frozen=True, slots=True)
class RLCheckpoint:
    """Loaded checkpoint bundle for one inference-only policy."""

    metadata: dict[str, Any]
    action_scores: tuple[object, ...]


def load_rl_checkpoint(path: str | Path, expected_role_family: str) -> RLCheckpoint:
    """Load and validate one JSON checkpoint file."""
    checkpoint_path = Path(path)
    if not checkpoint_path.exists():
        raise RLCheckpointError(f"Checkpoint path does not exist: {checkpoint_path}")

    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RLCheckpointError("Checkpoint payload must be a JSON object")

    raw_metadata = payload.get("metadata")
    validate_checkpoint_metadata(raw_metadata, expected_role_family)
    metadata = _require_metadata_dict(raw_metadata)

    policy = payload.get("policy", {})
    if not isinstance(policy, dict):
        raise RLCheckpointError("Checkpoint policy must be a JSON object")

    action_scores = policy.get("action_scores", [])
    if not isinstance(action_scores, list):
        raise RLCheckpointError("Checkpoint action_scores must be a JSON array")

    return RLCheckpoint(metadata=dict(metadata), action_scores=tuple(action_scores))


def validate_checkpoint_metadata(metadata: Any, expected_role_family: str) -> None:
    """Validate the minimum metadata contract required by runtime inference."""
    if not isinstance(metadata, dict):
        raise RLCheckpointError("Checkpoint metadata must be a JSON object")

    required_fields = (
        "schema_version",
        "role_family",
        "observation_version",
        "action_mapping_version",
    )
    missing = [field for field in required_fields if field not in metadata]
    if missing:
        raise RLCheckpointError(f"Checkpoint metadata is missing required fields: {', '.join(missing)}")

    if metadata["schema_version"] != 1:
        raise RLCheckpointError(f"Unsupported checkpoint schema_version: {metadata['schema_version']}")
    if metadata["role_family"] != expected_role_family:
        raise RLCheckpointError(
            f"Checkpoint role_family {metadata['role_family']!r} does not match expected {expected_role_family!r}"
        )
    if metadata["observation_version"] != OBSERVATION_VERSION:
        raise RLCheckpointError(
            "Checkpoint observation_version does not match runtime observation contract"
        )
    if metadata["action_mapping_version"] != ACTION_MAPPING_VERSION:
        raise RLCheckpointError(
            "Checkpoint action_mapping_version does not match runtime action mapping contract"
        )


def _require_metadata_dict(metadata: Any) -> dict[str, Any]:
    """Narrow validated metadata to the expected dictionary type."""
    if not isinstance(metadata, dict):
        raise RLCheckpointError("Checkpoint metadata must be a JSON object")
    return metadata

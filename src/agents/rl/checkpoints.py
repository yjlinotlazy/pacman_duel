"""Checkpoint loading and metadata validation for runtime RL agents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.agents.rl.action_mapping import ACTION_INDEX_TO_DIRECTION
from src.agents.rl.action_mapping import ACTION_MAPPING_VERSION
from src.agents.rl.encoding import OBSERVATION_VERSION
from src.agents.rl.runner import LinearPolicyRunner, PolicyRunner, StaticScoresRunner


class RLCheckpointError(ValueError):
    """Raised when an RL checkpoint cannot be loaded safely."""


@dataclass(frozen=True, slots=True)
class RLCheckpoint:
    """Loaded checkpoint bundle for one inference-only policy."""

    metadata: dict[str, Any]
    runner: PolicyRunner
    runner_type: str


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

    runner_type = policy.get("runner_type", "static_scores")
    runner = _build_runner(policy, runner_type)
    return RLCheckpoint(metadata=dict(metadata), runner=runner, runner_type=runner_type)


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


def _build_runner(policy: dict[str, Any], runner_type: Any) -> PolicyRunner:
    """Build one inference runner from the checkpoint policy payload."""
    if runner_type == "static_scores":
        scores = _require_float_tuple(policy.get("action_scores"), "Checkpoint action_scores")
        _validate_action_score_length(scores)
        return StaticScoresRunner(scores=scores)
    if runner_type == "linear":
        weights = _require_matrix(policy.get("weights"), "Checkpoint linear weights")
        bias = _require_float_tuple(policy.get("bias"), "Checkpoint linear bias")
        if len(weights) != len(ACTION_INDEX_TO_DIRECTION):
            raise RLCheckpointError("Checkpoint linear weights must provide one row per action")
        if len(bias) != len(ACTION_INDEX_TO_DIRECTION):
            raise RLCheckpointError("Checkpoint linear bias must provide one value per action")
        feature_count = len(weights[0])
        if feature_count == 0:
            raise RLCheckpointError("Checkpoint linear weights cannot be empty")
        if any(len(row) != feature_count for row in weights):
            raise RLCheckpointError("Checkpoint linear weights must use a rectangular matrix")
        return LinearPolicyRunner(weights=weights, bias=bias)
    raise RLCheckpointError(f"Unsupported checkpoint runner_type: {runner_type!r}")


def _validate_action_score_length(scores: tuple[float, ...]) -> None:
    """Ensure score vectors match the runtime action mapping length."""
    if len(scores) != len(ACTION_INDEX_TO_DIRECTION):
        raise RLCheckpointError("Checkpoint action_scores length must match the runtime action mapping")


def _require_float_tuple(value: Any, error_prefix: str) -> tuple[float, ...]:
    """Validate a flat numeric sequence and normalize it to floats."""
    if not isinstance(value, list):
        raise RLCheckpointError(f"{error_prefix} must be a JSON array")
    normalized: list[float] = []
    for item in value:
        if not isinstance(item, int | float):
            raise RLCheckpointError(f"{error_prefix} must contain only numeric values")
        normalized.append(float(item))
    return tuple(normalized)


def _require_matrix(value: Any, error_prefix: str) -> tuple[tuple[float, ...], ...]:
    """Validate a numeric matrix and normalize it to tuples of floats."""
    if not isinstance(value, list):
        raise RLCheckpointError(f"{error_prefix} must be a JSON array of rows")
    rows: list[tuple[float, ...]] = []
    for row in value:
        rows.append(_require_float_tuple(row, error_prefix))
    return tuple(rows)

"""Checkpoint save/export helpers for standalone training workflows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.agents.rl.action_mapping import ACTION_MAPPING_VERSION
from src.agents.rl.encoding import OBSERVATION_VERSION

SCHEMA_VERSION = 1


def build_checkpoint_payload(
    *,
    role_family: str,
    runner_type: str,
    policy: dict[str, Any],
    metadata_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one runtime-compatible checkpoint payload."""
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "role_family": role_family,
        "observation_version": OBSERVATION_VERSION,
        "action_mapping_version": ACTION_MAPPING_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if metadata_overrides:
        metadata.update(metadata_overrides)
    return {
        "metadata": metadata,
        "policy": {
            "runner_type": runner_type,
            **policy,
        },
    }


def save_checkpoint(
    path: str | Path,
    *,
    role_family: str,
    runner_type: str,
    policy: dict[str, Any],
    metadata_overrides: dict[str, Any] | None = None,
) -> Path:
    """Write one runtime-compatible checkpoint file to an explicit path."""
    checkpoint_path = Path(path)
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_checkpoint_payload(
        role_family=role_family,
        runner_type=runner_type,
        policy=policy,
        metadata_overrides=metadata_overrides,
    )
    checkpoint_path.write_text(json.dumps(payload, sort_keys=True), encoding="ascii")
    return checkpoint_path


def save_versioned_checkpoint(
    directory: str | Path,
    *,
    role_family: str,
    runner_type: str,
    policy: dict[str, Any],
    label: str = "policy",
    metadata_overrides: dict[str, Any] | None = None,
    retention_limit: int | None = None,
) -> Path:
    """Write one timestamped checkpoint file and optionally prune older ones."""
    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    checkpoint_path = directory_path / f"{role_family}_{label}_{timestamp}.json"
    save_checkpoint(
        checkpoint_path,
        role_family=role_family,
        runner_type=runner_type,
        policy=policy,
        metadata_overrides=metadata_overrides,
    )
    if retention_limit is not None:
        apply_retention(directory_path, role_family=role_family, retention_limit=retention_limit)
    return checkpoint_path


def list_checkpoints(directory: str | Path, role_family: str | None = None) -> list[Path]:
    """Return saved checkpoints ordered from oldest to newest."""
    directory_path = Path(directory)
    if not directory_path.exists():
        return []
    pattern = "*.json" if role_family is None else f"{role_family}_*.json"
    return sorted(directory_path.glob(pattern))


def latest_checkpoint(directory: str | Path, role_family: str | None = None) -> Path | None:
    """Return the newest checkpoint path matching the requested role family."""
    checkpoints = list_checkpoints(directory, role_family=role_family)
    return checkpoints[-1] if checkpoints else None


def apply_retention(directory: str | Path, *, role_family: str, retention_limit: int) -> list[Path]:
    """Delete older checkpoints beyond the configured retention limit."""
    if retention_limit < 1:
        raise ValueError("retention_limit must be at least 1")
    checkpoints = list_checkpoints(directory, role_family=role_family)
    to_delete = checkpoints[:-retention_limit]
    for path in to_delete:
        path.unlink(missing_ok=True)
    return to_delete

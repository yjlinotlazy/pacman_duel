from __future__ import annotations

from src.agents.rl.checkpoints import load_rl_checkpoint
from src.training.checkpoints import (
    apply_retention,
    latest_checkpoint,
    list_checkpoints,
    save_checkpoint,
    save_versioned_checkpoint,
)


def test_save_checkpoint_writes_runtime_compatible_payload(tmp_path) -> None:
    checkpoint_path = save_checkpoint(
        tmp_path / "pacman_policy.json",
        role_family="pacman",
        runner_type="static_scores",
        policy={"action_scores": [0, 0, 0, 1, 0]},
    )

    loaded = load_rl_checkpoint(checkpoint_path, expected_role_family="pacman")

    assert loaded.runner_type == "static_scores"
    assert loaded.metadata["role_family"] == "pacman"


def test_save_versioned_checkpoint_and_latest_checkpoint(tmp_path) -> None:
    first = save_versioned_checkpoint(
        tmp_path,
        role_family="pacman",
        runner_type="static_scores",
        policy={"action_scores": [0, 0, 0, 1, 0]},
        label="baseline",
    )
    second = save_versioned_checkpoint(
        tmp_path,
        role_family="pacman",
        runner_type="static_scores",
        policy={"action_scores": [1, 0, 0, 0, 0]},
        label="baseline",
    )

    checkpoints = list_checkpoints(tmp_path, role_family="pacman")

    assert checkpoints == [first, second]
    assert latest_checkpoint(tmp_path, role_family="pacman") == second


def test_apply_retention_prunes_older_checkpoints(tmp_path) -> None:
    save_versioned_checkpoint(
        tmp_path,
        role_family="slime",
        runner_type="static_scores",
        policy={"action_scores": [1, 0, 0, 0, 0]},
        label="eval",
    )
    save_versioned_checkpoint(
        tmp_path,
        role_family="slime",
        runner_type="static_scores",
        policy={"action_scores": [0, 1, 0, 0, 0]},
        label="eval",
    )
    latest = save_versioned_checkpoint(
        tmp_path,
        role_family="slime",
        runner_type="static_scores",
        policy={"action_scores": [0, 0, 1, 0, 0]},
        label="eval",
    )

    deleted = apply_retention(tmp_path, role_family="slime", retention_limit=1)

    assert len(deleted) == 2
    assert list_checkpoints(tmp_path, role_family="slime") == [latest]

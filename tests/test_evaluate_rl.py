from __future__ import annotations

from src.core.domain import Role
from src.training.checkpoints import save_checkpoint
from src.training.evaluate_rl import evaluate_checkpoint


def test_evaluate_checkpoint_summarizes_pacman_policy_matches(tmp_path) -> None:
    checkpoint_path = save_checkpoint(
        tmp_path / "pacman_policy.json",
        role_family="pacman",
        runner_type="static_scores",
        policy={"action_scores": [0, 0, 0, 1, 0]},
    )

    summary = evaluate_checkpoint(
        checkpoint_path=checkpoint_path,
        controlled_role=Role.PACMAN,
        board_layout=(
            "#######",
            "#P...S#",
            "#  . H#",
            "#######",
        ),
        matches=2,
    )

    assert summary.controlled_role == Role.PACMAN
    assert summary.total_matches == 2
    assert summary.pacman_wins + summary.enemy_wins == 2
    assert summary.average_ticks > 0.0


def test_evaluate_checkpoint_summarizes_slime_policy_matches(tmp_path) -> None:
    checkpoint_path = save_checkpoint(
        tmp_path / "slime_policy.json",
        role_family="slime",
        runner_type="static_scores",
        policy={"action_scores": [1, 0, 0, 0, 0]},
    )

    summary = evaluate_checkpoint(
        checkpoint_path=checkpoint_path,
        controlled_role=Role.SLIME,
        board_layout=(
            "#######",
            "#P...S#",
            "#  . H#",
            "#######",
        ),
        matches=2,
    )

    assert summary.controlled_role == Role.SLIME
    assert summary.total_matches == 2
    assert summary.pacman_wins + summary.enemy_wins == 2
    assert summary.average_ticks > 0.0

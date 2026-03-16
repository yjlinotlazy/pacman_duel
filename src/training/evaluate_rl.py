"""Offline evaluation helpers for RL checkpoints against baseline agents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.app_controller import AgentConfig, AppController, MatchConfig
from src.core.domain import MatchStatus, Role


@dataclass(frozen=True, slots=True)
class EvaluationSummary:
    """Aggregate summary for one batch of offline evaluation matches."""

    controlled_role: Role
    checkpoint_path: Path
    total_matches: int
    pacman_wins: int
    enemy_wins: int
    average_ticks: float


def evaluate_checkpoint(
    *,
    checkpoint_path: str | Path,
    controlled_role: Role,
    board_layout: tuple[str, ...],
    board_id: str = "default",
    matches: int = 3,
) -> EvaluationSummary:
    """Run one checkpoint against baseline opponents and summarize the results."""
    if matches < 1:
        raise ValueError("matches must be at least 1")

    checkpoint = Path(checkpoint_path)
    pacman_wins = 0
    enemy_wins = 0
    total_ticks = 0

    for match_index in range(matches):
        controller = AppController()
        session = controller.create_session(
            _match_config_for_evaluation(
                checkpoint_path=checkpoint,
                controlled_role=controlled_role,
                board_layout=board_layout,
                board_id=board_id,
                match_index=match_index,
            )
        )
        final_state = session.run_until_finished()
        total_ticks += final_state.tick
        if final_state.status == MatchStatus.PACMAN_WIN:
            pacman_wins += 1
        elif final_state.status == MatchStatus.ENEMY_WIN:
            enemy_wins += 1

    return EvaluationSummary(
        controlled_role=controlled_role,
        checkpoint_path=checkpoint,
        total_matches=matches,
        pacman_wins=pacman_wins,
        enemy_wins=enemy_wins,
        average_ticks=total_ticks / matches,
    )


def _match_config_for_evaluation(
    *,
    checkpoint_path: Path,
    controlled_role: Role,
    board_layout: tuple[str, ...],
    board_id: str,
    match_index: int,
) -> MatchConfig:
    """Build one evaluation config for the requested controlled role."""
    if controlled_role == Role.PACMAN:
        return MatchConfig(
            board_id=board_id,
            board_layout=board_layout,
            pacman_config=AgentConfig("ai", "rl", {"checkpoint_path": str(checkpoint_path)}),
            slime_config=AgentConfig("ai", "shortest_path"),
            helper_config=AgentConfig("ai", "copycat"),
        )
    if controlled_role == Role.SLIME:
        return MatchConfig(
            board_id=board_id,
            board_layout=board_layout,
            pacman_config=AgentConfig("ai", "random", {"seed": match_index}),
            slime_config=AgentConfig("ai", "rl", {"checkpoint_path": str(checkpoint_path)}),
            helper_config=AgentConfig("ai", "shortest_path"),
        )
    raise ValueError(f"Unsupported controlled_role for evaluation: {controlled_role}")

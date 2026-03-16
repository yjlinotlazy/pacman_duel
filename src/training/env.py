"""Standalone environment wrapper for RL training experiments."""

from __future__ import annotations

from dataclasses import dataclass

from src.agents.rl.action_mapping import direction_from_action_index
from src.core.board import Board
from src.core.domain import MatchStatus, Role
from src.core.engine import GameEngine, build_initial_state
from src.training.observation import build_observation
from src.training.reward import compute_reward


@dataclass(frozen=True, slots=True)
class StepResult:
    """One environment step result."""

    observation: object
    reward: float
    terminated: bool
    info: dict[str, object]


class TrainingEnv:
    """Small training wrapper around the deterministic core engine."""

    def __init__(
        self,
        board_layout: tuple[str, ...],
        controlled_role: Role = Role.PACMAN,
        speed_scaling_factor: int | str = 1,
    ) -> None:
        """Build a fresh environment from one board layout."""
        board, spawns = Board.from_ascii(board_layout)
        self._controlled_role = controlled_role
        self._speed_scaling_factor = speed_scaling_factor
        self._board = board
        self._spawns = spawns
        self._engine = GameEngine(
            build_initial_state(board, spawns, speed_scaling_factor=speed_scaling_factor),
        )

    @property
    def state(self):
        """Expose the current game state for tests and diagnostics."""
        return self._engine.state

    def reset(self):
        """Reset the environment and return the first observation."""
        self._engine = GameEngine(
            build_initial_state(
                self._board,
                self._spawns,
                speed_scaling_factor=self._speed_scaling_factor,
            ),
        )
        return build_observation(self._engine.state, self._controlled_role)

    def step(self, action_index: int) -> StepResult:
        """Apply one controlled action while leaving the other roles stationary."""
        previous_state = self._engine.state
        next_state = self._engine.step(
            {
                self._controlled_role: direction_from_action_index(action_index),
            }
        )
        return StepResult(
            observation=build_observation(next_state, self._controlled_role),
            reward=compute_reward(previous_state, next_state, self._controlled_role),
            terminated=next_state.status != MatchStatus.RUNNING,
            info={"tick": next_state.tick, "status": next_state.status.value},
        )


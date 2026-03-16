"""Application-side session lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.agents.base import Agent
from src.agents.pacman.human import HumanAgent
from src.agents.pacman.random import RandomAgent as PacmanRandomAgent
from src.agents.pacman.rl import RLAgent as PacmanRLAgent
from src.agents.slime.copycat import CopycatAgent
from src.agents.slime.random import RandomAgent as SlimeRandomAgent
from src.agents.slime.rl import RLAgent as SlimeRLAgent
from src.agents.slime.shortest_path import ShortestPathAgent
from src.core.board import Board
from src.core.domain import MatchStatus, Role
from src.core.engine import GameEngine, build_initial_state
from src.game_session import GameSession
from src.stats.history_store import JsonlMatchHistoryStore, MatchResult
from src.stats.winrate import StatsQuery, WinRateSummary, query_summary


@dataclass(frozen=True)
class AgentConfig:
    """Runtime agent selection for one role."""

    controller_type: str
    algorithm: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MatchConfig:
    """Runtime match configuration used to construct one `GameSession`."""

    board_id: str
    board_layout: tuple[str, ...]
    pacman_config: AgentConfig
    slime_config: AgentConfig
    helper_config: AgentConfig
    speed_scaling_factor: int | str = 1


class AppController:
    """Create, reset, destroy, and replace match sessions for the app layer."""

    def __init__(self, history_store: JsonlMatchHistoryStore | None = None) -> None:
        """Start with no active session."""
        self._current_session: GameSession | None = None
        self._current_config: MatchConfig | None = None
        self._result_persisted = False
        self._history_store = history_store or JsonlMatchHistoryStore(Path("user_data") / "match_history.jsonl")

    @property
    def current_session(self) -> GameSession | None:
        """Return the currently active session, if one exists."""
        return self._current_session

    def create_session(self, config: MatchConfig) -> GameSession:
        """Build a fresh session from a match config and make it current."""
        board, spawns = Board.from_ascii(config.board_layout)
        initial_state = build_initial_state(
            board,
            spawns,
            speed_scaling_factor=config.speed_scaling_factor,
        )
        agents = {
            Role.PACMAN: self._build_pacman_agent(config.pacman_config),
            Role.SLIME: self._build_slime_agent(Role.SLIME, config.slime_config),
            Role.HELPER: self._build_slime_agent(Role.HELPER, config.helper_config),
        }
        agent_config = {
            Role.PACMAN: dict(config.pacman_config.params),
            Role.SLIME: dict(config.slime_config.params),
            Role.HELPER: dict(config.helper_config.params),
        }
        self._current_session = GameSession(
            engine=GameEngine(initial_state),
            agents=agents,
            agent_config=agent_config,
        )
        self._current_config = config
        self._result_persisted = False
        return self._current_session

    def reset_session(self) -> GameSession:
        """Reset the active session back to its initial state."""
        if self._current_session is None:
            raise RuntimeError("No active session to reset")
        self._current_session.reset()
        return self._current_session

    def destroy_session(self) -> None:
        """Drop the active session reference."""
        self._current_session = None
        self._result_persisted = False

    def switch_session(self, config: MatchConfig) -> GameSession:
        """Replace the current session with one built from a new config."""
        self.destroy_session()
        return self.create_session(config)

    def persist_current_result_if_needed(self) -> MatchResult | None:
        """Persist the current session result once when the match has completed."""
        if self._result_persisted or self._current_session is None or self._current_config is None:
            return None
        if self._current_session.state.status == MatchStatus.RUNNING:
            return None

        result = MatchResult(
            winner=self._current_session.state.status,
            tick_count=self._current_session.state.tick,
            pacman_controller=self._controller_name(self._current_config.pacman_config),
            slime_controller=self._controller_name(self._current_config.slime_config),
            helper_controller=self._controller_name(self._current_config.helper_config),
            parameter_snapshot={
                "pacman_params": dict(self._current_config.pacman_config.params),
                "slime_params": dict(self._current_config.slime_config.params),
                "helper_params": dict(self._current_config.helper_config.params),
                "speed_scaling_factor": self._current_config.speed_scaling_factor,
            },
            board_id=self._current_config.board_id,
        )
        self._history_store.record_result(result)
        self._result_persisted = True
        return result

    def get_summary_for_config(self, config: MatchConfig) -> WinRateSummary:
        """Return the historical win-rate summary for one match configuration."""
        return query_summary(
            self._history_store.load_results(),
            StatsQuery(
                pacman_controller=self._controller_name(config.pacman_config),
                slime_controller=self._controller_name(config.slime_config),
                helper_controller=self._controller_name(config.helper_config),
                board_id=config.board_id,
                parameter_snapshot={
                    "speed_scaling_factor": config.speed_scaling_factor,
                },
            ),
        )

    def _build_pacman_agent(self, config: AgentConfig) -> Agent:
        """Instantiate one Pacman-side agent from a UI-friendly controller config."""
        if config.controller_type == "human":
            return HumanAgent()
        if config.controller_type != "ai":
            raise ValueError(f"Unsupported controller_type: {config.controller_type}")

        algorithm = config.algorithm
        if algorithm == "random":
            return PacmanRandomAgent(seed=config.params.get("seed"))
        if algorithm == "rl":
            return PacmanRLAgent(checkpoint_path=self._checkpoint_path_from(config.params))
        raise ValueError(f"Unsupported Pacman algorithm: {algorithm}")

    def _build_slime_agent(self, role: Role, config: AgentConfig) -> Agent:
        """Instantiate one slime-side agent from a UI-friendly controller config."""
        if config.controller_type != "ai":
            raise ValueError(f"Unsupported controller_type for slime-side role: {config.controller_type}")

        algorithm = config.algorithm
        if algorithm == "random":
            return SlimeRandomAgent(role=role, seed=config.params.get("seed"))
        if algorithm == "shortest_path":
            return ShortestPathAgent(
                role=role,
                target_role=self._target_role_for(role, config.params),
            )
        if algorithm == "copycat":
            return CopycatAgent(
                role=role,
                target_role=self._target_role_for(role, config.params),
            )
        if algorithm == "rl":
            return SlimeRLAgent(
                role=role,
                checkpoint_path=self._checkpoint_path_from(config.params),
            )
        raise ValueError(f"Unsupported slime algorithm: {algorithm}")

    def _target_role_for(self, role: Role, params: dict[str, Any]) -> Role:
        """Resolve an optional target role parameter for pursuit-style agents."""
        raw_target = params.get("target_role")
        if raw_target is None:
            return Role.PACMAN if role != Role.PACMAN else Role.SLIME
        if isinstance(raw_target, Role):
            return raw_target
        try:
            return Role(raw_target)
        except ValueError as exc:
            raise ValueError(f"Unsupported target_role: {raw_target}") from exc

    def _controller_name(self, config: AgentConfig) -> str:
        """Render a short stable controller name for match history."""
        if config.controller_type == "human":
            return "human"
        return config.algorithm or config.controller_type

    def _checkpoint_path_from(self, params: dict[str, Any]) -> str:
        """Extract the required checkpoint path from one agent config."""
        checkpoint_path = params.get("checkpoint_path")
        if not isinstance(checkpoint_path, str) or not checkpoint_path:
            raise ValueError("RL agents require a non-empty checkpoint_path parameter")
        return checkpoint_path

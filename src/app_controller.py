"""Application-side session lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.agents.base import Agent
from src.agents.pacman.human import HumanAgent
from src.agents.pacman.random import RandomAgent as PacmanRandomAgent
from src.agents.slime.copycat import CopycatAgent
from src.agents.slime.random import RandomAgent as SlimeRandomAgent
from src.agents.slime.shortest_path import ShortestPathAgent
from src.core.board import Board
from src.core.domain import Role
from src.core.engine import GameEngine, build_initial_state
from src.game_session import GameSession


@dataclass(frozen=True)
class AgentConfig:
    """Runtime agent selection for one role."""

    controller_type: str
    algorithm: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MatchConfig:
    """Runtime match configuration used to construct one `GameSession`."""

    board_layout: tuple[str, ...]
    pacman_config: AgentConfig
    slime_config: AgentConfig
    helper_config: AgentConfig
    speed_scaling_factor: int | str = 1


class AppController:
    """Create, reset, destroy, and replace match sessions for the app layer."""

    def __init__(self) -> None:
        """Start with no active session."""
        self._current_session: GameSession | None = None

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

    def switch_session(self, config: MatchConfig) -> GameSession:
        """Replace the current session with one built from a new config."""
        self.destroy_session()
        return self.create_session(config)

    def _build_pacman_agent(self, config: AgentConfig) -> Agent:
        """Instantiate one Pacman-side agent from a UI-friendly controller config."""
        if config.controller_type == "human":
            return HumanAgent()
        if config.controller_type != "ai":
            raise ValueError(f"Unsupported controller_type: {config.controller_type}")

        algorithm = config.algorithm
        if algorithm == "random":
            return PacmanRandomAgent(seed=config.params.get("seed"))
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

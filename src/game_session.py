
"""Session orchestration for one match, independent from any UI layer."""

from __future__ import annotations

from dataclasses import dataclass

from src.agents.base import Agent
from src.core.engine import GameEngine
from src.core.domain import Direction, GameState, MatchStatus, Role


@dataclass
class GameSession:
    """Coordinates agents and engine state for a single playable match."""

    engine: GameEngine
    agents: dict[Role, Agent]
    agent_config: dict[Role, dict] | None = None

    def __post_init__(self) -> None:
        """Normalize optional per-agent config storage after construction."""
        self.agent_config = self.agent_config or {}

    @property
    def state(self) -> GameState:
        """Return the current match state from the engine."""
        return self.engine.state

    def reset(self) -> GameState:
        """Reset all agents and restore the engine to its initial state."""
        for agent in self.agents.values():
            agent.reset()
        return self.engine.reset()

    def collect_actions(self) -> dict[Role, Direction]:
        """Collect one action per role, defaulting missing agents to `STAY`."""
        actions: dict[Role, Direction] = {}
        for role in (Role.PACMAN, Role.SLIME, Role.HELPER):
            agent = self.agents.get(role)
            if agent is None:
                actions[role] = Direction.STAY
                continue
            actions[role] = agent.next_action(self.state, self.agent_config.get(role, {}))
        return actions

    def step(self) -> GameState:
        """Advance the match by one tick using the current agents."""
        return self.engine.step(self.collect_actions())

    def run_until_finished(self, max_ticks: int = 500) -> GameState:
        """Run the match until it ends or the tick limit is reached."""
        while self.state.status == MatchStatus.RUNNING and self.state.tick < max_ticks:
            self.step()
        return self.state

"""Pacman-side agent protocol."""

from __future__ import annotations

from typing import Protocol

from src.agents.base import Agent


class PacmanAgent(Agent, Protocol):
    """Marker protocol for agents whose objective is to play as Pacman."""

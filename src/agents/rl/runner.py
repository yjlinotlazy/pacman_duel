"""Inference runners loaded from RL checkpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.agents.rl.encoding import EncodedObservation


class PolicyRunner(Protocol):
    """Minimal runtime interface for checkpoint-backed action inference."""

    def action_scores(self, observation: EncodedObservation) -> tuple[float, ...]:
        """Return one score per action for the current observation."""
        ...


@dataclass(frozen=True, slots=True)
class StaticScoresRunner:
    """Always return the same preconfigured score vector."""

    scores: tuple[float, ...]

    def action_scores(self, observation: EncodedObservation) -> tuple[float, ...]:
        """Ignore the observation and return the configured scores."""
        del observation
        return self.scores


@dataclass(frozen=True, slots=True)
class LinearPolicyRunner:
    """Simple linear runner over a flat numeric observation vector."""

    weights: tuple[tuple[float, ...], ...]
    bias: tuple[float, ...]

    def action_scores(self, observation: EncodedObservation) -> tuple[float, ...]:
        """Compute one linear score per action from flat observation features."""
        features = observation.flat_features()
        return tuple(
            sum(weight * feature for weight, feature in zip(row, features, strict=True)) + bias
            for row, bias in zip(self.weights, self.bias, strict=True)
        )

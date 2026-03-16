"""Training-side observation helpers built on the shared runtime contract."""

from __future__ import annotations

from src.agents.rl.encoding import EncodedObservation, encode_observation
from src.core.domain import GameState, Role


def build_observation(state: GameState, role: Role) -> EncodedObservation:
    """Return the shared structured observation used by training and inference."""
    return encode_observation(state, role)


def observation_to_feature_vector(observation: EncodedObservation) -> tuple[float, ...]:
    """Convert one shared observation into the flat numeric training feature vector."""
    return observation.flat_features()


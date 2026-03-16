from __future__ import annotations

import json

import pytest

from src.agents.pacman.rl import RLAgent as PacmanRLAgent
from src.agents.rl.action_mapping import (
    ACTION_INDEX_TO_DIRECTION,
    ACTION_MAPPING_VERSION,
    best_direction_for_scores,
    direction_from_action_index,
)
from src.agents.rl.checkpoints import RLCheckpointError, load_rl_checkpoint
from src.agents.rl.encoding import OBSERVATION_VERSION, encode_observation
from src.agents.slime.rl import RLAgent as SlimeRLAgent
from src.app_controller import AgentConfig, AppController, MatchConfig
from src.core.domain import Direction, Role
from src.training.observation import observation_to_feature_vector
from tests.conftest import build_state


def _write_checkpoint(
    tmp_path,
    *,
    role_family: str,
    policy: dict[str, object],
    metadata_overrides: dict[str, object] | None = None,
):
    metadata = {
        "schema_version": 1,
        "role_family": role_family,
        "observation_version": OBSERVATION_VERSION,
        "action_mapping_version": ACTION_MAPPING_VERSION,
    }
    if metadata_overrides:
        metadata.update(metadata_overrides)
    checkpoint_path = tmp_path / f"{role_family}_policy.json"
    checkpoint_path.write_text(
        json.dumps(
            {
                "metadata": metadata,
                "policy": policy,
            }
        ),
        encoding="utf-8",
    )
    return checkpoint_path


def test_action_mapping_contract_is_stable() -> None:
    assert ACTION_INDEX_TO_DIRECTION == (
        Direction.UP,
        Direction.LEFT,
        Direction.DOWN,
        Direction.RIGHT,
        Direction.STAY,
    )
    assert direction_from_action_index(3) == Direction.RIGHT
    assert direction_from_action_index(99) == Direction.STAY


def test_best_direction_for_scores_returns_stay_for_malformed_scores() -> None:
    assert best_direction_for_scores([1, 2]) == Direction.STAY
    assert best_direction_for_scores([1, "bad", 3, 4, 5]) == Direction.STAY


def test_encode_observation_is_deterministic_and_role_aware() -> None:
    state = build_state(
        (
            "#####",
            "#P .#",
            "# HS#",
            "#####",
        )
    )

    pacman_observation = encode_observation(state, Role.PACMAN)
    repeated_observation = encode_observation(state, Role.PACMAN)
    slime_observation = encode_observation(state, Role.SLIME)

    assert pacman_observation == repeated_observation
    assert pacman_observation.version == OBSERVATION_VERSION
    assert pacman_observation.actor_position == (1, 1)
    assert slime_observation.actor_position == (3, 2)
    assert pacman_observation.walls
    assert pacman_observation.dots == ((3, 1),)
    assert pacman_observation.as_dict()["role"] == "pacman"
    assert len(observation_to_feature_vector(pacman_observation)) == 21


def test_load_rl_checkpoint_rejects_role_family_mismatch(tmp_path) -> None:
    checkpoint_path = _write_checkpoint(
        tmp_path,
        role_family="pacman",
        policy={"runner_type": "static_scores", "action_scores": [0, 0, 0, 1, 0]},
    )

    with pytest.raises(RLCheckpointError, match="role_family"):
        load_rl_checkpoint(checkpoint_path, expected_role_family="slime")


def test_pacman_rl_agent_uses_checkpoint_scores_to_choose_action(tmp_path) -> None:
    checkpoint_path = _write_checkpoint(
        tmp_path,
        role_family="pacman",
        policy={"runner_type": "static_scores", "action_scores": [0.1, 0.3, 0.2, 0.9, 0.0]},
    )
    state = build_state(
        (
            "#####",
            "#P S#",
            "# .H#",
            "#####",
        )
    )

    agent = PacmanRLAgent(checkpoint_path)

    assert agent.next_action(state, {}) == Direction.RIGHT
    assert agent.checkpoint.metadata["role_family"] == "pacman"


def test_slime_rl_agent_rejects_malformed_static_score_checkpoint(tmp_path) -> None:
    checkpoint_path = _write_checkpoint(
        tmp_path,
        role_family="slime",
        policy={"runner_type": "static_scores", "action_scores": [0, 1, "bad", 0, 0]},
    )

    with pytest.raises(RLCheckpointError, match="numeric values"):
        SlimeRLAgent(Role.SLIME, checkpoint_path)


def test_linear_runner_checkpoint_can_drive_policy_scores(tmp_path) -> None:
    state = build_state(
        (
            "#####",
            "#P S#",
            "# .H#",
            "#####",
        )
    )
    feature_count = len(observation_to_feature_vector(encode_observation(state, Role.PACMAN)))
    weights = [[0.0] * feature_count for _ in range(len(ACTION_INDEX_TO_DIRECTION))]
    weights[3][4] = 1.0
    checkpoint_path = _write_checkpoint(
        tmp_path,
        role_family="pacman",
        policy={
            "runner_type": "linear",
            "weights": weights,
            "bias": [0, 0, 0, 0, 0],
        },
    )

    agent = PacmanRLAgent(checkpoint_path)

    assert agent.next_action(state, {}) == Direction.RIGHT
    assert agent.checkpoint.runner_type == "linear"


def test_app_controller_builds_rl_agents_from_config(tmp_path) -> None:
    pacman_checkpoint = _write_checkpoint(
        tmp_path,
        role_family="pacman",
        policy={"runner_type": "static_scores", "action_scores": [0, 0, 0, 1, 0]},
    )
    slime_checkpoint = _write_checkpoint(
        tmp_path,
        role_family="slime",
        policy={"runner_type": "static_scores", "action_scores": [1, 0, 0, 0, 0]},
    )
    controller = AppController()

    session = controller.create_session(
        MatchConfig(
            board_id="default",
            board_layout=(
                "#######",
                "#P...S#",
                "#  . H#",
                "#######",
            ),
            pacman_config=AgentConfig("ai", "rl", {"checkpoint_path": str(pacman_checkpoint)}),
            slime_config=AgentConfig("ai", "rl", {"checkpoint_path": str(slime_checkpoint)}),
            helper_config=AgentConfig("ai", "random", {"seed": 5}),
        )
    )

    assert isinstance(session.agents[Role.PACMAN], PacmanRLAgent)
    assert isinstance(session.agents[Role.SLIME], SlimeRLAgent)


def test_app_controller_rejects_rl_agent_without_checkpoint_path() -> None:
    controller = AppController()

    with pytest.raises(ValueError, match="checkpoint_path"):
        controller.create_session(
            MatchConfig(
                board_id="default",
                board_layout=(
                    "#######",
                    "#P...S#",
                    "#  . H#",
                    "#######",
                ),
                pacman_config=AgentConfig("ai", "rl"),
                slime_config=AgentConfig("ai", "shortest_path"),
                helper_config=AgentConfig("ai", "copycat"),
            )
        )

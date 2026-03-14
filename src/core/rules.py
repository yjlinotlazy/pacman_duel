"""Pure rule helpers for legal movement, state updates, and win resolution."""

from __future__ import annotations

from dataclasses import replace

from .domain import Direction, EntityState, GameState, MatchStatus, MOVE_PRIORITY, Role


def legal_actions(state: GameState, role: Role) -> tuple[Direction, ...]:
    """Return all legal moves for one role, always including `STAY`."""
    entity = state.entity_for(role)
    legal: list[Direction] = [Direction.STAY]
    for direction in MOVE_PRIORITY:
        if state.board.is_walkable(entity.position.moved(direction)):
            legal.append(direction)
    return tuple(legal)


def sanitize_action(state: GameState, role: Role, action: Direction) -> Direction:
    """Map illegal requested actions to `STAY` before applying them."""
    return action if action in legal_actions(state, role) else Direction.STAY


def apply_action(state: GameState, role: Role, action: Direction) -> GameState:
    """Apply one role's action and return the updated immutable state."""
    safe_action = sanitize_action(state, role, action)
    entity = state.entity_for(role)
    updated = EntityState(role=role, position=entity.position.moved(safe_action))
    state = state.with_entity(role, updated)
    if role == Role.PACMAN:
        state = replace(state, pacman_history=state.pacman_history + (safe_action,))
    return state


def consume_dot(state: GameState) -> GameState:
    """Remove a dot when Pacman occupies its tile."""
    if state.pacman.position not in state.dots:
        return state
    return replace(state, dots=state.dots - {state.pacman.position})


def resolve_status(state: GameState) -> GameState:
    """Resolve win/loss conditions after movement and dot consumption."""
    pacman_captured = state.pacman.position in {
        state.slime.position,
        state.helper.position,
    }
    dots_cleared = not state.dots

    if dots_cleared:
        return replace(state, status=MatchStatus.PACMAN_WIN)
    if pacman_captured:
        return replace(state, status=MatchStatus.ENEMY_WIN)
    return state

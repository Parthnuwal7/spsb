"""
validate_move Tool

Google ADK-compatible tool for validating player moves in RPS.
Pure validation — does not mutate game state.
"""

from typing import Literal, TypedDict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState, Move


# Constants
VALID_MOVES: set[str] = {"rock", "paper", "scissors", "bomb"}
Player = Literal["user", "bot"]


class ValidateMoveOutput(TypedDict):
    """Structured output for validate_move tool."""
    is_valid: bool
    normalized_move: Optional[Move]
    reason: str


def validate_move(
    move: str,
    player: Player,
    game_state: GameState | dict,
) -> ValidateMoveOutput:
    """
    Validate a player's move against game rules.

    Args:
        move: The raw move string provided by the player.
        player: Either "user" or "bot".
        game_state: Current game state (GameState object or dict).

    Returns:
        ValidateMoveOutput with is_valid, normalized_move, and reason.
    """
    # Handle dict input (for JSON-deserialized state)
    if isinstance(game_state, dict):
        game_state = GameState.from_dict(game_state)

    # Normalize input
    normalized = move.strip().lower() if isinstance(move, str) else ""

    # Rule 1: Check if move is in the valid set
    if normalized not in VALID_MOVES:
        return ValidateMoveOutput(
            is_valid=False,
            normalized_move=None,
            reason=f"Invalid move '{move}'. Must be one of: rock, paper, scissors, bomb.",
        )

    # Rule 2: Check bomb usage
    if normalized == "bomb":
        if player == "user" and game_state.user_bomb_used:
            return ValidateMoveOutput(
                is_valid=False,
                normalized_move=None,
                reason="Bomb already used. You can only use bomb once per game.",
            )
        if player == "bot" and game_state.bot_bomb_used:
            return ValidateMoveOutput(
                is_valid=False,
                normalized_move=None,
                reason="Bot has already used bomb this game.",
            )

    # All checks passed
    return ValidateMoveOutput(
        is_valid=True,
        normalized_move=normalized,  # type: ignore
        reason="Valid move.",
    )


# ADK Tool Schema (for registration with Google ADK)
TOOL_SCHEMA = {
    "name": "validate_move",
    "description": "Validates a player's move in Rock-Paper-Scissors-Plus. Checks move validity and bomb usage rules.",
    "parameters": {
        "type": "object",
        "properties": {
            "move": {
                "type": "string",
                "description": "The move to validate (rock, paper, scissors, or bomb).",
            },
            "player": {
                "type": "string",
                "enum": ["user", "bot"],
                "description": "Which player is making the move.",
            },
            "game_state": {
                "type": "object",
                "description": "The current game state object.",
            },
        },
        "required": ["move", "player", "game_state"],
    },
}

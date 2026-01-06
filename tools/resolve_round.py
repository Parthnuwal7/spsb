"""
resolve_round Tool

Google ADK-compatible tool for determining round winner in RPS.
Pure deterministic logic — no randomness, no state mutation.
"""

from typing import Literal, TypedDict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState, Move, Player


class ResolveRoundOutput(TypedDict):
    """Structured output for resolve_round tool."""
    winner: Player
    explanation: str


# Win matrix: winner[attacker][defender] = True if attacker beats defender
WIN_MATRIX: dict[Move, set[Move]] = {
    "rock": {"scissors"},
    "paper": {"rock"},
    "scissors": {"paper"},
    "bomb": {"rock", "paper", "scissors"},  # bomb beats all except bomb
}


def resolve_round(
    user_move: Move,
    bot_move: Move,
    game_state: GameState | dict,
) -> ResolveRoundOutput:
    """
    Determine the winner of a round based on both players' moves.

    Args:
        user_move: Validated move from the user.
        bot_move: Validated move from the bot.
        game_state: Current game state (unused, but passed for consistency).

    Returns:
        ResolveRoundOutput with winner and explanation.
    """
    # Handle identical moves (draw)
    if user_move == bot_move:
        return ResolveRoundOutput(
            winner="draw",
            explanation=f"Both played {user_move}. It's a draw.",
        )

    # Check if user wins
    if bot_move in WIN_MATRIX.get(user_move, set()):
        # Special case: bomb beats everything
        if user_move == "bomb":
            return ResolveRoundOutput(
                winner="user",
                explanation=f"User's bomb destroys bot's {bot_move}.",
            )
        return ResolveRoundOutput(
            winner="user",
            explanation=f"User's {user_move} beats bot's {bot_move}.",
        )

    # Check if bot wins
    if user_move in WIN_MATRIX.get(bot_move, set()):
        if bot_move == "bomb":
            return ResolveRoundOutput(
                winner="bot",
                explanation=f"Bot's bomb destroys user's {user_move}.",
            )
        return ResolveRoundOutput(
            winner="bot",
            explanation=f"Bot's {bot_move} beats user's {user_move}.",
        )

    # Fallback (should never reach here with valid moves)
    return ResolveRoundOutput(
        winner="draw",
        explanation=f"Unexpected matchup: {user_move} vs {bot_move}.",
    )


# ADK Tool Schema
TOOL_SCHEMA = {
    "name": "resolve_round",
    "description": "Determines the winner of a Rock-Paper-Scissors-Plus round based on both players' validated moves.",
    "parameters": {
        "type": "object",
        "properties": {
            "user_move": {
                "type": "string",
                "enum": ["rock", "paper", "scissors", "bomb"],
                "description": "The user's validated move.",
            },
            "bot_move": {
                "type": "string",
                "enum": ["rock", "paper", "scissors", "bomb"],
                "description": "The bot's validated move.",
            },
            "game_state": {
                "type": "object",
                "description": "The current game state object.",
            },
        },
        "required": ["user_move", "bot_move", "game_state"],
    },
}

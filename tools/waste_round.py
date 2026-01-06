"""
waste_round Tool

Google ADK-compatible tool for handling invalid moves.
Wastes the round without bot play or score changes.
"""

from typing import TypedDict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState


class WasteRoundOutput(TypedDict):
    """Structured output for waste_round tool."""
    updated_game_state: dict
    rounds_remaining: int


def waste_round(game_state: GameState | dict) -> WasteRoundOutput:
    """
    Waste a round due to invalid user move.
    
    - No bot move is generated
    - No scores change
    - Round counter increments
    - Game ends after 3 rounds (tie if scores equal)
    
    Args:
        game_state: Current game state.
        
    Returns:
        WasteRoundOutput with updated state and rounds remaining.
    """
    # Convert dict to GameState if needed
    if isinstance(game_state, dict):
        state = GameState.from_dict(game_state)
    else:
        state = game_state

    # Check for game over (3 rounds reached)
    if state.current_round >= 3:
        state.game_over = True
        if state.user_score > state.bot_score:
            state.final_winner = "user"
        elif state.bot_score > state.user_score:
            state.final_winner = "bot"
        else:
            state.final_winner = "draw"
    else:
        # Increment round counter
        state.current_round += 1

    rounds_remaining = 3 - (state.current_round - 1) if not state.game_over else 0

    return WasteRoundOutput(
        updated_game_state=state.to_dict(),
        rounds_remaining=rounds_remaining,
    )


# ADK Tool Schema
TOOL_SCHEMA = {
    "name": "waste_round",
    "description": "Wastes a round due to invalid user move. No bot play, no score changes, just advances the round counter.",
    "parameters": {
        "type": "object",
        "properties": {
            "game_state": {
                "type": "object",
                "description": "The current game state object.",
            },
        },
        "required": ["game_state"],
    },
}

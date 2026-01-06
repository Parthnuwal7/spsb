"""
update_game_state Tool

Google ADK-compatible tool for mutating game state after a round.
This is the ONLY place where state mutation occurs.
"""

from typing import TypedDict
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState, Move, Player, RoundResult


class UpdateGameStateOutput(TypedDict):
    """Structured output for update_game_state tool."""
    updated_game_state: dict


def update_game_state(
    game_state: GameState | dict,
    user_move: Move,
    bot_move: Move,
    round_winner: Player,
) -> UpdateGameStateOutput:
    """
    Apply round results to game state.

    This is the ONLY tool that mutates game state.

    Args:
        game_state: Current game state.
        user_move: The user's validated move for this round.
        bot_move: The bot's validated move for this round.
        round_winner: Result from resolve_round ("user", "bot", or "draw").

    Returns:
        UpdateGameStateOutput containing the updated game state as dict.
    """
    # Convert dict to GameState if needed
    if isinstance(game_state, dict):
        state = GameState.from_dict(game_state)
    else:
        state = game_state

    # Record round in history
    round_result = RoundResult(
        round_number=state.current_round,
        user_move=user_move,
        bot_move=bot_move,
        winner=round_winner,
    )
    state.round_history.append(round_result)

    # Update scores based on winner
    if round_winner == "user":
        state.user_score += 1
    elif round_winner == "bot":
        state.bot_score += 1
    # draw: no score change

    # Mark bomb usage
    if user_move == "bomb":
        state.user_bomb_used = True
    if bot_move == "bomb":
        state.bot_bomb_used = True

    # Check for game over (best of 3 = first to 2 wins, or all 3 rounds played)
    if state.user_score >= 2:
        state.game_over = True
        state.final_winner = "user"
    elif state.bot_score >= 2:
        state.game_over = True
        state.final_winner = "bot"
    elif state.current_round >= 3:
        # All rounds played, determine winner by score
        state.game_over = True
        if state.user_score > state.bot_score:
            state.final_winner = "user"
        elif state.bot_score > state.user_score:
            state.final_winner = "bot"
        else:
            state.final_winner = "draw"

    # Increment round counter for next round (if game continues)
    if not state.game_over:
        state.current_round += 1

    return UpdateGameStateOutput(
        updated_game_state=state.to_dict(),
    )


# ADK Tool Schema
TOOL_SCHEMA = {
    "name": "update_game_state",
    "description": "Applies round results to the game state. Updates scores, tracks bomb usage, records history, and checks for game completion.",
    "parameters": {
        "type": "object",
        "properties": {
            "game_state": {
                "type": "object",
                "description": "The current game state object.",
            },
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
            "round_winner": {
                "type": "string",
                "enum": ["user", "bot", "draw"],
                "description": "The winner of this round.",
            },
        },
        "required": ["game_state", "user_move", "bot_move", "round_winner"],
    },
}

"""
Bot Move Selection Helper

Simple random selection for bot moves.
Not a tool — just a utility function.
"""

import random
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState, Move


# Base moves (always available)
BASE_MOVES: list[Move] = ["rock", "paper", "scissors"]

# All possible moves
ALL_MOVES: list[Move] = ["rock", "paper", "scissors", "bomb"]


def select_bot_move(
    game_state: GameState | dict,
    seed: Optional[int] = None,
) -> Move:
    """
    Select a random valid move for the bot.

    Args:
        game_state: Current game state.
        seed: Optional seed for deterministic behavior (testing).

    Returns:
        A valid Move for the bot.
    """
    # Handle dict input
    if isinstance(game_state, dict):
        state = GameState.from_dict(game_state)
    else:
        state = game_state

    # Build available moves list
    if state.bot_bomb_used:
        available_moves = BASE_MOVES
    else:
        available_moves = ALL_MOVES

    # Set seed if provided (for deterministic testing)
    if seed is not None:
        random.seed(seed)

    # Random selection
    return random.choice(available_moves)


def select_bot_move_deterministic(
    game_state: GameState | dict,
    round_number: Optional[int] = None,
) -> Move:
    """
    Deterministic fallback for bot move selection.
    
    Uses round number to cycle through moves predictably.
    Useful for testing or when randomness is undesirable.

    Args:
        game_state: Current game state.
        round_number: Override round number (defaults to state's current_round).

    Returns:
        A valid Move for the bot.
    """
    # Handle dict input
    if isinstance(game_state, dict):
        state = GameState.from_dict(game_state)
    else:
        state = game_state

    # Use provided round or state's round
    rnd = round_number if round_number is not None else state.current_round

    # Build available moves list
    if state.bot_bomb_used:
        available_moves = BASE_MOVES
    else:
        available_moves = ALL_MOVES

    # Deterministic selection based on round
    index = (rnd - 1) % len(available_moves)
    return available_moves[index]

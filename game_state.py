"""
Rock–Paper–Scissors–Plus Game State Model

A deterministic, serializable state model for a best-of-3 RPSB referee.
"""

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json


# Type aliases for clarity
Move = Literal["rock", "paper", "scissors", "bomb"]
Player = Literal["user", "bot", "draw"]


@dataclass
class RoundResult:
    """Record of a single round."""
    round_number: int
    user_move: Move
    bot_move: Move
    winner: Player  # "user", "bot", or "draw"


@dataclass
class GameState:
    """
    Complete game state for Rock–Paper–Scissors-bomb (Best of 3).
    
    All fields are mutable and the entire state is JSON-serializable.
    """
    
    # Current round (1-indexed, max 3)
    current_round: int = 1
    
    # Scores
    user_score: int = 0
    bot_score: int = 0
    
    # Bomb usage tracking (each player can use bomb once per game)
    user_bomb_used: bool = False
    bot_bomb_used: bool = False
    
    # Round history
    round_history: list[RoundResult] = field(default_factory=list)
    
    # Game completion flag
    game_over: bool = False
    final_winner: Optional[Player] = None

    def to_dict(self) -> dict:
        """Convert state to a JSON-serializable dictionary."""
        return {
            "current_round": self.current_round,
            "user_score": self.user_score,
            "bot_score": self.bot_score,
            "user_bomb_used": self.user_bomb_used,
            "bot_bomb_used": self.bot_bomb_used,
            "round_history": [
                {
                    "round_number": r.round_number,
                    "user_move": r.user_move,
                    "bot_move": r.bot_move,
                    "winner": r.winner,
                }
                for r in self.round_history
            ],
            "game_over": self.game_over,
            "final_winner": self.final_winner,
        }

    def to_json(self) -> str:
        """Serialize state to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "GameState":
        """Reconstruct GameState from a dictionary."""
        history = [
            RoundResult(
                round_number=r["round_number"],
                user_move=r["user_move"],
                bot_move=r["bot_move"],
                winner=r["winner"],
            )
            for r in data.get("round_history", [])
        ]
        return cls(
            current_round=data.get("current_round", 1),
            user_score=data.get("user_score", 0),
            bot_score=data.get("bot_score", 0),
            user_bomb_used=data.get("user_bomb_used", False),
            bot_bomb_used=data.get("bot_bomb_used", False),
            round_history=history,
            game_over=data.get("game_over", False),
            final_winner=data.get("final_winner"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "GameState":
        """Reconstruct GameState from a JSON string."""
        return cls.from_dict(json.loads(json_str))


def create_new_game() -> GameState:
    """Factory function to create a fresh game state."""
    return GameState()

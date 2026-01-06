"""
Rock–Paper–Scissors–Plus Google ADK Agent

Orchestrates the game by:
1. Interpreting user intent (dictionary-based, no LLM)
2. Invoking tools for all game logic
3. Generating responses from tool outputs

NO game logic in prompts. NO state in agent memory.
"""

import json

from game_state import GameState, create_new_game
from tools.validate_move import validate_move, TOOL_SCHEMA as VALIDATE_SCHEMA
from tools.resolve_round import resolve_round, TOOL_SCHEMA as RESOLVE_SCHEMA
from tools.update_game_state import update_game_state, TOOL_SCHEMA as UPDATE_SCHEMA
from helpers.bot_move import select_bot_move
from helpers.intent_parser import extract_move_offline, is_rules_request
from logger import get_logger, GameLogger, LogLevel


# =============================================================================
# ADK TOOL SCHEMAS (for registration with Google ADK)
# =============================================================================

ADK_TOOL_SCHEMAS = [
    VALIDATE_SCHEMA,
    RESOLVE_SCHEMA,
    UPDATE_SCHEMA,
]


# =============================================================================
# GAME CONSTANTS
# =============================================================================

RULES_TEXT = """🎮 **Rock-Paper-Scissors-Bomb** (Best of 3)

• Rock beats Scissors, Scissors beats Paper, Paper beats Rock
• 💣 Bomb beats everything (Only one-time use per player)
• Bomb vs Bomb = Draw
• Invalid moves waste your turn
• Type "quit" or "exit" to end the game

Ready? Type your move: rock, paper, scissors or bomb"""


# =============================================================================
# TOOL DISPATCHER (with logging)
# =============================================================================

def execute_tool(name: str, args: dict) -> dict:
    """Execute a tool by name with given arguments."""
    log = get_logger()
    
    # Log tool call
    log.tool_call(name, args)
    
    # Execute tool
    if name == "validate_move":
        result = validate_move(**args)
    elif name == "resolve_round":
        result = resolve_round(**args)
    elif name == "update_game_state":
        result = update_game_state(**args)
    else:
        result = {"error": f"Unknown tool: {name}"}
        log.error(f"Unknown tool: {name}")
    
    # Log result
    log.tool_result(name, result)
    
    return result


# =============================================================================
# GAME ORCHESTRATOR
# =============================================================================

class RPSPlusGame:
    """
    Stateless game orchestrator.
    
    State is passed in/out explicitly - never stored in the class.
    Uses dictionary-based intent parsing (no LLM required).
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the game orchestrator.
        
        Args:
            debug: If True, enable DEBUG level logging
        """
        self.log = get_logger()
        if debug:
            from logger import set_logger, GameLogger, LogLevel
            set_logger(GameLogger(enabled=True, min_level=LogLevel.DEBUG))
            self.log = get_logger()

    def start_game(self) -> tuple[dict, str]:
        """
        Initialize a new game.
        
        Returns:
            Tuple of (initial_state_dict, welcome_message)
        """
        self.log.info("Starting new game")
        state = create_new_game()
        self.log.debug("Initial state created", state.to_dict())
        return state.to_dict(), RULES_TEXT

    def extract_move(self, user_input: str) -> str:
        """
        Extract move intent from user input using dictionary matching.
        
        Returns:
            Extracted move string or "unknown"
        """
        # Check for rules request first
        if is_rules_request(user_input):
            self.log.intent_parsed(user_input, "none (rules request)")
            return "none"
        
        # Dictionary-based extraction
        move = extract_move_offline(user_input)
        self.log.intent_parsed(user_input, move)
        return move

    def play_round(
        self,
        game_state: dict,
        user_input: str,
    ) -> tuple[dict, str]:
        """
        Process one round of the game.
        
        Args:
            game_state: Current state dict (from persistence)
            user_input: Raw user input string
            
        Returns:
            Tuple of (updated_state_dict, response_message)
        """
        state = GameState.from_dict(game_state)
        
        # Log round start
        self.log.round_start(state.current_round)
        
        # Check if game already over
        if state.game_over:
            self.log.debug("Game already over, returning final state")
            return game_state, self._format_game_over(state)

        # Step 1: Extract move intent (dictionary-based)
        candidate_move = self.extract_move(user_input)
        
        # Handle non-move requests
        if candidate_move == "none":
            self.log.debug("Non-move request, returning rules")
            return game_state, RULES_TEXT
        
        # Step 2: Validate move (TOOL)
        validation = execute_tool("validate_move", {
            "move": candidate_move,
            "player": "user",
            "game_state": game_state,
        })
        
        # Step 3: Handle invalid move (wastes round)
        if not validation["is_valid"]:
            self.log.info(f"Invalid move: {validation['reason']}")
            bot_move = select_bot_move(state)
            result = execute_tool("update_game_state", {
                "game_state": game_state,
                "user_move": "rock",  # Default for invalid
                "bot_move": bot_move,
                "round_winner": "bot",  # Bot wins wasted rounds
            })
            new_state = result["updated_game_state"]
            self.log.round_end(state.current_round, "bot", "invalid", bot_move)
            self._check_game_over(new_state)
            return new_state, self._format_invalid_move(validation, bot_move, new_state)
        
        user_move = validation["normalized_move"]
        
        # Step 4: Generate bot move (HELPER)
        bot_move = select_bot_move(state)
        self.log.debug(f"Bot selected move: {bot_move}")
        
        # Step 5: Resolve round (TOOL)
        resolution = execute_tool("resolve_round", {
            "user_move": user_move,
            "bot_move": bot_move,
            "game_state": game_state,
        })
        
        # Step 6: Update state (TOOL - only mutation point)
        result = execute_tool("update_game_state", {
            "game_state": game_state,
            "user_move": user_move,
            "bot_move": bot_move,
            "round_winner": resolution["winner"],
        })
        
        new_state = result["updated_game_state"]
        
        # Log round end
        self.log.round_end(state.current_round, resolution["winner"], user_move, bot_move)
        self._check_game_over(new_state)
        
        # Step 7: Generate response from tool outputs
        return new_state, self._format_round_result(
            user_move, bot_move, resolution, new_state
        )

    def _check_game_over(self, state: dict) -> None:
        """Log game over if applicable."""
        if state.get("game_over"):
            winner = state.get("final_winner", "unknown")
            self.log.game_over(winner, (state["user_score"], state["bot_score"]))

    # =========================================================================
    # RESPONSE FORMATTERS (generate text from tool outputs only)
    # =========================================================================

    def _format_round_result(
        self,
        user_move: str,
        bot_move: str,
        resolution: dict,
        state: dict,
    ) -> str:
        """Format round result message from tool outputs."""
        lines = [
            f"**Round {len(state['round_history'])}**",
            f"You: {self._emoji(user_move)} {user_move.upper()}",
            f"Bot: {self._emoji(bot_move)} {bot_move.upper()}",
            f"→ {resolution['explanation']}",
            "",
            f"**Score:** You {state['user_score']} - {state['bot_score']} Bot",
        ]
        
        if state["game_over"]:
            lines.append("")
            lines.append(self._format_game_over(GameState.from_dict(state)))
        else:
            lines.append(f"\n*Round {state['current_round']} ready. Your move?*")
        
        return "\n".join(lines)

    def _format_invalid_move(
        self,
        validation: dict,
        bot_move: str,
        state: dict,
    ) -> str:
        """Format invalid move message."""
        lines = [
            f"❌ **Invalid Move!** {validation['reason']}",
            f"Bot played {self._emoji(bot_move)} {bot_move.upper()} and wins this round.",
            "",
            f"**Score:** You {state['user_score']} - {state['bot_score']} Bot",
        ]
        
        if state["game_over"]:
            lines.append("")
            lines.append(self._format_game_over(GameState.from_dict(state)))
        else:
            lines.append(f"\n*Round {state['current_round']} ready. Your move?*")
        
        return "\n".join(lines)

    def _format_game_over(self, state: GameState) -> str:
        """Format game over message."""
        if state.final_winner == "user":
            return "🎉 **YOU WON THE GAME!** 🎉"
        elif state.final_winner == "bot":
            return "🤖 Bot wins the game. Better luck next time!"
        else:
            return "🤝 **It's a tie!** Well played."

    def _emoji(self, move: str) -> str:
        """Get emoji for move."""
        return {"rock": "🪨", "paper": "📄", "scissors": "✂️", "bomb": "💣"}.get(move, "❓")


# STORAGE (in-memory)
# =============================================================================

class GameStateStore:
    """
    In-memory game state storage.
    
    State is lost on restart — suitable for single-session CLI usage.
    """
    
    def __init__(self):
        self._data: dict[str, dict] = {}
    
    def save(self, session_id: str, state: dict) -> None:
        """Save game state for a session."""
        self._data[session_id] = state
    
    def load(self, session_id: str) -> dict | None:
        """Load game state for a session."""
        return self._data.get(session_id)
    
    def delete(self, session_id: str) -> None:
        """Delete game state for a session."""
        self._data.pop(session_id, None)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def create_agent(debug: bool = False) -> tuple[RPSPlusGame, GameStateStore]:
    """
    Factory function to create the game agent and state store.
    
    Args:
        debug: If True, enable verbose DEBUG logging
    
    Returns:
        Tuple of (game_agent, state_store)
    """
    game = RPSPlusGame(debug=debug)
    store = GameStateStore()
    return game, store


# Example usage (not executed when imported)
if __name__ == "__main__":
    import sys
    
    # Check for debug flag
    debug_mode = "--debug" in sys.argv or "-d" in sys.argv
    
    if debug_mode:
        print("Running RPSB in DEBUG mode (verbose logging)")
    else:
        print("Welcome to Rock-Paper-Scissors-Bomb game!")
    print()
    
    game, store = create_agent(debug=debug_mode)
    session_id = "demo_session"
    
    # Start new game
    state, welcome = game.start_game()
    store.save(session_id, state)
    print(welcome)
    print()
    
    # Game loop
    while True:
        user_input = input("Your move: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        
        state = store.load(session_id)
        new_state, response = game.play_round(state, user_input)
        store.save(session_id, new_state)
        
        print()
        print(response)
        print()
        
        if new_state.get("game_over"):
            break
    
    store.delete(session_id)
    print("Thanks for playing!")
    
    # Show log history in debug mode
    if debug_mode:
        print("\n--- Log History ---")
        print(get_logger().get_history_json())


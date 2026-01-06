"""
Move Intent Parser

Dictionary-based fallback for extracting moves from user input.
No LLM required — pure string matching with synonyms.
"""

from game_state import Move


# Synonym dictionary: maps variations to canonical moves
MOVE_SYNONYMS: dict[str, Move] = {
    # Rock
    "rock": "rock",
    "stone": "rock",
    "boulder": "rock",
    "fist": "rock",
    "r": "rock",
    "🪨": "rock",
    
    # Paper
    "paper": "paper",
    "sheet": "paper",
    "page": "paper",
    "wrap": "paper",
    "p": "paper",
    "📄": "paper",
    "📃": "paper",
    
    # Scissors
    "scissors": "scissors",
    "scissor": "scissors",
    "cut": "scissors",
    "snip": "scissors",
    "s": "scissors",
    "✂️": "scissors",
    "✂": "scissors",
    
    # Bomb
    "bomb": "bomb",
    "boom": "bomb",
    "explode": "bomb",
    "blast": "bomb",
    "nuke": "bomb",
    "b": "bomb",
    "💣": "bomb",
    "🧨": "bomb",
}


def normalize_input(text: str) -> str:
    """
    Normalize user input for matching.
    
    - Lowercase
    - Strip whitespace
    - Remove common filler words
    """
    normalized = text.lower().strip()
    
    # Remove common prefixes/fillers
    fillers = [
        "i pick ", "i choose ", "i go with ", "i'll go with ",
        "my move is ", "let's go ", "going with ", "i say ",
        "i want ", "give me ", "let's do ", "i play ",
    ]
    
    for filler in fillers:
        if normalized.startswith(filler):
            normalized = normalized[len(filler):].strip()
            break
    
    # Remove trailing punctuation
    normalized = normalized.rstrip("!.,?")
    
    return normalized


def extract_move_offline(user_input: str) -> str:
    """
    Extract move from user input using dictionary matching.
    
    Args:
        user_input: Raw user input string.
        
    Returns:
        Canonical move ("rock", "paper", "scissors", "bomb") or "unknown".
    """
    normalized = normalize_input(user_input)
    
    # Direct match first
    if normalized in MOVE_SYNONYMS:
        return MOVE_SYNONYMS[normalized]
    
    # Check if any synonym is contained in the input
    # (handles cases like "I want rock please")
    for synonym, move in MOVE_SYNONYMS.items():
        if synonym in normalized:
            return move
    
    return "unknown"


def is_rules_request(user_input: str) -> bool:
    """Check if user is asking for rules/help."""
    normalized = normalize_input(user_input)
    keywords = ["rules", "help", "how", "what", "explain", "?"]
    return any(kw in normalized for kw in keywords)

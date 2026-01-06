# Rock-Paper-Scissors-Bomb (RPSB)

A deterministic, tool-based game system for a conversational Rock-Paper-Scissors variant with a one-time "bomb" move. Designed with Google ADK.

## Architecture

```
agent.py          ← Orchestrator (stateless)
    ↓
tools/            ← Game logic (ADK-compatible)
    validate_move.py
    resolve_round.py
    update_game_state.py
    ↓
helpers/          ← Utilities
    intent_parser.py   (dictionary-based move extraction)
    bot_move.py        (random move selection)
    ↓
game_state.py     ← Dataclass model
logger.py         ← Optional debug logging
```

## Game State Model

```python
@dataclass
class GameState:
    current_round: int        # 1-3
    user_score: int
    bot_score: int
    user_bomb_used: bool      # One-time use
    bot_bomb_used: bool
    round_history: list       # All moves + outcomes
    game_over: bool
    final_winner: str | None  # "user", "bot", or "draw"
```

State is **JSON-serializable** and passed in/out of every function. No state lives in memory.

## Tool Responsibilities

| Tool | Input | Output | Mutates State? |
|------|-------|--------|----------------|
| `validate_move` | move, player, state | `{is_valid, normalized_move, reason}` | No |
| `resolve_round` | user_move, bot_move, state | `{winner, explanation}` | No |
| `update_game_state` | state, moves, winner | `{updated_game_state}` | **Yes** (only source) |

All game rules live in tools. The LLM/agent never implements logic—only intent extraction and response formatting.

## Agent Flow

```
User Input → extract_move (dictionary) → validate_move (tool)
                                              ↓
                                         [invalid?] → bot wins round
                                              ↓
                                         select_bot_move (helper)
                                              ↓
                                         resolve_round (tool)
                                              ↓
                                         update_game_state (tool)
                                              ↓
                                         Format response → User
```

## Usage

```bash
# Normal mode
python agent.py

# Debug mode (verbose logging)
python agent.py --debug
```

## Tradeoffs

| Decision | Tradeoff |
|----------|----------|
| **Dictionary-based helper for intent parsing** | Fast, no API calls, but limited to predefined synonyms. May Misses creative esge cases and phrasings. |
| **All state external** | Fully deterministic and testable, but requires passing state dict on every call. |
| **Single mutation point** | Easy to audit state changes, but `update_game_state` is a larger function. |
| **Best-of-3 hardcoded** | Simpler implementation. Would need refactoring for configurable round counts. |
| **Bot uses random selection** | No strategy = fair for casual play, but predictable opponent behavior. |
| **--debug mode** | Seperate Verbose logging for debugging and a main mode for cleaner conversational flow. |
## File Summary

| File | Purpose |
|------|---------|
| `game_state.py`| State dataclass + serialization |
| `agent.py`| Orchestrator + persistence + CLI |
| `tools/*.py`| Validation, resolution, state mutation |
| `helpers/*.py`| Intent parsing, bot moves |
| `logger.py`| Structured debug logging |

---

**No LLM logic in game rules. No state in prompts. Fully auditable.**
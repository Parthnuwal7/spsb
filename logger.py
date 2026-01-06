"""
RPS Game Logger

Structured logging for debugging and transparency.
All tool calls, state changes, and game events are logged.
"""

import json
import sys
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, asdict


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


class LogCategory(Enum):
    TOOL_CALL = "TOOL"
    STATE = "STATE"
    INTENT = "INTENT"
    GAME = "GAME"
    ERROR = "ERROR"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    level: str
    category: str
    message: str
    data: Optional[dict] = None

    def to_dict(self) -> dict:
        result = {
            "timestamp": self.timestamp,
            "level": self.level,
            "category": self.category,
            "message": self.message,
        }
        if self.data:
            result["data"] = self.data
        return result


class GameLogger:
    """
    Configurable logger for game.
    
    Supports console output and log history for inspection.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        min_level: LogLevel = LogLevel.INFO,
        show_data: bool = True,
        use_colors: bool = True,
    ):
        self.enabled = enabled
        self.min_level = min_level
        self.show_data = show_data
        self.use_colors = use_colors
        self.history: list[LogEntry] = []
        
        # ANSI color codes
        self.colors = {
            LogLevel.DEBUG: "\033[90m",   # Gray
            LogLevel.INFO: "\033[36m",    # Cyan
            LogLevel.WARN: "\033[33m",    # Yellow
            LogLevel.ERROR: "\033[31m",   # Red
        }
        self.category_colors = {
            LogCategory.TOOL_CALL: "\033[35m",  # Magenta
            LogCategory.STATE: "\033[32m",      # Green
            LogCategory.INTENT: "\033[34m",     # Blue
            LogCategory.GAME: "\033[36m",       # Cyan
            LogCategory.ERROR: "\033[31m",      # Red
        }
        self.reset = "\033[0m"

    def _should_log(self, level: LogLevel) -> bool:
        """Check if this level should be logged."""
        levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR]
        return levels.index(level) >= levels.index(self.min_level)

    def _format_entry(self, entry: LogEntry) -> str:
        """Format log entry for console output."""
        level = LogLevel(entry.level)
        category = LogCategory(entry.category)
        
        if self.use_colors:
            level_color = self.colors.get(level, "")
            cat_color = self.category_colors.get(category, "")
            formatted = (
                f"{level_color}[{entry.level}]{self.reset} "
                f"{cat_color}[{entry.category}]{self.reset} "
                f"{entry.message}"
            )
        else:
            formatted = f"[{entry.level}] [{entry.category}] {entry.message}"
        
        if self.show_data and entry.data:
            data_str = json.dumps(entry.data, indent=2, default=str)
            formatted += f"\n  └─ {data_str}"
        
        return formatted

    def _log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        data: Optional[dict] = None,
    ) -> None:
        """Internal logging method."""
        if not self.enabled or not self._should_log(level):
            return
        
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level.value,
            category=category.value,
            message=message,
            data=data,
        )
        
        self.history.append(entry)
        print(self._format_entry(entry), file=sys.stderr)

    # =========================================================================
    # Public logging methods
    # =========================================================================

    def tool_call(self, tool_name: str, args: dict) -> None:
        """Log a tool invocation."""
        self._log(
            LogLevel.INFO,
            LogCategory.TOOL_CALL,
            f"Calling {tool_name}",
            {"args": args},
        )

    def tool_result(self, tool_name: str, result: dict) -> None:
        """Log a tool result."""
        self._log(
            LogLevel.DEBUG,
            LogCategory.TOOL_CALL,
            f"{tool_name} returned",
            {"result": result},
        )

    def state_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """Log a state mutation."""
        self._log(
            LogLevel.DEBUG,
            LogCategory.STATE,
            f"State.{field} changed",
            {"old": old_value, "new": new_value},
        )

    def intent_parsed(self, raw_input: str, extracted_move: str) -> None:
        """Log intent extraction."""
        self._log(
            LogLevel.INFO,
            LogCategory.INTENT,
            f"Parsed intent: '{raw_input}' → {extracted_move}",
        )

    def round_start(self, round_number: int) -> None:
        """Log round start."""
        self._log(
            LogLevel.INFO,
            LogCategory.GAME,
            f"Round {round_number} started",
        )

    def round_end(self, round_number: int, winner: str, user_move: str, bot_move: str) -> None:
        """Log round end."""
        self._log(
            LogLevel.INFO,
            LogCategory.GAME,
            f"Round {round_number} ended: {winner} wins",
            {"user_move": user_move, "bot_move": bot_move},
        )

    def game_over(self, winner: str, final_score: tuple[int, int]) -> None:
        """Log game completion."""
        self._log(
            LogLevel.INFO,
            LogCategory.GAME,
            f"Game over: {winner} wins ({final_score[0]}-{final_score[1]})",
        )

    def error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log an error."""
        data = {"error": str(error)} if error else None
        self._log(LogLevel.ERROR, LogCategory.ERROR, message, data)

    def debug(self, message: str, data: Optional[dict] = None) -> None:
        """Log debug info."""
        self._log(LogLevel.DEBUG, LogCategory.GAME, message, data)

    def info(self, message: str, data: Optional[dict] = None) -> None:
        """Log info."""
        self._log(LogLevel.INFO, LogCategory.GAME, message, data)

    # =========================================================================
    # History methods
    # =========================================================================

    def get_history(self) -> list[dict]:
        """Get full log history as list of dicts."""
        return [e.to_dict() for e in self.history]

    def get_history_json(self) -> str:
        """Get log history as JSON string."""
        return json.dumps(self.get_history(), indent=2)

    def clear_history(self) -> None:
        """Clear log history."""
        self.history.clear()


# Global logger instance (DISABLED by default - use set_logger to enable)
logger = GameLogger(enabled=False)


def get_logger() -> GameLogger:
    """Get the global logger instance."""
    return logger


def set_logger(new_logger: GameLogger) -> None:
    """Replace the global logger instance."""
    global logger
    logger = new_logger

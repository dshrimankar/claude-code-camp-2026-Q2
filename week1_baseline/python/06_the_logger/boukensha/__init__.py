"""
Boukensha: AI-driven MUD player agent framework.

This module provides the structural components, tool dispatch pattern,
multi-provider LLM integration, HTTP API client, and session logging
for building agent-based systems that interact with MUD servers.
"""

from boukensha.config import Config
from boukensha.context import Context
from boukensha.errors import UnknownToolError, UnsupportedModelError, ApiError, LoopError
from boukensha.message import Message
from boukensha.registry import Registry
from boukensha.tool import Tool
from boukensha.tasks.player import Player
from boukensha.prompt_builder import PromptBuilder
from boukensha.client import Client
from boukensha.agent import Agent
from boukensha.logger import Logger
from boukensha import backends

# Module-level state
_quiet = False
_debug = False
_config = None


def config() -> Config:
    """Get or create the global Config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def quiet() -> None:
    """Enable quiet mode (suppress output)."""
    global _quiet
    _quiet = True


def loud() -> None:
    """Disable quiet mode (enable output)."""
    global _quiet
    _quiet = False


def is_quiet() -> bool:
    """Check if quiet mode is enabled."""
    return _quiet


def debug() -> None:
    """Enable debug mode (verbose logging)."""
    global _debug
    _debug = True


def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return _debug


__all__ = [
    "Config",
    "Context",
    "Message",
    "Registry",
    "Tool",
    "UnknownToolError",
    "UnsupportedModelError",
    "ApiError",
    "LoopError",
    "Player",
    "PromptBuilder",
    "Client",
    "Agent",
    "Logger",
    "backends",
    "config",
    "quiet",
    "loud",
    "is_quiet",
    "debug",
    "is_debug",
]

__version__ = "0.6.0"

"""
Boukensha: AI-driven MUD player agent framework.

This module provides the structural components, tool dispatch pattern,
and multi-provider LLM integration for building agent-based systems
that interact with MUD servers.
"""

from boukensha.config import Config
from boukensha.context import Context
from boukensha.errors import UnknownToolError, UnsupportedModelError
from boukensha.message import Message
from boukensha.registry import Registry
from boukensha.tool import Tool
from boukensha.tasks.player import Player
from boukensha.prompt_builder import PromptBuilder
from boukensha import backends

__all__ = [
    "Config",
    "Context",
    "Message",
    "Registry",
    "Tool",
    "UnknownToolError",
    "UnsupportedModelError",
    "Player",
    "PromptBuilder",
    "backends",
]

__version__ = "0.3.0"

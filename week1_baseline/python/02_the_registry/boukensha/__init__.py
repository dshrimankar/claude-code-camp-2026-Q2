"""
Boukensha: AI-driven MUD player agent framework.

This module provides the structural components and tool dispatch
pattern for building agent-based systems that interact with MUD servers.
"""

from boukensha.config import Config
from boukensha.context import Context
from boukensha.errors import UnknownToolError
from boukensha.message import Message
from boukensha.registry import Registry
from boukensha.tool import Tool
from boukensha.tasks.player import Player

__all__ = [
    "Config",
    "Context",
    "Message",
    "Registry",
    "Tool",
    "UnknownToolError",
    "Player",
]

__version__ = "0.2.0"

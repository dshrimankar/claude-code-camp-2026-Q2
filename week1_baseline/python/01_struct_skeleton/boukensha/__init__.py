"""
Boukensha: AI-driven MUD player agent framework.

This module provides the structural components for building
agent-based systems that interact with MUD servers.
"""

from boukensha.config import Config
from boukensha.context import Context
from boukensha.message import Message
from boukensha.tool import Tool
from boukensha.tasks.player import Player

__all__ = [
    "Config",
    "Context",
    "Message",
    "Tool",
    "Player",
]

__version__ = "0.1.0"

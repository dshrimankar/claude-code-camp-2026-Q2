from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class Tool:
    """
    Represents an AI tool/function that can be called by the agent.

    A tool defines an action the agent can perform, including its name,
    description, parameter schema, and the executable code to run when invoked.

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description shown to the agent
        parameters: JSON schema defining the tool's parameters
        block: Executable function called when tool is invoked
    """

    name: str
    description: str
    parameters: Dict[str, Any]
    block: Callable[[Dict[str, Any]], Any]

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        # Truncate description for readability
        desc_preview = (
            self.description[:30] + "..."
            if len(self.description) > 30
            else self.description
        )
        param_keys = list(self.parameters.keys())
        return f"#<Tool name={self.name} description={desc_preview} params={param_keys}>"

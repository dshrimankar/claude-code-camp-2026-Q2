from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class Base(ABC):
    """
    Abstract base class for Boukensha tasks.

    All behavior is expressed as class methods that accept a settings hash.
    No instances are created. Concrete subclasses must define task_name().
    """

    @classmethod
    @abstractmethod
    def task_name(cls) -> str:
        """Return the task name (e.g., 'player'). Must be overridden by subclasses."""
        raise NotImplementedError(f"{cls} must define .task_name()")

    @classmethod
    def provider(cls, settings: Dict[str, Any]) -> str:
        """Get the provider name from settings (required)."""
        result = cls._fetch(settings, "provider")
        if not result:
            raise ValueError(f"tasks.{cls.task_name()}.provider is required in settings.yaml")
        return result

    @classmethod
    def model(cls, settings: Dict[str, Any]) -> str:
        """Get the model name from settings (required)."""
        result = cls._fetch(settings, "model")
        if not result:
            raise ValueError(f"tasks.{cls.task_name()}.model is required in settings.yaml")
        return result

    @classmethod
    def prompt_override(cls, settings: Dict[str, Any], prompt: str = "system") -> bool:
        """
        Check if a prompt override is enabled in settings.

        Returns True if settings has prompt_override.{prompt} = true.
        """
        node = cls._fetch(settings, "prompt_override")
        if not isinstance(node, dict):
            return False

        value = node.get(str(prompt))
        return value is True

    @classmethod
    def prompt(
        cls,
        settings: Dict[str, Any],
        name: str = "system",
        user_prompts_dir: Optional[str] = None,
        default_prompts_dir: Optional[str] = None,
    ) -> Optional[str]:
        """
        Resolve a prompt, checking user override first, then default.

        1. If prompt_override.{name} is true and user prompt exists, use it
        2. Otherwise use default prompt from default_prompts_dir
        """
        # Try user override first
        if cls.prompt_override(settings, name):
            user_text = cls._read_user_prompt(name, user_prompts_dir=user_prompts_dir)
            if user_text is not None:
                return user_text

        # Fall back to default
        return cls._read_default_prompt(name, default_prompts_dir=default_prompts_dir)

    @classmethod
    def system_prompt(
        cls,
        settings: Dict[str, Any],
        user_prompts_dir: Optional[str] = None,
        default_prompts_dir: Optional[str] = None,
    ) -> Optional[str]:
        """Convenience method to get the system prompt."""
        return cls.prompt(
            settings,
            name="system",
            user_prompts_dir=user_prompts_dir,
            default_prompts_dir=default_prompts_dir,
        )

    # ---------- private class methods -------------------------------------

    @classmethod
    def _fetch(cls, settings: Dict[str, Any], key: str) -> Any:
        """Fetch a key from settings dict (handles string keys)."""
        return settings.get(str(key))

    @classmethod
    def _read_user_prompt(
        cls, prompt_name: str, user_prompts_dir: Optional[str] = None
    ) -> Optional[str]:
        """Read a user prompt from user_prompts_dir/<task_name>/<prompt_name>.md"""
        if not user_prompts_dir:
            return None

        path = Path(user_prompts_dir) / cls.task_name() / f"{prompt_name}.md"
        return cls._read_file(path)

    @classmethod
    def _read_default_prompt(
        cls, prompt_name: str, default_prompts_dir: Optional[str] = None
    ) -> Optional[str]:
        """Read a default prompt from default_prompts_dir/<prompt_name>.md"""
        if not default_prompts_dir:
            return None

        path = Path(default_prompts_dir) / f"{prompt_name}.md"
        return cls._read_file(path)

    @classmethod
    def _read_file(cls, path: Path) -> Optional[str]:
        """Read a file if it exists, return None otherwise."""
        if path.exists():
            return path.read_text().strip()
        return None

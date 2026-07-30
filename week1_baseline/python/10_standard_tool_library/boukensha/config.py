from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from dotenv import load_dotenv


class Config:
    """
    Boukensha configuration loader.

    Loads settings from .boukensha/settings.yaml and environment variables
    from .boukensha/.env.
    """

    # The .boukensha config directory is resolved in this order:
    #   1. BOUKENSHA_DIR environment variable (set before loading .env)
    #   2. ~/.boukensha  (default)
    DEFAULT_DIR: str = str(Path.home() / ".boukensha")

    # Default prompts shipped alongside the library code
    PROMPTS_DIR: str = str(Path(__file__).parent.parent / "prompts")

    def __init__(self) -> None:
        self.dir: str = self._resolve_dir()
        self._load_env()
        self.settings: Dict[str, Any] = self._load_settings()

    # ---------- tasks -----------------------------------------------------

    def tasks(self, name: Optional[str] = None) -> Union[Dict[str, Any], Any]:
        """
        With no argument: returns the full tasks hash from settings.yaml.
        With a name: returns that task's settings hash, e.g. tasks("player").
        """
        all_tasks = self.dig("tasks") or {}
        if name is None:
            return all_tasks
        # Try both string and symbol-like access (convert name to string)
        return all_tasks.get(str(name))

    @property
    def user_prompts_dir(self) -> str:
        """The user's prompts directory for task prompt overrides."""
        return str(Path(self.dir) / "prompts")

    # ---------- MCP servers -----------------------------------------------

    def mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """Parse and normalize mcp_servers configuration.

        MCP servers define where the agent's tools come from — boukensha
        ships none of its own:

        mcp_servers:
          mud:
            command: mud-manager
            args:    [--mcp]
            prefix:  tbamud
            env:
              MUD_HOST: your.mud.host      # a stdio server's credentials
              MUD_NAME: Gandalf            # travel by environment

        Returns dict mapping server name to {command, args, env, prefix, required}
        with defaults applied. `required: false` lets a server fail to spawn
        without taking the agent down with it.
        """
        raw_servers = self.dig("mcp_servers") or {}
        result = {}

        for name, raw in raw_servers.items():
            entry = raw if isinstance(raw, dict) else {}

            # Helper to get value with string key fallback
            def get(key):
                return entry.get(str(key))

            req = get("required")

            result[str(name)] = {
                "command": str(get("command") or ""),
                "args": [str(arg) for arg in (get("args") or [])],
                "env": {str(k): str(v) for k, v in (get("env") or {}).items()},
                "prefix": str(get("prefix")) if get("prefix") is not None else None,
                "required": True if req is None else bool(req)
            }

        return result

    # ---------- MUD connection --------------------------------------------

    @property
    def mud_host(self) -> str:
        return self.dig("mud", "host") or "localhost"

    @property
    def mud_port(self) -> int:
        return self.dig("mud", "port") or 4000

    @property
    def mud_username(self) -> Optional[str]:
        return self.dig("mud", "username")

    @property
    def mud_password(self) -> Optional[str]:
        return self.dig("mud", "password")

    # ---------- low-level helpers -----------------------------------------

    def dig(self, *keys: str) -> Any:
        """
        Fetch a nested key path from settings, e.g. dig("mud", "host").

        Handles both string keys gracefully.
        """
        node = self.settings
        for key in keys:
            if isinstance(node, dict):
                # In Ruby, we handle both symbol and string keys
                # In Python, just use string keys
                node = node.get(str(key))
                if node is None:
                    return None
            else:
                return None
        return node

    def __str__(self) -> str:
        task_keys = ",".join(self.tasks().keys()) if isinstance(self.tasks(), dict) else ""
        return f"#<Boukensha::Config dir={self.dir} tasks={task_keys}>"

    def __repr__(self) -> str:
        return str(self)

    # ---------- private methods -------------------------------------------

    def _resolve_dir(self) -> str:
        """Resolve the config directory from env var or default."""
        raw = os.environ.get("BOUKENSHA_DIR") or self.DEFAULT_DIR
        return str(Path(raw).expanduser().resolve())

    def _load_env(self) -> None:
        """Load environment variables from .boukensha/.env if it exists."""
        env_file = Path(self.dir) / ".env"
        if env_file.exists():
            load_dotenv(str(env_file))

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from .boukensha/settings.yaml if it exists."""
        settings_file = Path(self.dir) / "settings.yaml"
        if settings_file.exists():
            with open(settings_file, "r") as f:
                loaded = yaml.safe_load(f)
                return loaded if loaded is not None else {}
        return {}

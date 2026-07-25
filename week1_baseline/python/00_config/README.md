# Boukensha Configuration System - Python Port

This is a Python port of the Boukensha configuration system from Ruby, providing configuration management for AI-driven MUD player agents.

## Overview

The Boukensha configuration system loads settings from `.boukensha/settings.yaml` and environment variables from `.boukensha/.env`, providing a clean interface for managing:

- Task configurations (provider, model, prompt overrides)
- MUD connection settings (host, port, username, password)
- System prompt resolution (with user override support)

## Requirements

- Python 3.8+
- PyYAML
- python-dotenv

## Installation

```bash
pip install -r requirements.txt
```

If you're on macOS with a system-managed Python environment, you may need:

```bash
python3 -m pip install --break-system-packages PyYAML python-dotenv
```

## Directory Structure

```
week1_baseline/python/00_config/
  boukensha/
    __init__.py           # Main module exports
    config.py             # Config class for loading settings
    tasks/
      __init__.py         # Tasks module exports
      base.py             # Abstract base class for tasks
      player.py           # Concrete player task implementation
  prompts/
    system.md             # Default system prompt
  examples/
    example.py            # Smoke test demonstrating usage
  requirements.txt        # Python dependencies
  README.md              # This file
```

## Usage

### Basic Configuration Loading

```python
from boukensha import Config
from boukensha.tasks import Player

# Load configuration from ~/.boukensha/
config = Config()

# Access task settings
player_settings = config.tasks("player")
print(f"Provider: {Player.provider(player_settings)}")
print(f"Model: {Player.model(player_settings)}")

# Access MUD connection settings
print(f"MUD Server: {config.mud_host}:{config.mud_port}")
print(f"Username: {config.mud_username}")

# Get system prompt
system_prompt = Player.system_prompt(
    player_settings,
    user_prompts_dir=config.user_prompts_dir,
    default_prompts_dir=Config.PROMPTS_DIR
)
```

### Running the Example

```bash
cd week1_baseline/python/00_config
python3 examples/example.py
```

Expected output:
```
=== Boukensha Step 0: Configuration ===

Config dir:     /Users/you/.boukensha
Tasks:          player

-- player task --
Provider:       anthropic
Model:          claude-haiku-4-5
Prompt override?False
System prompt:  You are a modified MUD player assistant. Use the tools avail...

MUD host:       localhost:4000
MUD user:       dummy

API key set?    True

#<Boukensha::Config dir=/Users/you/.boukensha tasks=player>
```

## Configuration Directory

The `.boukensha/` directory is resolved in this order:

1. `BOUKENSHA_DIR` environment variable (if set)
2. `~/.boukensha` (default location)

### Expected Structure

```
~/.boukensha/
  .env                 # Stores credentials (e.g., API keys) - never commit
  settings.yaml        # All non-secret settings
  prompts/
    player/
      system.md        # Optional per-task system prompt override
```

### Example `settings.yaml`

```yaml
tasks:
  player:
    provider: anthropic
    model: claude-haiku-4-5
    prompt_override:
      system: false      # Set to true to use ~/.boukensha/prompts/player/system.md

mud:
  host: localhost
  port: 4000
  username: dummy
  password: helloworld
```

### Example `.env`

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

## API Reference

### `Config` Class

**Properties:**
- `dir: str` - Resolved configuration directory path
- `settings: Dict[str, Any]` - Loaded settings from settings.yaml
- `user_prompts_dir: str` - Path to user's prompts directory
- `mud_host: str` - MUD server hostname (default: "localhost")
- `mud_port: int` - MUD server port (default: 4000)
- `mud_username: Optional[str]` - MUD username
- `mud_password: Optional[str]` - MUD password

**Methods:**
- `tasks(name: Optional[str] = None)` - Get all tasks or a specific task's settings
- `dig(*keys: str)` - Navigate nested settings dictionary

**Class Attributes:**
- `DEFAULT_DIR: str` - Default config directory (`~/.boukensha`)
- `PROMPTS_DIR: str` - Path to default prompts shipped with library

### `Base` Task Class (Abstract)

**Class Methods:**
- `task_name() -> str` - Must be overridden by subclasses
- `provider(settings) -> str` - Get provider name (required)
- `model(settings) -> str` - Get model name (required)
- `prompt_override(settings, prompt="system") -> bool` - Check if prompt override is enabled
- `prompt(settings, name="system", ...) -> Optional[str]` - Resolve prompt with override logic
- `system_prompt(settings, ...) -> Optional[str]` - Get system prompt

### `Player` Task Class

Concrete implementation of `Base` for the player agent.

**Class Methods:**
- `task_name() -> str` - Returns `"player"`

## Differences from Ruby Version

### Implemented Differences

1. **Type Hints:** Full type annotations using `typing` module (Python 3.8 compatible)
2. **Properties:** MUD connection getters use `@property` decorator instead of instance methods
3. **Path Handling:** Uses `pathlib.Path` instead of `File` module
4. **Import System:** Python's module system vs Ruby's `require_relative`
5. **Abstract Base:** Uses `abc.ABC` and `@abstractmethod` for enforcement

### Behavioral Equivalence

- ✅ Configuration directory resolution (env var → default)
- ✅ YAML settings loading
- ✅ Environment variable loading via .env
- ✅ Task settings access with nested keys
- ✅ Prompt override logic (user dir → default dir)
- ✅ MUD connection configuration
- ✅ String representation matching Ruby output

## Development

### Running Tests

Currently the port includes a smoke test example. To verify functionality:

```bash
python3 examples/example.py
```

### Type Checking (Optional)

```bash
pip install mypy
mypy boukensha/
```

## Python 3.8 Compatibility

The code is compatible with Python 3.8+ and uses:

- `from __future__ import annotations` for forward references
- `typing.Dict`, `typing.Optional`, `typing.Any` (not `dict`, `None | T`)
- `typing.Union[X, Y]` (not `X | Y`)
- Standard library only (pathlib, os, abc)

Avoids Python 3.9+ features like `dict | dict` merge operator or `str.removeprefix()`.

## License

Same as the Ruby version.

## See Also

- Original Ruby implementation: `week1_baseline/ruby/00_config/`
- Port plan: `docs/plans/python_port/00_config`

# Python Port Plan: Boukensha Global Executable

## Overview
This plan outlines the port of the Boukensha global executable from Ruby to Python. Step 09 introduces a system-wide `boukensha` command that can be installed via a package manager (gem for Ruby, pip for Python) and run from anywhere on the system.

**Key Innovation:** The loader pattern allows users to:
1. **Choose which step's implementation to run** (`BOUKENSHA_PATH` or `boukensha_path` in `~/.boukensharc`)
2. **Choose which config directory to use** (`BOUKENSHA_DIR` or `boukensha_dir` in `~/.boukensharc`)

This enables testing different step implementations or switching between projects without reinstalling the package.

## Scope
Port **Boukensha Global Executable**:
- **Source:** `week1_baseline/ruby/09_global_executable/`
- **Target:** `week1_baseline/python/09_global_executable/`

**Key Changes from Step 08:**
- NEW: `boukensha_loader.rb` → `boukensha/loader.py` (96 lines) - Resolution logic
- NEW: `bin/boukensha` → entry point via `setup.py` or `pyproject.toml` (console script)
- NEW: `boukensha.gemspec` → `setup.py` or `pyproject.toml` (package configuration)
- NEW: `lib/boukensha/version.rb` → VERSION constant in `__init__.py`
- MODIFIED: `lib/boukensha/config.rb` → `boukensha/config.py` (simplify resolve_dir)
- UNCHANGED: All other files (copy from 08_the_repl_loop)

## Target Directory Structure

```
week1_baseline/
  ruby/09_global_executable/     # Ruby (keep as reference)
  python/
    09_global_executable/        # NEW: Python port
      boukensha/
        __init__.py              # MODIFIED: VERSION = "0.9.0"
        loader.py                # NEW: Loader class
        config.py                # MODIFIED: simplified resolve_dir()
        repl.py                  # COPY from 08
        agent.py                 # COPY from 08
        client.py                # COPY from 08
        context.py               # COPY from 08
        errors.py                # COPY from 08
        logger.py                # COPY from 08
        message.py               # COPY from 08
        prompt_builder.py        # COPY from 08
        registry.py              # COPY from 08
        run_dsl.py               # COPY from 08
        tool.py                  # COPY from 08
        backends/                # COPY all from 08
        tasks/                   # COPY all from 08
      prompts/
        system.md                # COPY from 08
      examples/                  # Optional (not needed for global executable)
      setup.py                   # NEW: Package configuration (OR pyproject.toml)
      pyproject.toml             # NEW: Modern package config (alternative)
      MANIFEST.in                # Optional: Include non-Python files
      README.md                  # Documentation
      requirements.txt           # COPY from 08
```

---

## File-by-File Mapping

| Ruby File | Python File | Lines | Complexity | Status | Notes |
|-----------|-------------|-------|------------|--------|-------|
| `lib/boukensha_loader.rb` | `boukensha/loader.py` | 96 | Medium | **NEW** | Resolution + loading logic |
| `bin/boukensha` | `setup.py` entry_points | 8→15 | Simple | **NEW** | Console script definition |
| `boukensha.gemspec` | `setup.py` or `pyproject.toml` | 24→30 | Simple | **NEW** | Package metadata |
| `lib/boukensha/version.rb` | `__init__.py` VERSION | 3→1 | Trivial | **NEW** | Version constant |
| `lib/boukensha/config.rb` | `boukensha/config.py` | -8 | Simple | **MODIFIED** | Simplify resolve_dir() |
| All other lib files | All other files | ~1600 | - | COPY | From 08_the_repl_loop |

**Total New Lines to Port:** ~132 lines
- `loader.py`: ~96 lines (NEW)
- `setup.py` or `pyproject.toml`: ~30 lines (NEW)
- `config.py`: -8 lines (MODIFIED - simplified)
- `__init__.py`: +1 line (VERSION constant)

**Key Translation Challenges:**
- Ruby gemspec → Python setup.py/pyproject.toml
- Ruby `bin/` executable → Python console_scripts entry point
- Ruby `$LOAD_PATH.unshift` → Python package installation handles this
- Ruby `require` → Python `import` with dynamic path
- YAML parsing for `~/.boukensharc` (same patterns)
- Module detection: `respond_to?(:repl)` → `hasattr(module, 'repl')`

---

## Dependencies

**External (same as step 08):**
- `python-dotenv` - .env file loading
- `requests` - HTTP client for API calls
- `PyYAML` - YAML parsing (for settings.yaml and ~/.boukensharc)

**Stdlib:**
- `pathlib` - Path manipulation
- `sys` - sys.path manipulation, exit codes
- `os` - Environment variables
- `importlib` - Dynamic module loading
- All other stdlib from step 08

**Build Tools:**
- `setuptools` - For setup.py approach
- `wheel` - For building wheels
- `build` - For pyproject.toml approach (modern)

---

## Key Translation Patterns

### 1. Ruby Gemspec → Python Setup.py

Ruby gemspec defines how to build and install a gem:

```ruby
# boukensha.gemspec
require_relative "lib/boukensha/version"

Gem::Specification.new do |spec|
  spec.name        = "boukensha"
  spec.version     = Boukensha::VERSION
  spec.summary     = "BOUKENSHA — a tiny teaching framework"
  spec.authors     = ["Andrew Brown"]
  spec.license     = "MIT"

  spec.required_ruby_version = ">= 3.0"
  spec.files = Dir["lib/**/*.rb"] + ["bin/boukensha"]

  spec.bindir      = "bin"
  spec.executables = ["boukensha"]  # Creates global command
end
```

Python setup.py equivalent:

```python
# setup.py
from setuptools import setup, find_packages
from pathlib import Path

# Read version from __init__.py
init_file = Path(__file__).parent / "boukensha" / "__init__.py"
for line in init_file.read_text().splitlines():
    if line.startswith("__version__"):
        version = line.split("=")[1].strip().strip('"\'')
        break

setup(
    name="boukensha",
    version=version,
    description="BOUKENSHA — a tiny teaching framework for coding harnesses",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Andrew Brown",
    author_email="andrew@exampro.co",
    license="MIT",
    python_requires=">=3.8",
    packages=find_packages(),
    include_package_data=True,  # Include non-Python files via MANIFEST.in
    install_requires=[
        "python-dotenv",
        "PyYAML",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "boukensha=boukensha.loader:main",  # Creates global command
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
)
```

### 2. Ruby Gemspec → Python pyproject.toml (Modern Approach)

Python's modern packaging uses `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "boukensha"
version = "0.9.0"
description = "BOUKENSHA — a tiny teaching framework for coding harnesses"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Andrew Brown", email = "andrew@exampro.co"}
]
keywords = ["mud", "agent", "llm", "teaching"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
]
dependencies = [
    "python-dotenv",
    "PyYAML",
    "requests",
]

[project.scripts]
boukensha = "boukensha.loader:main"  # Creates global command

[tool.setuptools]
packages = ["boukensha", "boukensha.backends", "boukensha.tasks"]
include-package-data = true
```

**Recommendation:** Use `pyproject.toml` (modern, cleaner) over `setup.py`.

### 3. Ruby bin/boukensha → Python Console Script Entry Point

Ruby uses a shebang script in `bin/`:

```ruby
#!/usr/bin/env ruby
# frozen_string_literal: true

$LOAD_PATH.unshift File.expand_path("../lib", __dir__)

require "boukensha_loader"

BoukenshaLoader.load_and_start_repl
```

Python doesn't need this file. Instead, the entry point is defined in the package config, and `pip install` creates the executable script automatically:

```python
# In setup.py or pyproject.toml
entry_points = {
    "console_scripts": [
        "boukensha=boukensha.loader:main",
    ],
}
```

Then in `boukensha/loader.py`, define the `main()` function:

```python
def main():
    """Entry point for the boukensha global command."""
    Loader.load_and_start_repl()

if __name__ == "__main__":
    main()
```

After `pip install`, users can run `boukensha` from anywhere.

### 4. Loader Resolution Logic - Bundled Path

Ruby gets the bundled lib path relative to the loader file:

```ruby
# Ruby
BUNDLED_LIB = File.expand_path("../boukensha.rb", __FILE__)
```

Python equivalent:

```python
# Python
from pathlib import Path

# Get the directory containing this loader.py file
LOADER_DIR = Path(__file__).parent

# Bundled lib is the __init__.py in the same package
BUNDLED_MODULE = "boukensha"  # Import name, not file path
```

### 5. RC File Loading - Backward Compatible YAML

Both Ruby and Python handle the same `~/.boukensharc` formats:

```ruby
# Ruby
def self.load_rc
  return {} unless File.exist?(rc_file)

  parsed = YAML.safe_load(File.read(rc_file), permitted_classes: [], aliases: false)

  case parsed
  when Hash
    parsed
  when String
    # Backward compatibility with single-path format
    { "boukensha_path" => parsed }
  when nil
    {}
  else
    abort "boukensha: #{rc_file} must contain a YAML mapping"
  end
rescue Psych::SyntaxError => e
  abort "boukensha: invalid YAML in #{rc_file}: #{e.message}"
end
```

```python
# Python
import yaml
from pathlib import Path

def load_rc() -> dict:
    rc_file = Path.home() / ".boukensharc"
    if not rc_file.exists():
        return {}

    try:
        with open(rc_file) as f:
            parsed = yaml.safe_load(f)

        if isinstance(parsed, dict):
            return parsed
        elif isinstance(parsed, str):
            # Backward compatibility with single-path format
            return {"boukensha_path": parsed}
        elif parsed is None:
            return {}
        else:
            sys.exit(f"boukensha: {rc_file} must contain a YAML mapping")

    except yaml.YAMLError as e:
        sys.exit(f"boukensha: invalid YAML in {rc_file}: {e}")
```

### 6. Path Expansion

```ruby
# Ruby
def self.expand_rc_path(path)
  return nil unless path.is_a?(String)
  return nil if path.strip.empty?

  File.expand_path(path, File.dirname(rc_file))
end
```

```python
# Python
from pathlib import Path

def expand_rc_path(path: str) -> Optional[Path]:
    """Expand a path from ~/.boukensharc relative to home directory."""
    if not path or not isinstance(path, str) or not path.strip():
        return None

    rc_file = Path.home() / ".boukensharc"
    return (rc_file.parent / path).expanduser().resolve()
```

### 7. Dynamic Module Loading

Ruby uses `require` with the resolved path:

```ruby
# Ruby
main = resolve  # Returns path like "/path/to/step/lib/boukensha.rb"
require main

unless Boukensha.respond_to?(:repl)
  abort "error: step does not support REPL"
end

Boukensha.repl
```

Python uses `importlib` for dynamic imports:

```python
# Python
import sys
import importlib.util

def load_and_start_repl():
    module_path = resolve()  # Returns path like "/path/to/step/boukensha/__init__.py"
    step_dir = module_path.parent.parent  # Go up from boukensha/__init__.py to step dir

    print(f"[boukensha] loading from: {step_dir}", file=sys.stderr)

    # Add the parent directory to sys.path so we can import 'boukensha'
    parent_dir = str(step_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Import the boukensha module
    try:
        import boukensha
    except ImportError as e:
        sys.exit(f"boukensha: failed to import from {step_dir}: {e}")

    # Check if it has repl() method
    if not hasattr(boukensha, 'repl'):
        sys.exit(
            f"boukensha: the step at {step_dir}\n"
            f"       does not support the interactive REPL (added in step 7).\n"
            f"       Run its examples directly, e.g.:\n"
            f"         python {step_dir}/examples/*.py\n"
            f"       Or point BOUKENSHA_PATH at step 7 or later."
        )

    # Start the REPL
    boukensha.repl()
```

### 8. Environment Variable Setup Before Import

Both Ruby and Python set `BOUKENSHA_DIR` before loading:

```ruby
# Ruby
rc_config_dir = expand_rc_path(rc["boukensha_dir"])
ENV["BOUKENSHA_DIR"] = rc_config_dir if !ENV["BOUKENSHA_DIR"] && rc_config_dir

require main  # This will read ENV["BOUKENSHA_DIR"] when Config initializes
```

```python
# Python
import os

rc_config_dir = expand_rc_path(rc.get("boukensha_dir"))
if not os.environ.get("BOUKENSHA_DIR") and rc_config_dir:
    os.environ["BOUKENSHA_DIR"] = str(rc_config_dir)

# Then import boukensha - Config.__init__ will read ENV["BOUKENSHA_DIR"]
import boukensha
```

### 9. Config Resolution Simplification

Step 09 simplifies config resolution by removing the current directory check:

**Step 08 (08_the_repl_loop):**
```python
def _resolve_dir(self) -> str:
    # 1. Explicit override
    if os.environ.get("BOUKENSHA_DIR"):
        return str(Path(os.environ["BOUKENSHA_DIR"]).expanduser().resolve())

    # 2. .boukensha in current working directory
    cwd_dir = Path.cwd() / ".boukensha"
    if cwd_dir.is_dir():
        return str(cwd_dir)

    # 3. ~/.boukensha default
    return str(Path(self.DEFAULT_DIR).expanduser().resolve())
```

**Step 09 (09_global_executable):**
```python
def _resolve_dir(self) -> str:
    """Resolve config directory (simplified for global executable)."""
    raw = os.environ.get("BOUKENSHA_DIR") or self.DEFAULT_DIR
    return str(Path(raw).expanduser().resolve())
```

---

## Implementation Phases

### Phase 1: Copy from 08_the_repl_loop

**Priority:** HIGH
**Estimated Time:** 15 minutes

Copy the entire directory as the base:

```bash
cp -r week1_baseline/python/08_the_repl_loop week1_baseline/python/09_global_executable
```

**Validation:**
- Directory structure matches 08_the_repl_loop
- All files present

---

### Phase 2: Simplify Config Resolution

**Priority:** HIGH
**Estimated Time:** 15 minutes

**File:** `boukensha/config.py` (MODIFIED)

**Steps:**
1. Read existing `config.py`
2. Find `_resolve_dir()` method
3. Replace with simplified version (only checks `BOUKENSHA_DIR` env var or default)
4. Remove current working directory check

**Python Changes:**
```python
def _resolve_dir(self) -> str:
    """Resolve config directory.

    Global executable uses simplified resolution:
    1. BOUKENSHA_DIR environment variable
    2. ~/.boukensha default

    The current directory check is removed for consistent behavior
    regardless of where the command is run.
    """
    raw = os.environ.get("BOUKENSHA_DIR") or self.DEFAULT_DIR
    return str(Path(raw).expanduser().resolve())
```

**Validation:**
- Config loads from `BOUKENSHA_DIR` if set
- Config loads from `~/.boukensha` if `BOUKENSHA_DIR` not set
- No current directory check

---

### Phase 3: Create Loader Module

**Priority:** HIGH
**Estimated Time:** 2 hours

**File:** `boukensha/loader.py` (NEW)

**Steps:**
1. Create `boukensha/loader.py`
2. Import required modules (sys, os, Path, yaml)
3. Define `Loader` class (or module-level functions)
4. Implement `load_rc()` method
5. Implement `expand_rc_path()` method
6. Implement `resolve()` method
7. Implement `load_and_start_repl()` method
8. Define `main()` entry point function

**Class Structure:**
```python
import os
import sys
from pathlib import Path
from typing import Dict, Optional
import yaml


class Loader:
    """
    BoukenshaLoader resolves which step folder and config directory to use,
    then boots the REPL.

    Each setting is resolved independently in this order:
      1. BOUKENSHA_PATH / BOUKENSHA_DIR environment variable
      2. boukensha_path / boukensha_dir in ~/.boukensharc
      3. The bundled lib / ~/.boukensha default

    Examples:
        boukensha                                              # uses bundled lib + ~/.boukensha
        BOUKENSHA_PATH=~/Sites/boukensha/07_the_run_dsl boukensha  # loads step 7
        BOUKENSHA_DIR=~/projects/mybot/.boukensha boukensha    # custom config dir
    """

    # The bundled module name (this package)
    BUNDLED_MODULE = "boukensha"

    @staticmethod
    def rc_file() -> Path:
        """Return path to ~/.boukensharc"""
        return Path.home() / ".boukensharc"

    @classmethod
    def load_rc(cls) -> Dict[str, str]:
        """Load and parse ~/.boukensharc file.

        Supports two formats:
        1. New format (dict):
           boukensha_path: ~/Sites/boukensha/07_the_run_dsl
           boukensha_dir: ~/Sites/myproject/.boukensha

        2. Legacy format (single string):
           ~/Sites/boukensha/07_the_run_dsl

        Returns:
            Dict with boukensha_path and/or boukensha_dir keys, or empty dict
        """
        rc_file = cls.rc_file()
        if not rc_file.exists():
            return {}

        try:
            with open(rc_file) as f:
                parsed = yaml.safe_load(f)

            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, str):
                # Backward compatibility with single-path format
                return {"boukensha_path": parsed}
            elif parsed is None:
                return {}
            else:
                sys.exit(f"boukensha: {rc_file} must contain a YAML mapping")

        except yaml.YAMLError as e:
            sys.exit(f"boukensha: invalid YAML in {rc_file}: {e}")

    @classmethod
    def expand_rc_path(cls, path: Optional[str]) -> Optional[Path]:
        """Expand a path from ~/.boukensharc.

        Args:
            path: Path string from rc file (can be None)

        Returns:
            Expanded absolute Path, or None if path is invalid
        """
        if not path or not isinstance(path, str) or not path.strip():
            return None

        # Expand relative to home directory
        return Path(path).expanduser().resolve()

    @classmethod
    def resolve(cls) -> str:
        """Resolve which boukensha module/package to load.

        Returns:
            Module name to import (e.g., "boukensha")
        """
        rc = cls.load_rc()

        # Set BOUKENSHA_DIR from rc file if not already set
        rc_config_dir = cls.expand_rc_path(rc.get("boukensha_dir"))
        if not os.environ.get("BOUKENSHA_DIR") and rc_config_dir:
            os.environ["BOUKENSHA_DIR"] = str(rc_config_dir)

        # Check BOUKENSHA_PATH env var first
        source = os.environ.get("BOUKENSHA_PATH") or cls.expand_rc_path(rc.get("boukensha_path"))

        # If no custom path, use bundled module
        if not source:
            return cls.BUNDLED_MODULE

        # Verify the path exists and has lib/boukensha structure
        source_dir = Path(source).resolve()
        expected_init = source_dir / "boukensha" / "__init__.py"

        if not expected_init.exists():
            sys.exit(
                f"boukensha: no boukensha/__init__.py found at:\n"
                f"       {source_dir}\n"
                f"       Check BOUKENSHA_PATH or {cls.rc_file()}."
            )

        # Add parent directory to sys.path so we can import 'boukensha'
        parent_dir = str(source_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        return "boukensha"

    @classmethod
    def load_and_start_repl(cls):
        """Load the resolved boukensha module and start the REPL."""
        module_name = cls.resolve()

        # Show debug info if requested
        if os.environ.get("BOUKENSHA_DEBUG"):
            if module_name == cls.BUNDLED_MODULE:
                print(f"[boukensha] loading bundled module", file=sys.stderr)
            else:
                print(f"[boukensha] loading from: {sys.path[0]}", file=sys.stderr)

        # Import the resolved module
        try:
            import boukensha
        except ImportError as e:
            sys.exit(f"boukensha: failed to import: {e}")

        # Verify it has repl() method (added in step 7)
        if not hasattr(boukensha, 'repl'):
            step_dir = sys.path[0] if sys.path else "(unknown)"
            sys.exit(
                f"boukensha: the step at {step_dir}\n"
                f"       does not support the interactive REPL (added in step 7).\n"
                f"       Run its examples directly, e.g.:\n"
                f"         python {step_dir}/examples/*.py\n"
                f"       Or point BOUKENSHA_PATH at step 7 or later."
            )

        # Start the REPL
        boukensha.repl()


def main():
    """Entry point for the boukensha global command."""
    Loader.load_and_start_repl()


if __name__ == "__main__":
    main()
```

**Validation:**
- Loader resolves bundled module correctly
- Loader resolves custom BOUKENSHA_PATH
- RC file parsing works for both formats
- Environment variables set before import
- Error messages are helpful

---

### Phase 4: Create Package Configuration

**Priority:** HIGH
**Estimated Time:** 30 minutes

**Choose ONE approach:**

#### Option A: setup.py (Traditional)

**File:** `setup.py` (NEW)

```python
from setuptools import setup, find_packages
from pathlib import Path

# Read version from __init__.py
init_file = Path(__file__).parent / "boukensha" / "__init__.py"
version = "0.9.0"
for line in init_file.read_text().splitlines():
    if line.startswith("__version__"):
        version = line.split("=")[1].strip().strip('"\'')
        break

# Read README
readme = Path("README.md").read_text() if Path("README.md").exists() else ""

setup(
    name="boukensha",
    version=version,
    description="BOUKENSHA — a tiny teaching framework for coding harnesses",
    long_description=readme,
    long_description_content_type="text/markdown",
    author="Andrew Brown",
    author_email="andrew@exampro.co",
    license="MIT",
    url="https://github.com/exampro/boukensha",
    python_requires=">=3.8",
    packages=find_packages(),
    package_data={
        "boukensha": ["prompts/*.md"],
    },
    install_requires=[
        "python-dotenv",
        "PyYAML",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "boukensha=boukensha.loader:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
```

#### Option B: pyproject.toml (Modern - RECOMMENDED)

**File:** `pyproject.toml` (NEW)

```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "boukensha"
version = "0.9.0"
description = "BOUKENSHA — a tiny teaching framework for coding harnesses"
readme = "README.md"
requires-python = ">=3.8"
license = {text = "MIT"}
authors = [
    {name = "Andrew Brown", email = "andrew@exampro.co"}
]
keywords = ["mud", "agent", "llm", "teaching", "framework"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "python-dotenv",
    "PyYAML",
    "requests",
]

[project.urls]
Homepage = "https://github.com/exampro/boukensha"
Documentation = "https://github.com/exampro/boukensha"
Repository = "https://github.com/exampro/boukensha"

[project.scripts]
boukensha = "boukensha.loader:main"

[tool.setuptools]
packages = ["boukensha", "boukensha.backends", "boukensha.tasks"]

[tool.setuptools.package-data]
boukensha = ["prompts/*.md"]
```

**Recommendation:** Use `pyproject.toml` - it's the modern standard and cleaner.

**Validation:**
- Package metadata correct
- Console script entry point defined
- Dependencies listed
- Package data (prompts) included

---

### Phase 5: Update Version in __init__.py

**Priority:** HIGH
**Estimated Time:** 5 minutes

**File:** `boukensha/__init__.py` (MODIFIED)

**Steps:**
1. Read existing `__init__.py`
2. Update `__version__ = "0.9.0"`

**Python Changes:**
```python
__version__ = "0.9.0"
```

**Validation:**
- Version string updated

---

### Phase 6: Test Installation

**Priority:** HIGH
**Estimated Time:** 1 hour

**Steps:**

1. **Install in editable mode** (for development):
   ```bash
   cd week1_baseline/python/09_global_executable
   pip install -e .
   ```

2. **Verify installation:**
   ```bash
   which boukensha  # Should show path in Python environment
   boukensha --help  # Should show error (no --help implemented yet)
   ```

3. **Test default behavior:**
   ```bash
   # Ensure ~/.boukensha exists with settings.yaml
   cp -r /path/to/project/.boukensha ~/.boukensha

   # Run boukensha
   boukensha
   # Should start REPL using bundled step 09 + ~/.boukensha config
   ```

4. **Test BOUKENSHA_PATH override:**
   ```bash
   BOUKENSHA_PATH=~/code/claude-code-camp-2026-Q2/week1_baseline/python/07_the_run_dsl boukensha
   # Should load step 07 implementation
   ```

5. **Test BOUKENSHA_DIR override:**
   ```bash
   BOUKENSHA_DIR=/path/to/project/.boukensha boukensha
   # Should use custom config directory
   ```

6. **Test ~/.boukensharc:**
   ```bash
   cat > ~/.boukensharc <<EOF
   boukensha_path: /Users/dshri/code/claude-code-camp-2026-Q2/week1_baseline/python/08_the_repl_loop
   boukensha_dir: /Users/dshri/code/claude-code-camp-2026-Q2/.boukensha
   EOF

   boukensha
   # Should load step 08 implementation with project config
   ```

7. **Test BOUKENSHA_DEBUG:**
   ```bash
   BOUKENSHA_DEBUG=1 boukensha
   # Should show debug output about which module is loaded
   ```

**Validation:**
- `boukensha` command available globally
- Default behavior works (bundled + ~/.boukensha)
- BOUKENSHA_PATH override works
- BOUKENSHA_DIR override works
- ~/.boukensharc file works (both dict and string formats)
- Debug mode shows loading info
- Error messages are helpful

---

### Phase 7: Port Unit Tests (Optional)

**Priority:** LOW
**Estimated Time:** 1 hour

**File:** `tests/test_loader.py` (NEW, optional)

Port the tests from `test/boukensha_loader_test.rb`:

```python
import os
import sys
import tempfile
from pathlib import Path
import pytest
import yaml

from boukensha.loader import Loader


class TestLoader:
    def test_rc_file_path(self):
        """Test rc_file returns ~/.boukensharc"""
        assert Loader.rc_file() == Path.home() / ".boukensharc"

    def test_load_rc_missing_file(self):
        """Test load_rc returns empty dict when file doesn't exist"""
        # This assumes ~/.boukensharc doesn't exist
        if Loader.rc_file().exists():
            pytest.skip("~/.boukensharc exists")

        assert Loader.load_rc() == {}

    def test_load_rc_dict_format(self, tmp_path):
        """Test load_rc parses dict format correctly"""
        rc_file = tmp_path / ".boukensharc"
        rc_file.write_text("boukensha_path: /foo/bar\nboukensha_dir: /baz")

        # Temporarily replace rc_file method
        original_rc_file = Loader.rc_file
        Loader.rc_file = lambda: rc_file

        try:
            result = Loader.load_rc()
            assert result == {"boukensha_path": "/foo/bar", "boukensha_dir": "/baz"}
        finally:
            Loader.rc_file = original_rc_file

    def test_load_rc_string_format(self, tmp_path):
        """Test load_rc handles legacy string format"""
        rc_file = tmp_path / ".boukensharc"
        rc_file.write_text("/foo/bar")

        original_rc_file = Loader.rc_file
        Loader.rc_file = lambda: rc_file

        try:
            result = Loader.load_rc()
            assert result == {"boukensha_path": "/foo/bar"}
        finally:
            Loader.rc_file = original_rc_file

    def test_expand_rc_path(self):
        """Test path expansion"""
        result = Loader.expand_rc_path("~/foo/bar")
        assert result == Path.home() / "foo" / "bar"

    def test_expand_rc_path_empty(self):
        """Test expand_rc_path returns None for empty strings"""
        assert Loader.expand_rc_path("") is None
        assert Loader.expand_rc_path("   ") is None
        assert Loader.expand_rc_path(None) is None

    # Add more tests as needed
```

**Validation:**
- All unit tests pass
- Edge cases covered

---

## Testing Strategy

### Manual Validation

1. **Installation:**
   ```bash
   cd week1_baseline/python/09_global_executable
   pip install -e .
   which boukensha  # Verify it's installed
   ```

2. **Default behavior:**
   ```bash
   # Ensure ~/.boukensha exists
   boukensha
   # Should start REPL with bundled step 09
   ```

3. **Environment variable overrides:**
   ```bash
   BOUKENSHA_PATH=~/path/to/step7 boukensha
   BOUKENSHA_DIR=~/myproject/.boukensha boukensha
   BOUKENSHA_DEBUG=1 boukensha
   ```

4. **RC file configuration:**
   ```bash
   echo "boukensha_path: ~/path/to/step8" > ~/.boukensharc
   boukensha
   ```

5. **Error handling:**
   ```bash
   BOUKENSHA_PATH=/invalid/path boukensha  # Should show helpful error
   ```

6. **Compare with Ruby:**
   ```bash
   # Test same scenarios with Ruby gem
   gem install boukensha-0.9.0.gem
   boukensha
   ```

### Automated Tests (Optional)

- Run pytest: `pytest tests/`
- Test coverage: `pytest --cov=boukensha tests/`

---

## Migration Checklist

### Pre-Port
- [x] Analyze Ruby codebase structure
- [x] Identify changes from Step 08
- [x] Document translation patterns
- [x] Create porting plan

### Step 09 Port
- [ ] Copy entire `08_the_repl_loop` directory to `09_global_executable`
- [ ] Simplify `config.py` resolve_dir() method
- [ ] Create `boukensha/loader.py` with Loader class
- [ ] Create `pyproject.toml` (or `setup.py`)
- [ ] Update VERSION to "0.9.0" in `boukensha/__init__.py`
- [ ] Install in editable mode: `pip install -e .`
- [ ] Test global `boukensha` command
- [ ] Port unit tests (optional)

### Testing & Finalization
- [ ] Test default behavior (bundled + ~/.boukensha)
- [ ] Test BOUKENSHA_PATH override
- [ ] Test BOUKENSHA_DIR override
- [ ] Test ~/.boukensharc (dict format)
- [ ] Test ~/.boukensharc (legacy string format)
- [ ] Test BOUKENSHA_DEBUG mode
- [ ] Test error messages
- [ ] Compare behavior with Ruby gem
- [ ] Build wheel: `python -m build`
- [ ] Test wheel installation: `pip install dist/*.whl`
- [ ] Update README.md

---

## Known Differences & Gotchas

### 1. **Package Installation**

**Ruby:** Build and install gem
```bash
gem build boukensha.gemspec
gem install boukensha-0.9.0.gem
```

**Python:** Build and install with pip
```bash
pip install -e .  # Editable install
# OR
python -m build   # Build wheel
pip install dist/boukensha-0.9.0-*.whl
```

**Impact:** Different commands, same result

### 2. **Entry Point Creation**

**Ruby:** Creates wrapper script in `bin/` that calls Ruby code
**Python:** pip creates wrapper script automatically from entry_points

**Impact:** No bin/ directory needed in Python

### 3. **Module Loading**

**Ruby:** Uses `require` with file path
```ruby
require "/path/to/lib/boukensha.rb"
```

**Python:** Adds directory to sys.path, then imports by name
```python
sys.path.insert(0, "/path/to/step")
import boukensha
```

**Impact:** Python is cleaner (no file extensions)

### 4. **Package Data**

**Ruby:** `spec.files = Dir["lib/**/*.rb"]` includes all Ruby files
**Python:** Need explicit `package_data` or `MANIFEST.in` for non-Python files

```toml
[tool.setuptools.package-data]
boukensha = ["prompts/*.md"]
```

### 5. **Editable Install**

**Ruby:** `bundle exec` or path manipulation
**Python:** `pip install -e .` creates symlinks - changes are live

**Impact:** Development workflow is easier in Python

### 6. **Version Management**

**Ruby:** `lib/boukensha/version.rb` with constant
**Python:** Can be in `__init__.py` or read from pyproject.toml

**Impact:** Slight structural difference

---

## Success Criteria

All criteria must be met:

- [ ] `Loader` class implemented with all resolution methods
- [ ] `main()` entry point function works
- [ ] Package configuration complete (pyproject.toml or setup.py)
- [ ] Global `boukensha` command installs via pip
- [ ] Default behavior works (bundled + ~/.boukensha)
- [ ] BOUKENSHA_PATH override works
- [ ] BOUKENSHA_DIR override works
- [ ] ~/.boukensharc works (both dict and string formats)
- [ ] Environment variables set before module import
- [ ] Error messages are helpful and match Ruby version
- [ ] BOUKENSHA_DEBUG shows loading information
- [ ] Module detection (hasattr) works correctly
- [ ] Config resolution simplified (no cwd check)
- [ ] Code is compatible with Python 3.8+
- [ ] Type hints are comprehensive
- [ ] Code follows Python best practices (PEP 8)
- [ ] No regressions from Step 08 functionality

---

## Timeline Estimate

| Phase | Estimated Time | Complexity |
|-------|----------------|------------|
| Copy from 08_the_repl_loop | 15 min | Trivial |
| Simplify config resolution | 15 min | Simple |
| Create Loader module | 2 hours | Medium |
| Create package config | 30 min | Simple |
| Update version | 5 min | Trivial |
| Test installation | 1 hour | Medium |
| Port unit tests (optional) | 1 hour | Medium |
| **Total** | **5-6 hours** | - |

**Note:** The Loader module is the most complex part (~2 hours), involving path resolution, YAML parsing, dynamic imports, and environment variable management.

---

## Next Steps

**Ready to start!** Begin with:

```bash
# Copy entire 08_the_repl_loop directory
cp -r week1_baseline/python/08_the_repl_loop week1_baseline/python/09_global_executable
cd week1_baseline/python/09_global_executable
```

Then modify/create files in this order:

1. **Simplify `boukensha/config.py`** - Remove cwd check from resolve_dir() (15 min)
2. **Create `boukensha/loader.py`** - Implement Loader class (2 hours)
3. **Create `pyproject.toml`** - Package configuration (30 min)
4. **Update `boukensha/__init__.py`** - Set VERSION = "0.9.0" (5 min)
5. **Install and test** - `pip install -e .` and verify (1 hour)

**Key files to reference:**
- `week1_baseline/ruby/09_global_executable/lib/boukensha_loader.rb` (96 lines)
- `week1_baseline/ruby/09_global_executable/boukensha.gemspec` (24 lines)
- `week1_baseline/ruby/09_global_executable/bin/boukensha` (8 lines)
- `week1_baseline/ruby/09_global_executable/lib/boukensha/config.rb` (for resolve_dir changes)

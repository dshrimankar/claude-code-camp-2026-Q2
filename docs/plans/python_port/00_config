# Python Port Plan: Boukensha Configuration System

## Overview
This plan outlines the port of the Boukensha configuration system from Ruby to Python, targeting Python 3.8+ compatibility with type hints and dataclasses while keeping dependencies minimal (stdlib-focused).

## Scope
Port **Boukensha** configuration system only:
- **Source:** `week1_baseline/ruby/00_config/`
- **Target:** `week1_baseline/python/00_config/`

**Note:** MudManager (`week0_explore/mud_manager/`) is NOT included in this port.

## Target Directory Structure

```
week1_baseline/
  ruby/00_config/       # Ruby (keep as reference)
  python/               # NEW: Python port
    00_config/
      boukensha/
        __init__.py
        config.py
        tasks/
          __init__.py
          base.py
          player.py
      prompts/
        system.md
      examples/
        example.py
      requirements.txt
      README.md
```

---

## File-by-File Mapping

| Ruby File | Python File | Lines | Complexity | Notes |
|-----------|-------------|-------|------------|-------|
| `lib/boukensha.rb` | `boukensha/__init__.py` | 3 | Simple | Module imports |
| `lib/boukensha/config.rb` | `boukensha/config.py` | 94 | Medium | YAML, env loading, path resolution |
| `lib/boukensha/tasks/base.rb` | `boukensha/tasks/base.py` | 61 | Medium | Abstract base, prompt resolution |
| `lib/boukensha/tasks/player.rb` | `boukensha/tasks/player.py` | 10 | Simple | Concrete task implementation |
| `prompts/system.md` | `prompts/system.md` | - | - | Copy as-is |
| `examples/example.rb` | `examples/example.py` | 27 | Low | Smoke test |

**Total Lines to Port:** ~165 lines (excluding prompts/examples)

**Key Translation Challenges:**
- Ruby `require_relative` → Python `import` / `from X import Y`
- Ruby `YAML.safe_load` → Python `yaml.safe_load` (PyYAML)
- Ruby `Dotenv.load` → Python `python-dotenv` (`load_dotenv`)
- Ruby `File.expand_path` → Python `pathlib.Path.resolve()`
- Ruby `Dir.home` → Python `pathlib.Path.home()`
- Ruby `module` → Python class or module-level code
- Ruby symbol/string key flexibility → Python dict access patterns
- Ruby `freeze` → Python `Final` type hint (documentation only)
- Ruby `to_s` / `inspect` → Python `__str__` / `__repr__`

---

## Dependencies

**External (minimal):**
- `PyYAML` - YAML parsing (equivalent to Ruby stdlib yaml)
- `python-dotenv` - .env file loading (equivalent to Ruby dotenv gem)

**Stdlib:**
- `pathlib` - Path manipulation
- `os` - Environment variables
- `typing` - Type hints
- `abc` - Abstract base classes

---

## Key Translation Patterns

### 1. Ruby Class Methods → Python Class Methods
```ruby
# Ruby
class Base
  def self.provider(settings)
    # ...
  end
end
```
```python
# Python
from abc import ABC, abstractmethod

class Base(ABC):
    @classmethod
    @abstractmethod
    def task_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def provider(cls, settings: dict) -> str:
        # ...
```

### 2. Path Resolution
```ruby
# Ruby
File.expand_path("../../prompts", __dir__)
```
```python
# Python
from pathlib import Path
Path(__file__).parent.parent / "prompts"
```

### 3. Hash/Dict Key Access
```ruby
# Ruby - flexible symbol/string access
settings[:provider] || settings["provider"]
```
```python
# Python - explicit handling
settings.get("provider") or settings.get("provider")
# OR use helper function
def _get_key(d, key):
    return d.get(str(key))
```

---

## Phase 1: Port Core Files

**Priority:** HIGH

### Steps:
1. ✅ Create directory structure: `week1_baseline/python/00_config/boukensha/`
2. ✅ Port `config.py`:
   - Define `Config` class with type hints
   - Implement directory resolution logic (BOUKENSHA_DIR env var, ~/.boukensha)
   - Add `.env` loading via `python-dotenv`
   - Add `settings.yaml` loading via `PyYAML`
   - Port helper methods: `tasks()`, `dig()`, MUD connection getters
   - Add `__str__` and `__repr__`
3. ✅ Port `tasks/base.py`:
   - Create abstract `Base` class using `abc.ABC`
   - Port class methods with type hints
   - Implement prompt resolution logic (user override vs default)
4. ✅ Port `tasks/player.py`:
   - Concrete `Player` subclass
5. ✅ Create `__init__.py` files for proper imports
6. ✅ Copy `prompts/system.md` as-is
7. ✅ Port `examples/example.py`
8. ✅ Create `requirements.txt`: `PyYAML`, `python-dotenv`

**Reference Files:**
- `week1_baseline/ruby/00_config/lib/boukensha/config.rb` (94 lines)
- `week1_baseline/ruby/00_config/lib/boukensha/tasks/base.rb` (61 lines)
- `week1_baseline/ruby/00_config/lib/boukensha/tasks/player.py` (10 lines)
- `week1_baseline/ruby/00_config/examples/example.rb` (27 lines)

**Validation:**
- Config loads from `.boukensha/settings.yaml`
- Environment variables loaded from `.boukensha/.env`
- Task settings accessible via `config.tasks("player")`
- Prompt override logic works correctly
- Example runs and displays config information

---

## Phase 2: Testing & Documentation

**Priority:** MEDIUM

### Steps:
1. ✅ Test example.py with real `.boukensha/` config
2. ✅ Verify all config methods work correctly
3. ✅ Document any behavioral differences from Ruby
4. ✅ Add type checking with `mypy` (optional but recommended)
5. ✅ Write README.md for Python port

---

## Python 3.8 Compatibility Considerations

**Use:**
- `from __future__ import annotations` - for forward references
- `typing.Dict`, `typing.List`, `typing.Optional` - not `dict`, `list`, `None | T`
- `typing.Union[X, Y]` - not `X | Y`
- Standard library `pathlib`, `os`

**Avoid:**
- `match`/`case` statements (3.10+)
- `|` union operator for types (3.10+) - use `Union[X, Y]` instead
- `dict | dict` merge operator (3.9+) - use `{**d1, **d2}` instead
- `str.removeprefix`/`removesuffix` (3.9+)

---

## Testing Strategy

### Manual Validation
- Run `examples/example.py` to verify Boukensha config loading
- Compare output with Ruby equivalent
- Test with different `.boukensha/settings.yaml` configurations
- Test prompt override functionality

### Unit Tests (Optional - Phase 2)
- Test `config.py` with mocked filesystem/env
- Test `tasks/base.py` prompt resolution logic
- Test `dig()` method with various nested structures

---

## Migration Checklist

### Pre-Port
- [x] Analyze Ruby codebase structure
- [x] Identify all dependencies
- [x] Create directory structure plan
- [x] Document translation patterns

### Boukensha Port
- [ ] Create directory structure
- [ ] Port `boukensha/__init__.py`
- [ ] Port `config.py`
- [ ] Port `tasks/__init__.py`
- [ ] Port `tasks/base.py`
- [ ] Port `tasks/player.py`
- [ ] Copy `prompts/system.md`
- [ ] Port `examples/example.py`
- [ ] Create `requirements.txt`

### Testing & Finalization
- [ ] Run example.py successfully
- [ ] Test with real `.boukensha/` config
- [ ] Add type checking (mypy) - optional
- [ ] Write README for Python port
- [ ] Document any behavior changes

---

## Known Differences & Gotchas

1. **Hash/Dict Key Access:**
   - Ruby allows both symbol (`:key`) and string (`"key"`) keys flexibly
   - Python requires explicit key type handling
   - Use `.get()` with defaults for safer access

2. **Module vs Class:**
   - Ruby modules with class methods → Python classes with `@classmethod`
   - Import patterns differ slightly

3. **Abstract Classes:**
   - Ruby uses convention (`raise NotImplementedError`)
   - Python uses `abc.ABC` and `@abstractmethod` decorators for enforcement

4. **Frozen Constants:**
   - Ruby `.freeze` has runtime enforcement
   - Python `Final` is type-checker only (no runtime effect)

5. **Path Handling:**
   - Ruby uses `File` module with string paths
   - Python `pathlib.Path` is more object-oriented
   - Both approaches work, but `pathlib` is more Pythonic

---

## Success Criteria

✅ All Ruby functionality is replicated in Python
✅ Python code is well-typed with comprehensive type hints
✅ All examples run successfully
✅ Can load configuration from `.boukensha/`
✅ Code is compatible with Python 3.8+
✅ Dependencies are minimal (stdlib + PyYAML + python-dotenv only)
✅ Code follows Python best practices (PEP 8, etc.)
✅ No regressions in functionality compared to Ruby

---

## Timeline Estimate

| Phase | Estimated Time | Complexity |
|-------|----------------|------------|
| Directory setup | 10 min | Trivial |
| Port config.py | 1-2 hours | Medium |
| Port tasks/base.py | 45-60 min | Medium |
| Port tasks/player.py | 15 min | Low |
| Port __init__ files | 15 min | Low |
| Port examples | 30 min | Low |
| Testing & validation | 1 hour | Medium |
| Documentation | 30 min | Low |
| **Total** | **4-6 hours** | - |

---

## Next Steps

**Ready to start!** Begin with:

```bash
mkdir -p week1_baseline/python/00_config/boukensha/tasks
mkdir -p week1_baseline/python/00_config/prompts
mkdir -p week1_baseline/python/00_config/examples
```

Then create files in this order:
1. `boukensha/__init__.py` (simple)
2. `boukensha/config.py` (core logic)
3. `boukensha/tasks/__init__.py` (simple)
4. `boukensha/tasks/base.py` (abstract base)
5. `boukensha/tasks/player.py` (concrete implementation)
6. Copy `prompts/system.md`
7. Port `examples/example.py`
8. Create `requirements.txt`

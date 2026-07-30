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
    def resolve(cls):
        """Resolve which boukensha module/package to load.

        Returns:
            Tuple of (module_name, source_dir) where source_dir is None for bundled
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
            return (cls.BUNDLED_MODULE, None)

        # Verify the path exists and has boukensha package structure
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

        return ("boukensha", source_dir)

    @classmethod
    def load_and_start_repl(cls):
        """Load the resolved boukensha module and start the REPL."""
        module_name, source_dir = cls.resolve()

        # Show debug info if requested
        if os.environ.get("BOUKENSHA_DEBUG"):
            if source_dir is None:
                print(f"[boukensha] loading bundled module", file=sys.stderr)
            else:
                print(f"[boukensha] loading from: {source_dir}", file=sys.stderr)

        # Import the resolved module
        try:
            import boukensha
        except ImportError as e:
            sys.exit(f"boukensha: failed to import: {e}")

        # Verify it has repl() method (added in step 7)
        if not hasattr(boukensha, 'repl'):
            step_dir = source_dir if source_dir else "(bundled)"
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

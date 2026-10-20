#!/usr/bin/env python3
"""Portable host CLI with explicit inputs and no accidental fixture run."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "runtime"))


def main():
    if "--help" not in sys.argv and "-h" not in sys.argv:
        for flag in ("--prd", "--run"):
            if not any(arg == flag or arg.startswith(flag + "=") for arg in sys.argv[1:]):
                print(json.dumps({"error": f"Provide explicit {flag}; bundled fixtures are not real tasks."}), file=sys.stderr)
                return 2
    try:
        from atc10.__main__ import main as coordinator_main
    except ModuleNotFoundError as exc:
        if exc.name != "jsonschema":
            raise
        print(json.dumps({"error": "Install scripts/runtime/requirements.txt with Python 3.11+ first."}), file=sys.stderr)
        return 2
    return coordinator_main()


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Wrapper to run gemini/listar.py from the project root.

This preserves the original script behavior and forwards any CLI arguments.
"""
from pathlib import Path
import runpy
import sys


def main() -> int:
    script = Path(__file__).with_name("gemini") / "listar.py"
    if not script.exists():
        print(f"Arquivo não encontrado: {script}")
        return 1

    original_argv = sys.argv
    sys.argv = [str(script), *original_argv[1:]]
    try:
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = original_argv

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

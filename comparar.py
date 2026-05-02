#!/usr/bin/env python3
"""Wrapper to run gemini/comparar.py from the project root.

Run with `python comparar.py` from the repository root.
"""
from pathlib import Path
import runpy
import sys
import argparse
import builtins


def main() -> int:
    parser = argparse.ArgumentParser(description="Run gemini/comparar.py (interactive or via CLI args)")
    parser.add_argument("cursos", nargs="*", help="Dois nomes de curso para comparar (opcional)")
    args = parser.parse_args()

    script = Path(__file__).with_name("gemini") / "comparar.py"
    if not script.exists():
        print(f"Arquivo não encontrado: {script}")
        return 1

    # If two course names are provided, patch builtins.input to return them sequentially
    if args.cursos and len(args.cursos) >= 2:
        inputs = iter(args.cursos[:2])
        original_input = builtins.input

        def _fake_input(prompt=""):
            try:
                return next(inputs)
            except StopIteration:
                return original_input(prompt)

        builtins.input = _fake_input
        try:
            runpy.run_path(str(script), run_name="__main__")
        finally:
            builtins.input = original_input
    else:
        # Execute normally (will prompt the user)
        runpy.run_path(str(script), run_name="__main__")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

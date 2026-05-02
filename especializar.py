#!/usr/bin/env python3
"""Wrapper to run gemini/especializar.py from the project root.

Run with `python especializar.py` (interactive) or `python especializar.py NomeDoCurso` (CLI).
"""
from pathlib import Path
import runpy
import sys
import argparse
import builtins


def main() -> int:
    parser = argparse.ArgumentParser(description="Run gemini/especializar.py (interactive or via CLI arg)")
    parser.add_argument("curso", nargs="?", help="Nome do curso para especializar (opcional)")
    args = parser.parse_args()

    script = Path(__file__).with_name("gemini") / "especializar.py"
    if not script.exists():
        print(f"Arquivo não encontrado: {script}")
        return 1

    # If a course name is provided, patch builtins.input to return it
    if args.curso:
        inputs = iter([args.curso])
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

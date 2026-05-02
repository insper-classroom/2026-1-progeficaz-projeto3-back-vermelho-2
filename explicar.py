#!/usr/bin/env python3
"""Wrapper to run gemini/explicar.py from the project root.

Run with `python explicar.py` (interactive) or `python explicar.py NomeDoCurso` (CLI).
"""
from pathlib import Path
import argparse
import builtins
import runpy


def main() -> int:
    parser = argparse.ArgumentParser(description="Run gemini/explicar.py (interactive or via CLI arg)")
    parser.add_argument("curso", nargs="?", help="Nome do curso para explicar (opcional)")
    args = parser.parse_args()

    script = Path(__file__).with_name("gemini") / "explicar.py"
    if not script.exists():
        print(f"Arquivo não encontrado: {script}")
        return 1

    if args.curso:
        original_input = builtins.input
        builtins.input = lambda prompt='': args.curso
        try:
            runpy.run_path(str(script), run_name="__main__")
        finally:
            builtins.input = original_input
    else:
        runpy.run_path(str(script), run_name="__main__")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

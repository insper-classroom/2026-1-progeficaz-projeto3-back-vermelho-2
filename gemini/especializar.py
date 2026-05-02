#!/usr/bin/env python3
"""Chama a função `especializar()` definida em `api gemini.py`.

Carrega o arquivo pelo caminho (não importa que o nome do arquivo contenha espaços)
e executa a função `()`.
"""
from pathlib import Path
import importlib.util
import sys


def load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    script_path = Path(__file__).with_name("api gemini.py")
    if not script_path.exists():
        print(f"Arquivo não encontrado: {script_path}")
        sys.exit(1)

    mod = load_module_from_path(script_path, "api_gemini_module")
    if hasattr(mod, "especializar"):
        mod.especializar()
    else:
        print("Função 'especializar' não encontrada em api gemini.py")
        sys.exit(1)

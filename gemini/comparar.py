#!/usr/bin/env python3
"""Chama a função `comparar()` definida em `api_gemini.py`.

Carrega o arquivo pelo caminho (não importa que o nome do arquivo contenha espaços)
e executa a função `comparar()`.
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
    script_path = Path(__file__).with_name("api_gemini.py")
    if not script_path.exists():
        print(f"Arquivo não encontrado: {script_path}")
        sys.exit(1)

    mod = load_module_from_path(script_path, "api_gemini_module")
    if hasattr(mod, "comparar"):
        mod.comparar()
    else:
        print("Função 'comparar' não encontrada em api_gemini.py")
        sys.exit(1)

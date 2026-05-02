#!/usr/bin/env python3
from pathlib import Path
import sys
import argparse
import json
import sqlite3


def load_info(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Gera um JSON com a listagem de cursos')
    parser.add_argument('--local', action='store_true', help='Ler cursos diretamente de info.json')
    parser.add_argument('--file', '-f', default='info.json', help='Caminho para info.json (quando --local)')
    parser.add_argument('--export', '-o', help='Salvar a listagem em JSON no caminho fornecido')
    args = parser.parse_args()

    cursos = []
    if args.local:
        info_path = Path(args.file)
        if not info_path.exists():
            print(f"Arquivo não encontrado: {info_path}")
            sys.exit(1)
        data = load_info(info_path)
        cursos = data.get('lista_cursos', [])
    else:
        db_path = Path(__file__).with_name('gemini.db')
        if not db_path.exists():
            print(f"Banco não encontrado: {db_path}. Use --local para ler o arquivo info.json em vez disso.")
            sys.exit(1)

        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT value_key, response, created_at FROM responses WHERE category=? ORDER BY created_at DESC", ('explicar',))
        rows = cur.fetchall()

        if not rows:
            info_path = Path(__file__).with_name('info.json')
            if not info_path.exists():
                print(f"Nenhuma entrada 'explicar' no DB e {info_path} não encontrado.")
                sys.exit(0)
            data = load_info(info_path)
            cursos = data.get('lista_cursos', [])
        else:
            for value_key, response_text, created_at in rows:
                try:
                    obj = json.loads(response_text)
                    if isinstance(obj, dict) and 'Curso' in obj:
                        cursos.append(obj)
                    else:
                        cursos.append({'Curso': value_key, 'Descricao': '', 'Faculdades': [], 'Carreiras': [], 'Profissionalizacoes': [], 'raw': obj})
                except Exception:
                    cursos.append({'Curso': value_key, 'Descricao': response_text, 'Faculdades': [], 'Carreiras': [], 'Profissionalizacoes': []})
        conn.close()

    result = {'lista': {'lista_cursos': cursos}}

    if args.export:
        out_path = Path(args.export)
        try:
            with out_path.open('w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Falha ao exportar para {out_path}: {e}")

    print(json.dumps(result, ensure_ascii=False, indent=2))

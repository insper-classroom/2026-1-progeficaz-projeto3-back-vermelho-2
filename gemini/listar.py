#!/usr/bin/env python3
from pathlib import Path
import argparse
import json
import os
import sys

from dotenv import load_dotenv
from pymongo import MongoClient


def load_info(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def load_from_mongo():
    load_dotenv(dotenv_path=Path(__file__).with_name('.env'))
    mongo_uri = os.getenv('MONGO_URI')
    mongo_db_name = os.getenv('MONGO_DB_NAME', 'planejador_carreira')

    if not mongo_uri:
        print('MONGO_URI não encontrada. Use --local para ler o arquivo info.json.')
        sys.exit(1)

    client = MongoClient(mongo_uri)
    db = client[mongo_db_name]
    response_collection = db['cursos']

    rows = response_collection.find(
        {},
        {'value_key': 1, 'response': 1, 'created_at': 1},
    ).sort('created_at', -1)

    cursos = []
    for doc in rows:
        value_key = doc.get('value_key', '')
        response_text = doc.get('response', '')

        try:
            obj = json.loads(response_text)
            if isinstance(obj, dict) and 'Curso' in obj:
                cursos.append(obj)
            else:
                cursos.append({'Curso': value_key, 'Descricao': '', 'Faculdades': [], 'Carreiras': [], 'Profissionalizacoes': [], 'raw': obj})
        except Exception:
            cursos.append({'Curso': value_key, 'Descricao': response_text, 'Faculdades': [], 'Carreiras': [], 'Profissionalizacoes': []})

    client.close()
    return cursos


def normalize_courses(cursos):
    normalizados = []
    for item in cursos:
        if isinstance(item, dict) and isinstance(item.get('lista_cursos'), list):
            normalizados.extend(item['lista_cursos'])
        elif isinstance(item, dict) and len(item) == 1 and isinstance(next(iter(item.values())), list):
            normalizados.extend(next(iter(item.values())))
        else:
            normalizados.append(item)
    return normalizados


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
        cursos = load_from_mongo()

        if not cursos:
            info_path = Path(__file__).with_name('info.json')
            if not info_path.exists():
                print(f"Nenhuma entrada 'explicar' no MongoDB e {info_path} não encontrado.")
                sys.exit(0)
            data = load_info(info_path)
            cursos = data.get('lista_cursos', [])

            cursos = normalize_courses(cursos)
            result = {'lista_cursos': cursos}

    if args.export:
        out_path = Path(args.export)
        try:
            with out_path.open('w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Falha ao exportar para {out_path}: {e}")

    print(json.dumps(result, ensure_ascii=False, indent=2))

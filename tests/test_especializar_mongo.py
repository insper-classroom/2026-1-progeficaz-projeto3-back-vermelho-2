#!/usr/bin/env python
"""
Teste de ESPECIALIZAR com MongoDB (mongomock)
Simula a função especializar() lendo dados do MongoDB
"""
import sqlite3
import os
import sys
import json
from datetime import datetime

import mongomock

class DatabaseServiceMock:
    """Mock de DatabaseService que usa mongomock"""
    def __init__(self, client):
        self.db = client["planejador_carreira"]
        self.responses = self.db["responses"]

    def get_responses(self, category: str, value_key: str):
        docs = (
            self.responses.find(
                {"category": category, "value_key": value_key},
                {"response": 1, "created_at": 1},
            )
            .sort("created_at", -1)
        )
        return [(doc["response"], doc.get("created_at")) for doc in docs]

def parse_timestamp(ts_str):
    """Converter string timestamp SQLite para datetime."""
    try:
        return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
    except:
        return datetime.now()

def migrate_from_sqlite(client):
    """Migrar dados do SQLite para MongoDB (simulado)."""
    db = client["planejador_carreira"]
    db.responses.delete_many({})
    
    total_responses = 0
    
    for db_path in ['gemini.db', 'gemini/gemini.db']:
        if not os.path.exists(db_path):
            continue
            
        sqlite_conn = sqlite3.connect(db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        sqlite_cursor.execute('SELECT category, value_key, response, created_at FROM responses;')
        for category, value_key, response, created_at in sqlite_cursor.fetchall():
            doc = {
                'category': category,
                'value_key': value_key,
                'response': response,
                'created_at': parse_timestamp(created_at)
            }
            db.responses.insert_one(doc)
            total_responses += 1
        
        sqlite_conn.close()
    
    return total_responses

def format_json_response(json_str):
    """Formatar resposta JSON para exibição."""
    try:
        data = json.loads(json_str)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except:
        return json_str

def test_especializar(curso: str):
    """Testar especializar() usando dados existentes no MongoDB."""
    print('='*70)
    print(f'🔍 TESTE: Especializar "{curso}"')
    print('='*70)
    
    client = mongomock.MongoClient()
    migrate_from_sqlite(client)
    
    db_service = DatabaseServiceMock(client)
    
    # Buscar respostas existentes
    existing = db_service.get_responses("especializar", curso)
    
    if existing:
        response_text, created_at = existing[0]
        print(f'\n✅ Encontrado no MongoDB:')
        print(f'   Curso: {curso}')
        print(f'   Criado em: {created_at}')
        print(f'\n📊 Resposta:\n')
        
        # Mostrar resposta (truncada se muito longa)
        resp_formatted = format_json_response(response_text)
        if len(resp_formatted) > 2000:
            print(resp_formatted[:2000])
            print(f'\n... (resposta truncada, total: {len(resp_formatted)} caracteres)')
        else:
            print(resp_formatted)
        return True
    else:
        print(f'\n❌ Nenhuma resposta encontrada para: {curso}')
        print(f'\n💡 Cursos disponíveis para ESPECIALIZAR:')
        db = client["planejador_carreira"]
        all_especializacoes = db.responses.find({'category': 'especializar'})
        cursos = set()
        for doc in all_especializacoes:
            key = doc["value_key"]
            if key:  # Ignorar chaves vazias
                cursos.add(key)
        
        for curso in sorted(cursos):
            print(f'   • {curso}')
        return False

def main():
    print('\n🚀 TESTE DE ESPECIALIZAR COM MONGODB (mongomock)\n')
    
    if len(sys.argv) < 2:
        # Modo sem argumentos - listar opções disponíveis
        print('📋 Uso: python test_especializar_mongo.py "Curso"\n')
        print('Exemplos:')
        print('  python test_especializar_mongo.py "Engenharia"')
        print('  python test_especializar_mongo.py "microeconomia"')
        print('  python test_especializar_mongo.py "Ciencia da Computacao"\n')
        
        # Mostrar opções disponíveis
        client = mongomock.MongoClient()
        migrate_from_sqlite(client)
        db = client["planejador_carreira"]
        
        print('✅ Cursos disponíveis para ESPECIALIZAR:')
        all_docs = list(db.responses.find({'category': 'especializar'}))
        cursos = set()
        for doc in all_docs:
            key = doc["value_key"]
            if key:
                cursos.add(key)
        
        for curso in sorted(cursos):
            print(f'   • {curso}')
        
        print(f'\nTotal: {len(all_docs)} especializações no banco')
        sys.exit(0)
    
    # Modo com argumentos - testar especialização específica
    curso = sys.argv[1]
    test_especializar(curso)
    
    print('\n' + '='*70)

if __name__ == '__main__':
    main()

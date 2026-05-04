#!/usr/bin/env python
"""
Teste de COMPARAR com MongoDB (mongomock)
Simula a função comparar() mas lê dados do MongoDB ao invés de fazer chamada Gemini
"""
import sqlite3
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Usar mongomock para simulação local
import mongomock

# Simular GeminiService com MongoDB
from pymongo import MongoClient as RealMongoClient

class DatabaseServiceMock:
    """Mock de DatabaseService que usa mongomock"""
    def __init__(self, client):
        self.db = client["planejador_carreira"]
        self.responses = self.db["responses"]
        self.requests = self.db["requests"]

    def get_responses(self, category: str, value_key: str):
        docs = (
            self.responses.find(
                {"category": category, "value_key": value_key},
                {"response": 1, "created_at": 1},
            )
            .sort("created_at", -1)
        )
        return [(doc["response"], doc.get("created_at")) for doc in docs]

    def save_response(self, category: str, value_key: str, response_text: str) -> None:
        self.responses.insert_one(
            {
                "category": category,
                "value_key": value_key,
                "response": response_text,
                "created_at": datetime.now(),
            }
        )

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
    db.requests.delete_many({})
    
    print('🧹 Collections limpas')
    
    total_responses = 0
    total_requests = 0
    
    for db_path in ['gemini.db', 'gemini/gemini.db']:
        if not os.path.exists(db_path):
            continue
            
        sqlite_conn = sqlite3.connect(db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Migrar responses
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
    
    print(f'✓ Migrados {total_responses} responses\n')
    return total_responses

def format_json_response(json_str):
    """Formatar resposta JSON para exibição."""
    try:
        data = json.loads(json_str)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except:
        return json_str

def test_comparar_with_existing_data(c1: str, c2: str):
    """Testar comparar() usando dados existentes no MongoDB."""
    print('='*70)
    print(f'🔍 TESTE: Comparar "{c1}" × "{c2}"')
    print('='*70)
    
    # Criar cliente mongomock e migrar dados
    client = mongomock.MongoClient()
    migrate_from_sqlite(client)
    
    # Simular DatabaseService
    db_service = DatabaseServiceMock(client)
    
    # Buscar respostas existentes
    key = f"{c1}|{c2}"
    existing = db_service.get_responses("comparar", key)
    
    if existing:
        response_text, created_at = existing[0]
        print(f'\n✅ Encontrado no MongoDB:')
        print(f'   Chave: {key}')
        print(f'   Criado em: {created_at}')
        print(f'\n📊 Resposta:\n')
        print(format_json_response(response_text))
        return True
    else:
        print(f'\n❌ Nenhuma resposta encontrada para: {key}')
        print(f'\n💡 Dados disponíveis para COMPARAR:')
        db = client["planejador_carreira"]
        all_comparacoes = db.responses.find({'category': 'comparar'})
        for doc in all_comparacoes:
            print(f'   • {doc["value_key"]}')
        return False

def main():
    print('\n🚀 TESTE DE COMPARAR COM MONGODB (mongomock)\n')
    
    if len(sys.argv) < 2:
        # Modo sem argumentos - listar opções disponíveis
        print('📋 Uso: python test_comparar_mongo.py "Curso1|Curso2"\n')
        print('Exemplos:')
        print('  python test_comparar_mongo.py "Engenharia|Medicina"')
        print('  python test_comparar_mongo.py "Corredor|poliatleta"')
        print('  python test_comparar_mongo.py "pintor|medicina"\n')
        
        # Mostrar opções disponíveis
        client = mongomock.MongoClient()
        migrate_from_sqlite(client)
        db = client["planejador_carreira"]
        
        print('✅ Comparações disponíveis no banco:')
        for doc in db.responses.find({'category': 'comparar'}):
            print(f'   • {doc["value_key"]}')
        sys.exit(0)
    
    # Modo com argumentos - testar comparação específica
    comparison = sys.argv[1]
    
    if '|' not in comparison:
        print(f'❌ Formato inválido: {comparison}')
        print('Use: "Curso1|Curso2"\n')
        sys.exit(1)
    
    c1, c2 = comparison.split('|', 1)
    test_comparar_with_existing_data(c1.strip(), c2.strip())
    
    print('\n' + '='*70)

if __name__ == '__main__':
    main()

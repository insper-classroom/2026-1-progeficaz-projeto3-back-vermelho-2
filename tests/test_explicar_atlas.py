#!/usr/bin/env python
"""
Teste de EXPLICAR contra MongoDB Atlas REAL
"""
import os
import sys
import json
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class DatabaseServiceAtlas:
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI')
        self.db_name = os.getenv('MONGO_DB_NAME', 'planejador_carreira')
        if not self.mongo_uri:
            raise RuntimeError("MONGO_URI não encontrada")
        self.client = MongoClient(
            self.mongo_uri,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        self.db = self.client[self.db_name]
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
    
    def close(self):
        self.client.close()

def format_json_response(json_str):
    try:
        data = json.loads(json_str)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except:
        return json_str

def test_explicar_atlas(curso: str):
    print('='*70)
    print(f'🔍 TESTE ATLAS: Explicar "{curso}"')
    print('='*70)
    
    try:
        db_service = DatabaseServiceAtlas()
        existing = db_service.get_responses("explicar", curso)
        
        if existing:
            response_text, created_at = existing[0]
            print(f'\n✅ Encontrado no MongoDB Atlas:')
            print(f'   Curso: {curso}')
            print(f'   Criado em: {created_at}')
            print(f'\n📊 Resposta:\n')
            
            resp_formatted = format_json_response(response_text)
            if len(resp_formatted) > 2000:
                print(resp_formatted[:2000])
                print(f'\n... (resposta truncada)')
            else:
                print(resp_formatted)
            
            db_service.close()
            return True
        else:
            print(f'\n❌ Nenhuma resposta encontrada para: {curso}')
            print(f'\n💡 Cursos disponíveis:')
            for doc in db_service.responses.find({'category': 'explicar'}):
                key = doc["value_key"]
                if key:
                    print(f'   • {key}')
            db_service.close()
            return False
    
    except Exception as e:
        print(f'\n❌ ERRO: {e}')
        return False

def main():
    print('\n🚀 TESTE DE EXPLICAR COM MONGODB ATLAS (Real)\n')
    
    if len(sys.argv) < 2:
        print('📋 Uso: python test_explicar_atlas.py "Curso"\n')
        print('Exemplos:')
        print('  python test_explicar_atlas.py "Quimica"')
        print('  python test_explicar_atlas.py "Engenharia"\n')
        sys.exit(0)
    
    curso = sys.argv[1]
    test_explicar_atlas(curso)
    print('\n' + '='*70)

if __name__ == '__main__':
    main()

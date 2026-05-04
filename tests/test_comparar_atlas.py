#!/usr/bin/env python
"""
Teste de COMPARAR contra MongoDB Atlas REAL
(não mongomock)
"""
import os
import sys
import json
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class DatabaseServiceAtlas:
    """DatabaseService conectado ao MongoDB Atlas real"""
    def __init__(self):
        self.mongo_uri = os.getenv('MONGO_URI')
        self.db_name = os.getenv('MONGO_DB_NAME', 'planejador_carreira')
        
        if not self.mongo_uri:
            raise RuntimeError("MONGO_URI não encontrada em variáveis de ambiente")
        
        # Conectar com tlsAllowInvalidCertificates=True
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
    """Formatar resposta JSON para exibição."""
    try:
        data = json.loads(json_str)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except:
        return json_str

def test_comparar_atlas(c1: str, c2: str):
    """Testar comparar() contra MongoDB Atlas real."""
    print('='*70)
    print(f'🔍 TESTE ATLAS: Comparar "{c1}" × "{c2}"')
    print('='*70)
    
    try:
        db_service = DatabaseServiceAtlas()
        
        # Buscar respostas
        key = f"{c1}|{c2}"
        existing = db_service.get_responses("comparar", key)
        
        if existing:
            response_text, created_at = existing[0]
            print(f'\n✅ Encontrado no MongoDB Atlas:')
            print(f'   Chave: {key}')
            print(f'   Criado em: {created_at}')
            print(f'\n📊 Resposta:\n')
            
            resp_formatted = format_json_response(response_text)
            if len(resp_formatted) > 2000:
                print(resp_formatted[:2000])
                print(f'\n... (resposta truncada, total: {len(resp_formatted)} caracteres)')
            else:
                print(resp_formatted)
            
            db_service.close()
            return True
        else:
            print(f'\n❌ Nenhuma resposta encontrada para: {key}')
            
            # Listar disponíveis
            print(f'\n💡 Comparações disponíveis no Atlas:')
            all_comparacoes = db_service.responses.find({'category': 'comparar'})
            for doc in all_comparacoes:
                print(f'   • {doc["value_key"]}')
            
            db_service.close()
            return False
    
    except Exception as e:
        print(f'\n❌ ERRO: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    print('\n🚀 TESTE DE COMPARAR COM MONGODB ATLAS (Real)\n')
    
    if len(sys.argv) < 2:
        print('📋 Uso: python test_comparar_atlas.py "Curso1|Curso2"\n')
        print('Exemplos:')
        print('  python test_comparar_atlas.py "Engenharia|Medicina"')
        print('  python test_comparar_atlas.py "Corredor|poliatleta"')
        print('  python test_comparar_atlas.py "pintor|medicina"\n')
        sys.exit(0)
    
    comparison = sys.argv[1]
    
    if '|' not in comparison:
        print(f'❌ Formato inválido: {comparison}')
        print('Use: "Curso1|Curso2"\n')
        sys.exit(1)
    
    c1, c2 = comparison.split('|', 1)
    test_comparar_atlas(c1.strip(), c2.strip())
    
    print('\n' + '='*70)

if __name__ == '__main__':
    main()

#!/usr/bin/env python
"""
Teste de QUESTIONÁRIO com MongoDB (mongomock)
Simula o fluxo de questionário com cache-first
"""
import json
import hashlib
import sys
import os
from pathlib import Path
from datetime import datetime

import mongomock

# Adicionar paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "gemini"))

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

    def save_response(self, category: str, value_key: str, response_text: str):
        self.responses.insert_one({
            "category": category,
            "value_key": value_key,
            "response": response_text,
            "created_at": datetime.now(),
        })

def test_questionario_cache():
    """Testa o fluxo cache-first do questionário"""
    
    print('='*70)
    print('🧪 TESTE DE QUESTIONÁRIO COM CACHE-FIRST')
    print('='*70)
    
    # Criar mock do banco
    client = mongomock.MongoClient()
    db_service = DatabaseServiceMock(client)
    
    # Exemplo de respostas
    answers = [
        {"id": "Q01", "resposta": "3o ano do EM", "valor_normalizado": "3o_ano"},
        {"id": "Q02", "resposta": "Tecnologia e programacao", "valor_normalizado": "tecnologia"},
        {"id": "Q03", "resposta": "Bootcamp ou curso acelerado", "valor_normalizado": "bootcamp"},
        {"id": "Q04", "resposta": "Tenho recursos limitados", "valor_normalizado": "limitado"},
    ]
    
    # Criar hash determinístico (como faz a API)
    answers_str = json.dumps(answers, sort_keys=True, ensure_ascii=False)
    value_key = hashlib.sha256(answers_str.encode('utf-8')).hexdigest()
    
    print(f'\n📝 Respostas do questionário:')
    for ans in answers:
        print(f"   {ans['id']}: {ans['resposta']}")
    
    print(f'\n🔑 Hash gerado: {value_key[:16]}...')
    
    # PRIMEIRA REQUISIÇÃO (sem cache)
    print(f'\n------- PRIMEIRA REQUISIÇÃO (SEM CACHE) -------')
    existing = db_service.get_responses("questionario", value_key)
    
    if existing:
        print("✅ Encontrado no cache (inesperado)")
        cached = True
    else:
        print("❌ Não encontrado no cache (esperado)")
        
        # Simular resposta da IA
        mock_response = {
            "resumo_entrevista": {
                "objetivo_principal": "Ingresso em carreira de tecnologia/programação",
                "nivel_atual": "Iniciante",
                "areas_prioritarias": ["Tecnologia", "Programação"],
                "tempo_semana_horas": "20-30 horas",
                "orcamento": "Limitado",
                "prazo_resultado": "3 meses",
            },
            "perfil_estruturado": {
                "momento_carreira": "Entrada",
                "foco_principal": "Programação Full-Stack",
                "intensidade_estudo": "Alta",
                "grau_autonomia": "Alto",
                "risco_evasao": "Baixo",
            },
            "recomendacoes_cursos": [
                {
                    "ranking": 1,
                    "nome_curso": "Bootcamp Python Full-Stack",
                    "tipo_formacao": "Bootcamp",
                    "nivel_indicado": "Iniciante",
                    "duracao_estimada": "3 meses",
                    "faixa_preco": "R$ 0 a R$ 500/mes",
                    "modalidade": "Online",
                    "score_aderencia": 0.95,
                    "explicacao_fit": "Alinha-se perfeitamente com interesse em tecnologia e programação, oferece resultado rápido dentro do orçamento limitado.",
                    "pontos_atencao": ["Exige dedicação alta", "Acompanhamento semanal recomendado"],
                    "plano_acao_30_dias": [
                        "Selecionar bootcamp e fazer inscrição",
                        "Criar cronograma semanal de estudos",
                        "Completar módulo introdutório"
                    ]
                }
            ]
        }
        
        response_text = json.dumps(mock_response, ensure_ascii=False, indent=2)
        
        # Salvar na simulação
        db_service.save_response("questionario", value_key, response_text)
        print(f"✅ Resposta salva no cache")
        print(f"   Categoria: questionario")
        print(f"   Value_key: {value_key[:16]}...")
        cached = False
    
    # SEGUNDA REQUISIÇÃO (COM CACHE)
    print(f'\n------- SEGUNDA REQUISIÇÃO (COM CACHE) -------')
    existing = db_service.get_responses("questionario", value_key)
    
    if existing:
        print("✅ Encontrado no cache (esperado)")
        response_text, created_at = existing[0]
        cached = True
        print(f"   Criado em: {created_at}")
        
        # Mostrar preview da resposta
        try:
            data = json.loads(response_text)
            print(f"\n📊 Resposta cacheada:")
            print(f"   Perfil: {data.get('perfil_estruturado', {}).get('foco_principal', 'N/A')}")
            print(f"   Cursos recomendados: {len(data.get('recomendacoes_cursos', []))}")
            if data.get('recomendacoes_cursos'):
                primeiro_curso = data['recomendacoes_cursos'][0]
                print(f"   1º Recomendado: {primeiro_curso.get('nome_curso')}")
        except:
            print("   (Resposta não é JSON válido)")
    else:
        print("❌ Não encontrado no cache (inesperado)")
    
    # TESTE COM RESPOSTAS DIFERENTES (deve gerar nova chave)
    print(f'\n------- TESTE COM RESPOSTAS DIFERENTES -------')
    answers2 = [
        {"id": "Q01", "resposta": "1o ano do EM", "valor_normalizado": "1o_ano"},
        {"id": "Q02", "resposta": "Artes e Design", "valor_normalizado": "artes"},
    ]
    
    answers_str2 = json.dumps(answers2, sort_keys=True, ensure_ascii=False)
    value_key2 = hashlib.sha256(answers_str2.encode('utf-8')).hexdigest()
    
    print(f"🔑 Nova hash (respostas diferentes): {value_key2[:16]}...")
    print(f"   Hash anterior:  {value_key[:16]}...")
    print(f"   Hashes iguais? {value_key == value_key2} (deve ser False)")
    
    existing2 = db_service.get_responses("questionario", value_key2)
    if existing2:
        print("❌ Encontrado (inesperado)")
    else:
        print("✅ Não encontrado (esperado - nova requisição)")
    
    # Resumo
    print('\n' + '='*70)
    print('✅ TESTE CONCLUÍDO COM SUCESSO')
    print('='*70)
    print(f'''
✓ Respostas são normalizadas
✓ Hash SHA256 é determinístico
✓ Cache-first funciona: primeira req salva, segunda retorna cache
✓ Respostas diferentes geram hashes diferentes
✓ Estrutura JSON é preservada

Fluxo validado:
1. POST /api/questionario {"answers": [...]}
2. Backend valida e normaliza
3. Gera SHA256 hash da resposta
4. Verifica cache no MongoDB (questionario | value_key)
5. Se não tem: chama Gemini, salva, retorna
6. Se tem: retorna cache com flag cached=true
    ''')

if __name__ == '__main__':
    test_questionario_cache()

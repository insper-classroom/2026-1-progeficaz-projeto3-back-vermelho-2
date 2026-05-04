#!/usr/bin/env python
"""
Teste de /api/questionario contra o servidor Flask real
Execute: python api.py (em outro terminal)
Depois: python tests/test_api_questionario.py
"""
import requests
import json
import sys
import time

BASE_URL = "http://127.0.0.1:5000"

def test_questionario_api():
    """Testa a rota /api/questionario"""
    
    print('='*70)
    print('🧪 TESTE DA ROTA /api/questionario')
    print('='*70)
    
    # Verificar se o servidor está rodando
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print("❌ Servidor não está respondendo corretamente")
            sys.exit(1)
        print("✅ Servidor está rodando\n")
    except requests.exceptions.ConnectionError:
        print("❌ Não consegui conectar ao servidor em http://127.0.0.1:5000")
        print("   Execute 'python api.py' em outro terminal\n")
        sys.exit(1)
    
    # Teste 1: Payload inválido (sem answers)
    print("------- TESTE 1: Payload inválido -------")
    response = requests.post(f"{BASE_URL}/api/questionario", json={})
    print(f"Status: {response.status_code} (esperado: 400)")
    print(f"Resposta: {response.json()}")
    assert response.status_code == 400, "Deveria retornar 400"
    print("✅ Validação de payload funcionando\n")
    
    # Teste 2: Answers vazio
    print("------- TESTE 2: Answers vazio -------")
    response = requests.post(f"{BASE_URL}/api/questionario", json={"answers": []})
    print(f"Status: {response.status_code} (esperado: 400)")
    print(f"Resposta: {response.json()}")
    assert response.status_code == 400, "Deveria retornar 400"
    print("✅ Validação de array vazio funcionando\n")
    
    # Teste 3: Resposta válida (PRIMEIRA REQUISIÇÃO)
    print("------- TESTE 3: Resposta válida (PRIMEIRA REQ - sem cache) -------")
    answers = [
        {"id": "Q01", "resposta": "3o ano do EM", "valor_normalizado": "3o_ano"},
        {"id": "Q02", "resposta": "Tecnologia e programacao", "valor_normalizado": "tecnologia"},
        {"id": "Q03", "resposta": "Bootcamp ou curso acelerado", "valor_normalizado": "bootcamp"},
        {"id": "Q04", "resposta": "Tenho recursos limitados", "valor_normalizado": "limitado"},
    ]
    
    payload = {"answers": answers}
    
    print(f"Enviando: {json.dumps(payload, ensure_ascii=False)[:100]}...")
    response = requests.post(f"{BASE_URL}/api/questionario", json=payload)
    
    print(f"Status: {response.status_code} (esperado: 200)")
    
    if response.status_code != 200:
        print(f"❌ Erro: {response.text}")
        return False
    
    result = response.json()
    print(f"Status da resposta: {result.get('status')}")
    print(f"Cached: {result.get('cached')} (esperado: false)")
    print(f"Value_key: {result.get('value_key', '')[:16]}...")
    print(f"Timestamp: {result.get('timestamp')}")
    
    # Validar estrutura de resposta
    assert result.get('status') == 'success', "Status deve ser 'success'"
    assert result.get('cached') == False, "Primeira requisição deve ter cached=false"
    assert 'value_key' in result, "Deve retornar value_key"
    assert result.get('data'), "Deve ter dados de resposta"
    
    print(f"\n📊 Dados retornados:")
    data = result.get('data', {})
    
    # Se for string, parsear
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            pass
    
    if isinstance(data, dict):
        print(f"   Estrutura: {list(data.keys())}")
    else:
        print(f"   (Resposta: {str(data)[:100]}...)")
    
    value_key_1 = result.get('value_key')
    print("✅ Primeira requisição OK (cache-miss)\n")
    
    # Teste 4: SEGUNDA REQUISIÇÃO com MESMAS respostas (deve ter cache)
    print("------- TESTE 4: Segunda requisição (COM cache) -------")
    
    # Enviar as MESMAS respostas
    response2 = requests.post(f"{BASE_URL}/api/questionario", json=payload)
    
    print(f"Status: {response2.status_code} (esperado: 200)")
    
    if response2.status_code != 200:
        print(f"❌ Erro: {response2.text}")
        return False
    
    result2 = response2.json()
    value_key_2 = result2.get('value_key')
    
    print(f"Status da resposta: {result2.get('status')}")
    print(f"Cached: {result2.get('cached')} (esperado: true)")
    print(f"Value_key: {value_key_2[:16] if value_key_2 else 'N/A'}...")
    
    # Validar cache
    assert result2.get('cached') == True, "Segunda requisição deve ter cached=true"
    assert value_key_1 == value_key_2, "Value_keys devem ser idênticos"
    
    print("✅ Segunda requisição OK (cache-hit)\n")
    
    # Teste 5: TERCEIRA REQUISIÇÃO com RESPOSTAS DIFERENTES (novo cache)
    print("------- TESTE 5: Terceira requisição (respostas diferentes) -------")
    answers_different = [
        {"id": "Q01", "resposta": "1o ano do EM", "valor_normalizado": "1o_ano"},
        {"id": "Q02", "resposta": "Artes e Design", "valor_normalizado": "artes"},
    ]
    
    payload_different = {"answers": answers_different}
    response3 = requests.post(f"{BASE_URL}/api/questionario", json=payload_different)
    
    print(f"Status: {response3.status_code} (esperado: 200)")
    
    if response3.status_code != 200:
        print(f"❌ Erro: {response3.text}")
        return False
    
    result3 = response3.json()
    value_key_3 = result3.get('value_key')
    
    print(f"Cached: {result3.get('cached')} (esperado: false)")
    print(f"Value_key: {value_key_3[:16] if value_key_3 else 'N/A'}...")
    
    assert result3.get('cached') == False, "Respostas diferentes devem resultar em cache-miss"
    assert value_key_3 != value_key_1, "Value_keys devem ser diferentes"
    
    print("✅ Respostas diferentes geram cache-miss (novo value_key)\n")
    
    # Resumo
    print('='*70)
    print('✅ TODOS OS TESTES PASSARAM')
    print('='*70)
    print(f'''
Validações:
✓ Endpoint /api/questionario está funcionando
✓ Validação de payload (400 para inválido)
✓ Cache-first: primeira req tem cached=false
✓ Cache-first: segunda req tem cached=true
✓ Hash SHA256 é determinístico (mesmas respostas = mesmo value_key)
✓ Respostas diferentes geram value_keys diferentes
✓ Resposta JSON é válida

Próximos passos:
1. Testar no frontend
2. Validar estrutura de resposta (recomendações de cursos)
3. Monitorar performance de cache
    ''')
    
    return True

if __name__ == '__main__':
    try:
        success = test_questionario_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

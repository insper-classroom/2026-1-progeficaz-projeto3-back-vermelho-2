#!/usr/bin/env python
"""
Script de teste para a API REST
Testa todas as rotas sem precisar de curl/Postman
"""
import requests
import json
from time import sleep

BASE_URL = "http://localhost:5000"

def print_response(title, response):
    """Imprimir resposta formatada."""
    print(f'\n{"="*70}')
    print(f'✅ {title}')
    print(f'{"="*70}')
    print(f'Status: {response.status_code}')
    try:
        data = response.json()
        print(f'Response:\n{json.dumps(data, ensure_ascii=False, indent=2)[:500]}...')
    except:
        print(f'Response: {response.text[:200]}...')

def test_health():
    """Testar health check."""
    print('\n[1/6] Testando Health Check...')
    try:
        response = requests.get(f'{BASE_URL}/api/health', timeout=5)
        print_response('Health Check', response)
        return response.status_code == 200
    except Exception as e:
        print(f'❌ Erro: {e}')
        return False

def test_stats():
    """Testar estatísticas."""
    print('\n[2/6] Testando Estatísticas...')
    try:
        response = requests.get(f'{BASE_URL}/api/stats', timeout=5)
        print_response('Estatísticas', response)
        return response.status_code == 200
    except Exception as e:
        print(f'❌ Erro: {e}')
        return False

def test_comparar():
    """Testar rota de comparação."""
    print('\n[3/6] Testando COMPARAR...')
    try:
        payload = {
            "curso1": "Engenharia",
            "curso2": "Medicina"
        }
        response = requests.post(
            f'{BASE_URL}/api/comparar',
            json=payload,
            timeout=10
        )
        print_response('COMPARAR: Engenharia vs Medicina', response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Cached: {data.get('cached')}")
            return True
        return False
    except Exception as e:
        print(f'❌ Erro: {e}')
        return False

def test_especializar():
    """Testar rota de especialização."""
    print('\n[4/6] Testando ESPECIALIZAR...')
    try:
        payload = {
            "curso": "Engenharia"
        }
        response = requests.post(
            f'{BASE_URL}/api/especializar',
            json=payload,
            timeout=10
        )
        print_response('ESPECIALIZAR: Engenharia', response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Cached: {data.get('cached')}")
            return True
        return False
    except Exception as e:
        print(f'❌ Erro: {e}')
        return False

def test_explicar():
    """Testar rota de explicação."""
    print('\n[5/6] Testando EXPLICAR...')
    try:
        payload = {
            "curso": "Quimica"
        }
        response = requests.post(
            f'{BASE_URL}/api/explicar',
            json=payload,
            timeout=10
        )
        print_response('EXPLICAR: Química', response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Cached: {data.get('cached')}")
            return True
        return False
    except Exception as e:
        print(f'❌ Erro: {e}')
        return False

def test_listar():
    """Testar rota de listagem."""
    print('\n[6/6] Testando LISTAR...')
    try:
        response = requests.get(
            f'{BASE_URL}/api/listar',
            timeout=10
        )
        print_response('LISTAR: Todos os cursos', response)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Cached: {data.get('cached')}")
            return True
        return False
    except Exception as e:
        print(f'❌ Erro: {e}')
        return False

def main():
    print('\n' + '='*70)
    print('🧪 TESTE DA API REST')
    print('='*70)
    print('\nCertifique-se de que a API está rodando:')
    print('  python api.py')
    print('\nAguardando conexão...')
    
    # Tentar conectar
    max_retries = 5
    for i in range(max_retries):
        try:
            requests.get(f'{BASE_URL}/api/health', timeout=2)
            print('✅ API conectada!\n')
            break
        except:
            if i < max_retries - 1:
                print(f'  Tentativa {i+1}/{max_retries-1}: aguardando...')
                sleep(1)
            else:
                print(f'❌ Não consegui conectar à API em {BASE_URL}')
                print('Certifique-se de que a API está rodando: python api.py')
                return
    
    # Rodar testes
    results = [
        ("Health Check", test_health()),
        ("Estatísticas", test_stats()),
        ("COMPARAR", test_comparar()),
        ("ESPECIALIZAR", test_especializar()),
        ("EXPLICAR", test_explicar()),
        ("LISTAR", test_listar()),
    ]
    
    # Resumo
    print('\n' + '='*70)
    print('📊 RESUMO DOS TESTES')
    print('='*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for title, result in results:
        status = '✅' if result else '❌'
        print(f'{status} {title}')
    
    print(f'\n📈 Resultado: {passed}/{total} testes passaram')
    print('\n' + '='*70)
    
    if passed == total:
        print('\n🎉 TODOS OS TESTES PASSARAM!')
        print('\n✨ Próximos passos:')
        print('  1. Conectar frontend à API')
        print('  2. Fazer requisições para: /api/comparar, /api/especializar, etc')
        print('  3. Dados serão cacheados automaticamente no MongoDB')

if __name__ == '__main__':
    main()

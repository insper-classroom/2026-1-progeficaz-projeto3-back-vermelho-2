#!/usr/bin/env python
"""
API REST para Planejador de Carreiras
Cache-First Architecture: busca no MongoDB, se não encontrar chama IA
"""
import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Adicionar caminho do gemini para imports
sys.path.insert(0, str(Path(__file__).parent / "gemini"))

from api_gemini import GeminiService, DatabaseService

# Carregar variáveis de ambiente
load_dotenv(Path(__file__).with_name(".env").parent / "gemini" / ".env")

app = Flask(__name__)

# Habilita CORS para permitir testes a partir de uma página estática local
CORS(app)

# Configuração
app.json.ensure_ascii = False  # Suporta português
app.config['JSON_SORT_KEYS'] = False

# Inicializar serviços
try:
    gemini_service = GeminiService()
    db_service = gemini_service.db
except Exception as e:
    print(f"❌ Erro ao inicializar serviços: {e}")
    gemini_service = None
    db_service = None

# ============================================================================
# ROTAS DA API
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica saúde da API e conexão com MongoDB."""
    try:
        if db_service:
            # Testar conexão
            db_service.responses.find_one()
            mongodb_status = "✅ Conectado"
        else:
            mongodb_status = "❌ Desconectado"
        
        return jsonify({
            "status": "ok",
            "mongodb": mongodb_status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/comparar', methods=['POST'])
def api_comparar():
    """
    Comparar dois cursos
    
    Request:
    {
        "curso1": "Engenharia",
        "curso2": "Medicina"
    }
    
    Response:
    {
        "status": "success",
        "data": {JSON da comparação},
        "cached": true/false,
        "timestamp": "2026-05-03T..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'curso1' not in data or 'curso2' not in data:
            return jsonify({
                "status": "error",
                "error": "Envie: {\"curso1\": \"...\", \"curso2\": \"...\"}"
            }), 400
        
        curso1 = data['curso1'].strip()
        curso2 = data['curso2'].strip()
        
        if not curso1 or not curso2:
            return jsonify({
                "status": "error",
                "error": "Cursos não podem estar vazios"
            }), 400
        
        # Montar chave
        value_key = f"{curso1}|{curso2}"
        
        # Buscar no cache (MongoDB)
        existing = db_service.get_responses("comparar", value_key)
        cached = False
        
        if existing:
            response_text = existing[0][0]
            cached = True
        else:
            # Chamar IA
            base_path = Path(__file__).parent / "gemini" / "comp.json"
            base_template = base_path.read_text(encoding="utf-8")
            
            prompt = f"""
    Você é um especialista em orientação vocacional e planejamento de carreira. 
    O usuário, um estudante do ensino médio indeciso, solicitou uma comparação detalhada e prática entre os cursos: {curso1} e {curso2}.

    Sua tarefa é analisar esses dois cursos e retornar as informações ESTRITAMENTE no formato JSON abaixo. 
    Substitua os valores de exemplo pelas informações reais da comparação. 
    Seja objetivo, claro e foque em ajudar o aluno a entender as diferenças de grade, mercado e qual perfil se encaixa melhor em cada opção.

    IMPORTANTE: Retorne APENAS um objeto JSON válido, sem textos antes ou depois, e sem marcações Markdown (como ```json).

    Molde JSON:
    {base_template}
            """
            
            response_text = gemini_service.process_request("comparar", value_key, prompt)
        
        # Parsear JSON
        try:
            response_json = json.loads(response_text)
        except:
            response_json = response_text
        
        return jsonify({
            "status": "success",
            "data": response_json,
            "cached": cached,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/especializar', methods=['POST'])
def api_especializar():
    """
    Especializar em um curso específico
    
    Request:
    {
        "curso": "Engenharia"
    }
    
    Response:
    {
        "status": "success",
        "data": {JSON da especialização},
        "cached": true/false,
        "timestamp": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'curso' not in data:
            return jsonify({
                "status": "error",
                "error": "Envie: {\"curso\": \"...\"}"
            }), 400
        
        curso = data['curso'].strip()
        
        if not curso:
            return jsonify({
                "status": "error",
                "error": "Curso não pode estar vazio"
            }), 400
        
        # Buscar no cache
        existing = db_service.get_responses("especializar", curso)
        cached = False
        
        if existing:
            response_text = existing[0][0]
            cached = True
        else:
            # Chamar IA
            base_path = Path(__file__).parent / "gemini" / "especializar.json"
            base_template = base_path.read_text(encoding="utf-8")
            
            prompt = f"""
    Gere APENAS JSON válido para explicar o curso abaixo.
    Não inclua texto fora do JSON e não use markdown.
    O usuario quer mais informações sobre cursos de graduação e carreiras.
    Preencha os campos com informações relacionadas ao curso {curso}
    
    Use o exemplo abaixo como base de estrutura:

    {base_template}
            """
            
            response_text = gemini_service.process_request("especializar", curso, prompt, json_mode=True)
        
        # Parsear JSON
        try:
            response_json = json.loads(response_text)
        except:
            response_json = response_text
        
        return jsonify({
            "status": "success",
            "data": response_json,
            "cached": cached,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/explicar', methods=['POST'])
def api_explicar():
    """
    Explicar um curso
    
    Request:
    {
        "curso": "Química"
    }
    
    Response:
    {
        "status": "success",
        "data": {JSON da explicação},
        "cached": true/false,
        "timestamp": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'curso' not in data:
            return jsonify({
                "status": "error",
                "error": "Envie: {\"curso\": \"...\"}"
            }), 400
        
        curso = data['curso'].strip()
        
        if not curso:
            return jsonify({
                "status": "error",
                "error": "Curso não pode estar vazio"
            }), 400
        
        # Buscar no cache
        existing = db_service.get_responses("explicar", curso)
        cached = False
        
        if existing:
            response_text = existing[0][0]
            cached = True
        else:
            # Chamar IA
            base_path = Path(__file__).parent / "gemini" / "info.json"
            base_template = base_path.read_text(encoding="utf-8")
            
            prompt = f"""
    Gere APENAS JSON válido para explicar o curso abaixo.
    Não inclua texto fora do JSON e não use markdown.
    O usuario quer as informações sobre cursos de graduação e carreiras.
    Preencha os campos com informações relacionadas ao curso {curso}
    
    Use este modelo como referência:
    {base_template}
            """
            
            response_text = gemini_service.process_request("explicar", curso, prompt, json_mode=True)
        
        # Parsear JSON
        try:
            response_json = json.loads(response_text)
        except:
            response_json = response_text
        
        return jsonify({
            "status": "success",
            "data": response_json,
            "cached": cached,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/questionario', methods=['POST'])
def api_questionario():
    """
    Processar questionário de vocação (cache-first)
    
    Request:
    {
        "answers": [
            {"id": "Q01", "resposta": "...", "valor_normalizado": "..."},
            {"id": "Q02", "resposta": "...", "valor_normalizado": "..."},
            ...
        ]
    }
    
    Response:
    {
        "status": "success",
        "data": {JSON com recomendações de cursos},
        "cached": true/false,
        "timestamp": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'answers' not in data:
            return jsonify({
                "status": "error",
                "error": "Envie: {\"answers\": [{\"id\": \"Q01\", \"resposta\": \"...\", \"valor_normalizado\": \"...\"}, ...]}"
            }), 400
        
        answers = data['answers']
        
        if not isinstance(answers, list) or len(answers) == 0:
            return jsonify({
                "status": "error",
                "error": "answers deve ser um array não vazio"
            }), 400
        
        # Validar cada resposta
        for ans in answers:
            if not isinstance(ans, dict) or 'id' not in ans or 'resposta' not in ans:
                return jsonify({
                    "status": "error",
                    "error": "Cada resposta deve ter 'id' e 'resposta'"
                }), 400
        
        # Criar hash determinístico das respostas para cache-key
        # Normalizamos para garantir que o mesmo conjunto de respostas sempre gera a mesma chave
        answers_str = json.dumps(answers, sort_keys=True, ensure_ascii=False)
        value_key = hashlib.sha256(answers_str.encode('utf-8')).hexdigest()
        
        # Buscar no cache
        existing = db_service.get_responses("questionario", value_key)
        cached = False
        
        if existing:
            response_text = existing[0][0]
            cached = True
        else:
            # Carregar templates
            questionario_path = Path(__file__).parent / "gemini" / "questionario.json"
            retorno_path = Path(__file__).parent / "gemini" / "retorno_questionario.json"
            
            questionario_template = ""
            retorno_template = ""
            
            if questionario_path.exists():
                questionario_template = questionario_path.read_text(encoding="utf-8")
            
            if retorno_path.exists():
                retorno_template = retorno_path.read_text(encoding="utf-8")
            
            # Formatar respostas para o prompt
            respostas_texto = "\n".join([
                f"Q{ans.get('id', '?')}: {ans.get('resposta', '')}"
                for ans in answers
            ])
            
            # Montar prompt
            prompt = f"""
Você é um especialista em orientação vocacional e planejamento de carreira.
Um aluno do ensino médio respondeu a um questionário para descobrir qual carreira é mais adequada para ele.

RESPOSTAS DO QUESTIONÁRIO:
{respostas_texto}

Sua tarefa é:
1. Analisar essas respostas
2. Entender o perfil, interesses e objetivos do aluno
3. Recomendar cursos e carreiras alinhados com o perfil identificado
4. Retornar um JSON estruturado com:
   - Resumo da entrevista
   - Perfil estruturado (momento de carreira, foco principal, intensidade de estudo, etc)
   - Recomendações de cursos (ranking, tipo, duração, preço, modalidade, score de aderência, explicação, pontos de atenção, plano de ação)
   - Métrica de decisão (confiança geral, pesos dos critérios)

IMPORTANTE: 
- Retorne APENAS um objeto JSON válido, sem textos antes ou depois
- Não use marcações Markdown (como ```json)
- Adapte o conteúdo para português brasileiro
- Seja objetivo, prático e foque em ajudar o aluno

Molde de estrutura de retorno (preencha com dados reais):
{retorno_template}
            """
            
            response_text = gemini_service.process_request("questionario", value_key, prompt, json_mode=True)
        
        # Parsear JSON
        try:
            response_json = json.loads(response_text)
        except:
            response_json = response_text
        
        return jsonify({
            "status": "success",
            "data": response_json,
            "cached": cached,
            "value_key": value_key,  # Retorna a chave para debug/referência
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/listar', methods=['GET'])
def api_listar():
    """
    Listar cursos
    
    Response:
    {
        "status": "success",
        "data": {lista de cursos},
        "cached": true/false,
        "timestamp": "..."
    }
    """
    try:

        # Se houver um parâmetro de busca ?q=Curso, tentar retornar info do curso
        query_curso = request.args.get('q', '').strip()
        if query_curso:
            try:
                # Buscar cache 'explicar' por título exato
                existing_course = db_service.get_responses("explicar", query_curso)
                if existing_course:
                    response_text = existing_course[0][0]
                    cached = True
                else:
                    # Reaproveita a lógica de /api/explicar para gerar a explicação
                    base_path = Path(__file__).parent / "gemini" / "info.json"
                    base_template = base_path.read_text(encoding="utf-8")

                    prompt = f"""
    Gere APENAS JSON válido para explicar o curso abaixo.
    Não inclua texto fora do JSON e não use markdown.
    O usuario quer as informações sobre cursos de graduação e carreiras.
    Preencha os campos com informações relacionadas ao curso {query_curso}
    
    Use este modelo como referência:
    {base_template}
                    """

                    response_text = gemini_service.process_request("explicar", query_curso, prompt, json_mode=True)
                    cached = False

                try:
                    response_json = json.loads(response_text)
                except Exception:
                    response_json = response_text

                return jsonify({
                    "status": "success",
                    "data": response_json,
                    "cached": cached,
                    "queried": query_curso,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500

        # Permite forçar refresh via ?refresh=1
        refresh_param = request.args.get('refresh', '')
        force_refresh = str(refresh_param).lower() in ("1", "true", "yes")

        # Buscar no cache
        existing = None if force_refresh else db_service.get_responses("listar", "")
        cached = False

        if existing:
            response_text = existing[0][0]
            cached = True
        else:
            # Tentar montar lista a partir de entradas 'explicar' já salvas no banco
            try:
                docs = db_service.responses.find(
                    {"category": "explicar"},
                    {"value_key": 1, "response": 1, "created_at": 1},
                ).sort("created_at", -1)

                cursos = []
                import json as _json
                for doc in docs:
                    value_key = doc.get('value_key', '')
                    response_text_doc = doc.get('response', '')
                    try:
                        obj = _json.loads(response_text_doc)
                        if isinstance(obj, dict) and 'Curso' in obj:
                            cursos.append(obj)
                        else:
                            cursos.append({'Curso': value_key, 'Descricao': '', 'Faculdades': [], 'Carreiras': [], 'Profissionalizacoes': [], 'raw': obj})
                    except Exception:
                        cursos.append({'Curso': value_key, 'Descricao': response_text_doc, 'Faculdades': [], 'Carreiras': [], 'Profissionalizacoes': []})

                result_obj = {"lista": {"lista_cursos": cursos}}

                # Cachear o resultado para "listar" para próximas requisições
                try:
                    db_service.save_response("listar", "", _json.dumps(result_obj, ensure_ascii=False))
                except Exception:
                    pass

                response_text = _json.dumps(result_obj, ensure_ascii=False)
                cached = False
            except Exception:
                # Fallback: chamar IA para gerar a lista
                base_path = Path(__file__).parent / "gemini" / "info.json"
                base_template = base_path.read_text(encoding="utf-8")

                prompt = f"""
    Gere APENAS JSON válido para listar cursos com base no modelo abaixo.
    Não inclua texto fora do JSON e não use markdown.
    O usuario quer as informações sobre cursos de graduação e carreiras.

    Use esta estrutura como referência:
    {base_template}

    Se houver dados salvos em cache local, reaproveite o conteúdo coerente com esta estrutura.
                """

                response_text = gemini_service.process_request("listar", "", prompt, json_mode=True)
        
        # Parsear JSON
        try:
            response_json = json.loads(response_text)
        except:
            response_json = response_text
        
        return jsonify({
            "status": "success",
            "data": response_json,
            "cached": cached,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """
    Estatísticas do banco de dados
    """
    try:
        responses_count = db_service.responses.count_documents({})
        requests_count = db_service.requests.count_documents({})
        
        # Contar por categoria
        categories = db_service.responses.distinct('category')
        category_counts = {}
        for cat in categories:
            category_counts[cat] = db_service.responses.count_documents({'category': cat})
        
        return jsonify({
            "status": "success",
            "data": {
                "total_responses": responses_count,
                "total_requests": requests_count,
                "categories": category_counts
            }
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/debug', methods=['GET'])
def api_debug():
    """Rota administrativa: retorna contagens e amostras por categoria para diagnóstico.
    Uso: GET /api/debug?limit=3
    """
    try:
        limit = int(request.args.get('limit', 3))
        categories = db_service.responses.distinct('category')
        samples = {}
        for cat in categories:
            cursor = db_service.responses.find(
                {'category': cat},
                {'value_key': 1, 'response': 1, 'created_at': 1}
            ).sort('created_at', -1).limit(limit)

            docs = []
            for d in cursor:
                created = d.get('created_at')
                if hasattr(created, 'isoformat'):
                    created = created.isoformat()
                docs.append({
                    'value_key': d.get('value_key'),
                    'created_at': created,
                    'response_preview': (d.get('response')[:100] + '...') if isinstance(d.get('response'), str) and len(d.get('response'))>100 else d.get('response')
                })

            samples[cat] = {
                'count': db_service.responses.count_documents({'category': cat}),
                'samples': docs,
            }

        return jsonify({
            'status': 'success',
            'data': {
                'total_responses': db_service.responses.count_documents({}),
                'by_category': samples,
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "error": "Rota não encontrada"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "error": "Erro interno do servidor"
    }), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    if not gemini_service:
        print("❌ Não consegui inicializar os serviços")
        sys.exit(1)
    
    print('\n' + '='*70)
    print('🚀 API Planejador de Carreiras')
    print('='*70)
    print('''
Rotas disponíveis:

  GET  /api/health              - Verifica saúde da API
  GET  /api/stats               - Estatísticas do banco
  GET  /api/debug               - Debug: amostras por categoria
  
  POST /api/comparar            - Compara dois cursos
  POST /api/especializar        - Especializa em um curso
  POST /api/explicar            - Explica um curso
  POST /api/questionario        - Processa questionário de vocação (cache-first)
  GET  /api/listar              - Lista todos os cursos

Exemplos de requisição:
  
  POST /api/comparar
  {
    "curso1": "Engenharia",
    "curso2": "Medicina"
  }
  
  POST /api/especializar
  {
    "curso": "Engenharia"
  }
  
  POST /api/questionario
  {
    "answers": [
      {"id": "Q01", "resposta": "1o ano do EM", "valor_normalizado": "1o_ano"},
      {"id": "Q02", "resposta": "Tecnologia", "valor_normalizado": "tecnologia"},
      ...
    ]
  }

Documentação interativa:
  http://localhost:5000/  (após iniciar)

    ''')
    print('='*70)
    print('Iniciando servidor...\n')
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False
    )

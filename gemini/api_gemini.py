import argparse
import datetime
import json
import os
import random
import time
from functools import wraps
from pathlib import Path

from bson import ObjectId
from pymongo import MongoClient

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemma-4-31b-it")
MAX_RETRIES = 3
INITIAL_BACKOFF = 1  # segundos
MAX_BACKOFF = 32  # segundos


def exponential_backoff(max_retries: int = MAX_RETRIES, initial_backoff: float = INITIAL_BACKOFF, max_backoff: float = MAX_BACKOFF):
    """
    Decorator que implementa exponential backoff com jitter para requisições.
    Tenta novamente a função em caso de exceção, com atraso exponencial crescente.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            backoff = initial_backoff
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        # Adiciona jitter (aleatoriedade) para evitar thundering herd
                        jitter = random.uniform(0, backoff)
                        wait_time = min(backoff + jitter, max_backoff)
                        print(f"Tentativa {attempt + 1} falhou. Aguardando {wait_time:.2f}s antes de retry...")
                        time.sleep(wait_time)
                        backoff = min(backoff * 2, max_backoff)
                    else:
                        print(f"Todas as {max_retries + 1} tentativas falharam.")
            
            raise last_exception
        
        return wrapper
    return decorator
    

class DatabaseService:
    """Serviço baseado em MongoDB para armazenar respostas e contagens de requisições."""

    def __init__(self, mongo_uri: str | None = None, db_name: str | None = None):
        load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI")
        self.db_name = db_name or os.getenv("MONGO_DB_NAME", "cursos")

        if not self.mongo_uri:
            raise RuntimeError("MONGO_URI nao encontrada. Crie um arquivo .env com MONGO_URI=sua_string")

        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.responses = self.db["cursos"]
        self.requests = self.db["requests"]
        self._init_db()

    def _init_db(self):
        self.responses.create_index([("category", 1), ("value_key", 1)])
        self.requests.create_index("requested_at")

    @staticmethod
    def _utcnow():
        return datetime.datetime.now(datetime.timezone.utc)

    def save_response(self, category: str, value_key: str, response_text: str) -> None:
        self.responses.insert_one(
            {
                "category": category,
                "value_key": value_key,
                "response": response_text,
                "created_at": self._utcnow(),
            }
        )

    def get_responses(self, category: str, value_key: str):
        docs = (
            self.responses.find(
                {"category": category, "value_key": value_key},
                {"response": 1, "created_at": 1},
            )
            .sort("created_at", -1)
        )
        return [(doc["response"], doc.get("created_at")) for doc in docs]

    def count_since(self, seconds: int) -> int:
        since_ts = self._utcnow() - datetime.timedelta(seconds=seconds)
        return self.requests.count_documents({"requested_at": {"$gte": since_ts}})

    def count_today(self) -> int:
        today = datetime.datetime.now(datetime.timezone.utc).date()
        start = datetime.datetime.combine(today, datetime.time.min, tzinfo=datetime.timezone.utc)
        end = datetime.datetime.combine(today, datetime.time.max, tzinfo=datetime.timezone.utc)
        return self.requests.count_documents({"requested_at": {"$gte": start, "$lte": end}})

    def oldest_timestamp_since(self, seconds: int):
        since_ts = self._utcnow() - datetime.timedelta(seconds=seconds)
        doc = self.requests.find(
            {"requested_at": {"$gte": since_ts}},
            {"requested_at": 1},
        ).sort("requested_at", 1).limit(1)
        first = next(iter(doc), None)
        return first["requested_at"] if first else None

    def log_request(self, success: bool = False) -> str:
        result = self.requests.insert_one(
            {
                "requested_at": self._utcnow(),
                "success": bool(success),
            }
        )
        return str(result.inserted_id)

    def update_request_status(self, request_id: str, success: bool) -> None:
        self.requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"success": bool(success)}},
        )

class GeminiService:
    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY nao encontrada. Crie um arquivo .env com GEMINI_API_KEY=sua_chave"
            )

        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.db = DatabaseService()

    @exponential_backoff()
    def generate_text(self, prompt: str) -> str:
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        return response.text or ""

    @exponential_backoff()
    def generate_json(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        return response.text or "{}"

    def process_request(self, category: str, value_key: str, prompt: str, json_mode: bool = False) -> str:
        existing = self.db.get_responses(category, value_key)
        if existing:
            latest_response = existing[0][0]
            print(f"Retornando {len(existing)} resultado(s) salvo(s) para ({category}, {value_key})")
            return latest_response

        req_id = self.db.log_request(success=False)
        try:
            result = self.generate_json(prompt) if json_mode else self.generate_text(prompt)
            self.db.save_response(category, value_key, result)
            self.db.update_request_status(req_id, True)
            return result
        except Exception:
            self.db.update_request_status(req_id, False)
            raise


def _read_json_template(filename: str):
    template_path = Path(__file__).with_name(filename)
    return json.loads(template_path.read_text(encoding="utf-8"))


def _choose_question_text(question: dict) -> str:
    options = [question.get("pergunta_base", "")]
    options.extend(question.get("variacoes", []))
    options = [option for option in options if option]
    return random.choice(options) if options else ""


def questionario() -> None:
    gemini = GeminiService()
    survey_template = _read_json_template("questionario.json")
    retorno_template = _read_json_template("retorno_questionario.json")
    perguntas = survey_template.get("questionario_pesquisa", {}).get("perguntas_base", [])

    respostas = []
    print("\n=== Questionario de Pesquisa ===")
    print("Responda com calma. No fim, vou montar uma recomendacao com base no seu perfil.\n")

    for pergunta in perguntas:
        texto_base = _choose_question_text(pergunta)
        pergunta_exibida = texto_base

        print(pergunta_exibida)
        opcoes = pergunta.get("opcoes", [])
        if opcoes:
            for indice, opcao in enumerate(opcoes, start=1):
                print(f"  {indice}. {opcao}")

        resposta_usuario = input("> ").strip()
        respostas.append(
            {
                "id_pergunta": pergunta.get("id", ""),
                "pergunta_exibida": pergunta_exibida,
                "resposta_usuario": resposta_usuario,
                "valor_normalizado": resposta_usuario,
            }
        )
        print()

    prompt_final = f"""
    Voce e um assistente de pesquisa vocacional.
    Gere APENAS JSON valido, sem markdown e sem texto fora do JSON.
    Preencha a estrutura abaixo com base nas respostas do usuario.
    Se houver dados insuficientes, estime com cautela e preencha "dados_faltantes".
    Recomende cursos coerentes com o perfil e explique de forma objetiva por que cada um combina.

    Estrutura de retorno:
    {json.dumps(retorno_template, ensure_ascii=False, indent=2)}

    Respostas coletadas:
    {json.dumps(respostas, ensure_ascii=False, indent=2)}
    """

    print("=== Resultado ===")
    print(gemini.generate_json(prompt_final))

def explicar() -> None:
    x = input("curso:")
    
    gemini = GeminiService()
    base_path = Path(__file__).with_name("info.json")
    base_template = base_path.read_text(encoding="utf-8")

    prompt = f"""
    Gere APENAS JSON válido para explicar o curso abaixo.
    Não inclua texto fora do JSON e não use markdown.
    O usuario quer mais informações sobre cursos de graduação e carreiras.
    Preencha os campos com informações relacionadas ao curso {x}
    
    Use o exemplo abaixo como base de estrutura:

    {base_template}
    """

    print("\n=== Carregando... ===")
    print(gemini.process_request("explicar", x, prompt, json_mode=True))

def comparar() -> None:
    c1 = input("Primeiro Curso: ")
    c2 = input("Segundo Curso: ")

    gemini = GeminiService()
    base_path = Path(__file__).with_name("comp.json")
    base_template = base_path.read_text(encoding="utf-8")
 
    prompt = f"""
    Você é um especialista em orientação vocacional e planejamento de carreira. 
    O usuário, um estudante do ensino médio indeciso, solicitou uma comparação detalhada e prática entre os cursos: {c1} e {c2}.

    Sua tarefa é analisar esses dois cursos e retornar as informações ESTRITAMENTE no formato JSON abaixo. 
    Substitua os valores de exemplo pelas informações reais da comparação. 
    Seja objetivo, claro e foque em ajudar o aluno a entender as diferenças de grade, mercado e qual perfil se encaixa melhor em cada opção.

    IMPORTANTE: Retorne APENAS um objeto JSON válido, sem textos antes ou depois, e sem marcações Markdown (como ```json).

    Molde JSON:
    {base_template}
    """
    
    print("\n=== Carregando... ===")
    key = f"{c1}|{c2}"
    print(gemini.process_request("comparar", key, prompt))

def listar() -> None:
    gemini = GeminiService()
    base_path = Path(__file__).with_name("info.json")
    base_template = base_path.read_text(encoding="utf-8")

    prompt = f"""
    Gere APENAS JSON válido para listar cursos com base no modelo abaixo.
    Não inclua texto fora do JSON e não use markdown.
    O usuario quer as informações sobre cursos de graduação e carreiras.

    Use esta estrutura como referência:
    {base_template}

    Se houver dados salvos em cache local, reaproveite o conteúdo coerente com esta estrutura.
    """

    print("\n=== Carregando... ===")
    print(gemini.process_request("listar","", prompt, json_mode=True))

def especializar() -> None:
    curso = input("Curso: ")
    
    gemini = GeminiService()
    base_path = Path(__file__).with_name("especializar.json")
    base_template = base_path.read_text(encoding="utf-8")

    prompt = f"""
    Gere APENAS JSON válido para explicar o curso abaixo.
    Não inclua texto fora do JSON e não use markdown.
    O usuario quer mais informações sobre cursos de graduação e carreiras.
    Preencha os campos com informações relacionadas ao curso {curso}
    
    Use o exemplo abaixo como base de estrutura:

    {base_template}
    """
    print("\n=== Carregando... ===")
    print(gemini.process_request("especializar", curso, prompt, json_mode=True))

def main():
    parser = argparse.ArgumentParser(description="Executa explicar, comparar ou questionario.")
    parser.add_argument("mode", nargs="?", choices=["explicar", "comparar", "questionario"], help="Modo de execução")
    args = parser.parse_args()

    if args.mode == "explicar":
        explicar()
        return
    if args.mode == "comparar":
        comparar()
        return
    if args.mode == "questionario":
        questionario()
        return


if __name__ == "__main__":
    main()

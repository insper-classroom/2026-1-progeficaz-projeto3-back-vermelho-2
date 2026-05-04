# Utilitários Gemini para o projeto Vocacionar

Este diretório guarda scripts auxiliares usados para gerar respostas estruturadas com a [api_gemini.py](api_gemini.py). Eles servem como apoio para comparação, explicação, especialização e questionário vocacional.

## 1) Criar ambiente virtual

No PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

## 2) Instalar dependências

pip install -r ../requirements.txt

## 3) Configurar credenciais

Crie um arquivo `.env` nesta pasta com:

```env
GEMINI_API_KEY=sua_chave_real
MONGO_URI=sua_string_de_conexao_mongodb
MONGO_DB_NAME=vocacionar
```

## 4) Executar os modos

python "api_gemini.py" explicar
python "api_gemini.py" comparar
python "api_gemini.py" questionario

## O que este projeto faz

- Gera texto e JSON com `gemini-2.5-flash`
- Reaproveita respostas salvas em MongoDB
- Produz saídas para uso no backend Flask do Vocacionar

## Arquivo principal

- `api_gemini.py`: classe `GeminiService` com métodos:
  - `generate_text(prompt)`
  - `generate_json(prompt)`
  - `process_request(category, value_key, prompt, json_mode=False)`

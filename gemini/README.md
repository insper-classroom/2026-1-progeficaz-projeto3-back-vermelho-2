# Utilitários Gemini para o projeto Vocacionar

Este diretório guarda scripts auxiliares usados para gerar respostas estruturadas com a API Gemini. Eles servem como apoio para comparação, explicação, especialização e questionário vocacional.

## 1) Criar ambiente virtual

No PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

## 2) Instalar dependências

pip install -r ../requirements.txt

## 3) Configurar credenciais

1. Copie `.env.example` para `.env`
2. Preencha `GEMINI_API_KEY`

Exemplo:

GEMINI_API_KEY=sua_chave_real

## 4) Executar os modos

python "api gemini.py" explicar
python "api gemini.py" comparar
python "api gemini.py" questionario

## O que este projeto faz

- Gera texto e JSON com `gemini-2.5-flash`
- Reaproveita respostas salvas em SQLite local
- Produz saídas para uso no backend Flask do Vocacionar

## Arquivo principal

- `api gemini.py`: classe `GeminiService` com métodos:
  - `generate_text(prompt)`
  - `generate_json(prompt)`
  - `process_request(category, value_key, prompt, json_mode=False)`

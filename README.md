# Vocacionar Backend

Backend do projeto **Vocacionar**, feito em Flask, com persistência em MongoDB e um conjunto de utilitários Gemini para apoiar recomendações vocacionais.

## Visão Geral

O repositório está organizado em duas partes:

- `server.py` e `utils.py`: API Flask principal com CRUD de cursos.
- `gemini/`: scripts auxiliares para comparação, explicação, especialização e questionário com a API Gemini.

## Requisitos

- Python 3.13+ ou compatível
- MongoDB Atlas
- Chave da API Gemini para os utilitários em `gemini/`

## Instalação

Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências da raiz:

```powershell
pip install -r requirements.txt
```

## Configuração do MongoDB

O backend atual lê a string de conexão a partir de um arquivo `.cred` na raiz do projeto.

Crie um arquivo `.cred` com o conteúdo:

```env
MONGO_URI=sua_string_de_conexao_do_mongodb_atlas
```

Mantenha esse arquivo fora do Git.

## Executar a API

Inicie o servidor Flask:

```powershell
python server.py
```

Por padrão, a aplicação sobe em modo de desenvolvimento e expõe estas rotas:

- `GET /` - página simples de status
- `GET /cursos` - lista todos os cursos
- `GET /cursos/<titulo>` - busca um curso pelo título
- `POST /cursos` - cria um curso
- `PUT /cursos/<titulo>` - atualiza um curso
- `DELETE /cursos/<titulo>` - remove um curso

## Testes

Rode os testes com:

```powershell
pytest test_api.py
```

## Utilitários Gemini

Os scripts em `gemini/` usam a chave `GEMINI_API_KEY` em um arquivo `.env` dentro da própria pasta.

Exemplo de arquivo:

```env
GEMINI_API_KEY=sua_chave_da_gemini
GOOGLE_API_KEY=opcional
GEMINI_MODEL=gemini-2.5-flash
```

Para preparar esse ambiente, consulte [gemini/README.md](gemini/README.md).

## Dependências

As dependências do backend principal e dos utilitários Gemini foram unificadas em [requirements.txt](requirements.txt).

## Estrutura

- [server.py](server.py) - rotas Flask
- [utils.py](utils.py) - acesso ao MongoDB e serialização
- [test_api.py](test_api.py) - testes da API
- [gemini/](gemini/) - apoio com IA para conteúdos vocacionais

## Observações

- Credenciais não devem ser commitadas.
- O pacote `gemini/` é um apoio local e não substitui o backend Flask principal.
- O projeto ainda pode evoluir para separar melhor os modelos do MongoDB e expor endpoints mais alinhados ao Vocacionar.
